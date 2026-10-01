"""Giving paid shares back (#544; the mechanics §12.3; ``docs/adr/0190`` §4).

**Decided here, made at the provider after the commit** — the fill's rule for
a capture, kept for a refund: each paid share is marked to be given back in the
caller's transaction (``SeatChargeRefundDecided``), and ``SettleSeatCharges``
refunds it from the outbox and records what the provider gave back and the card
fee it kept. A crash between the two leaves a decision a subscriber retries.

**Three reasons, two amounts.** A player who **left before the club's
cut-off** is refunded at once **less the card fee**, which the provider never
returns — the leaver bears it — and so is one who left **after** it, the moment
somebody takes their seat (#545). A game **called off at its cut-off** gives
everybody still in **everything back**: it is the club's own free-cancellation
rule, so the club bears the fees. Each player is emailed — every notice about
money is.

**Nothing here commits**: the act is the caller's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from enum import StrEnum
from typing import final
from uuid import UUID

from app.application.ports import MailQueue
from app.kernel import Instant
from app.modules.payments.application.seat_charge_emails import (
    game_called_off_email,
    left_the_game_email,
    seat_taken_email,
)
from app.modules.payments.domain.card_fee import estimated_card_fee
from app.modules.payments.domain.ports import Payers, SeatChargeRepository, Sellers
from app.modules.payments.domain.seat_charge import SeatCharge


class RefundReason(StrEnum):
    """Why a paid share is given back."""

    #: The player left before the club's cut-off: less the card fee.
    LEFT = "LEFT"
    #: The game was called off at the club's cut-off: in full.
    CALLED_OFF_AT_THE_CUT_OFF = "CALLED_OFF_AT_THE_CUT_OFF"
    #: The player left after the cut-off and somebody took their seat (#545):
    #: less the card fee.
    SEAT_TAKEN = "SEAT_TAKEN"


@final
class RefundTheSeats:
    def __init__(
        self,
        *,
        charges: SeatChargeRepository,
        sellers: Sellers,
        payers: Payers,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._charges = charges
        self._sellers = sellers
        self._payers = payers
        self._mail = mail
        self._app_link = app_link

    async def execute(
        self,
        game_id: UUID,
        players: Collection[UUID],
        *,
        reason: RefundReason,
        at: Instant,
    ) -> Mapping[UUID, SeatCharge]:
        """Give back what each of these players paid for this game. Answers
        each player's charge that a refund was decided on — a share nobody
        paid, or one already being given back, is not."""

        withhold_fee = reason is not RefundReason.CALLED_OFF_AT_THE_CUT_OFF
        refunded: dict[UUID, SeatCharge] = {}
        for charge in await self._charges.of_game(game_id):
            if charge.player_id not in players:
                continue
            if charge.refund(withhold_fee=withhold_fee, at=at):
                await self._charges.save(charge)
                refunded[charge.player_id] = charge
        await self._email(refunded, reason=reason, at=at)
        return refunded

    async def _email(
        self,
        refunded: Mapping[UUID, SeatCharge],
        *,
        reason: RefundReason,
        at: Instant,
    ) -> None:
        if not refunded:
            return
        sellers = await self._sellers.of({c.club_id for c in refunded.values()})
        payers = await self._payers.of(list(refunded))
        for player, charge in refunded.items():
            payer = payers.get(player)
            seller = sellers.get(charge.club_id)
            if payer is None:
                continue
            club = "the club" if seller is None else seller.name
            if reason is RefundReason.LEFT:
                message = left_the_game_email(
                    to=payer.email,
                    name=payer.name,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    share_grosze=charge.amount_grosze,
                    fee_estimate_grosze=estimated_card_fee(charge.amount_grosze),
                    app_link=self._app_link,
                )
            elif reason is RefundReason.SEAT_TAKEN:
                message = seat_taken_email(
                    to=payer.email,
                    name=payer.name,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    share_grosze=charge.amount_grosze,
                    fee_estimate_grosze=estimated_card_fee(charge.amount_grosze),
                    app_link=self._app_link,
                )
            else:
                message = game_called_off_email(
                    to=payer.email,
                    name=payer.name,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    app_link=self._app_link,
                )
            await self._mail.enqueue(message, at=at)
