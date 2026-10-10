"""Giving shares back (#544, #637; the mechanics §12.3, Q113; ``docs/adr/0190`` §4).

**A share only held is let go; a share taken is refunded.** Since the fill
holds every share until the club's cut-off (#637), giving a share back before
then takes nothing: the hold is **let go** (``SeatCharge.let_go``) — nothing is
refunded, no fee arises, nobody pays, the club included — and its player is
told *nothing was taken*. A share already taken — at the cut-off, at once after
it, or a rescuer's — is **refunded**.

**Decided here, made at the provider after the commit** — the fill's rule for
a capture, kept for a refund and a release: each share is marked in the
caller's transaction (``SeatChargeReleased`` with its reason, or
``SeatChargeRefundDecided``), and ``SettleSeatCharges`` cancels the hold or
refunds the payment from the outbox. A crash between the two leaves a decision
a subscriber retries.

**Five reasons, two amounts for a share taken.** A player who **left after**
the club's cut-off is refunded **less the card fee** the moment somebody takes
their seat (#545). One who left **before** it with their share taken already —
only #639's fallback takes one that early — gets **everything back**: leaving
before the cut-off costs nobody anything (Q113). A game **called off
at its cut-off** gives a share taken **everything back** — the fallback of
#639 — and so does a game **the club cancelled** (#547) after its cut-off, its
reason said in the email, to everybody still in and to **a leaver whose seat
it left open and paid**, who is told in a leaver's words and promised no new
game (#623, Q108). Each player is emailed — every notice about money is.

**Nothing here commits**: the act is the caller's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.application.ports import MailQueue
from app.kernel import Instant, invariant
from app.modules.payments.application.seat_charge_emails import (
    CancelledBecause,
    game_called_off_email,
    game_cancelled_email,
    game_you_left_cancelled_email,
    left_the_game_email,
    seat_taken_email,
)
from app.modules.payments.domain.card_fee import estimated_card_fee
from app.modules.payments.domain.ports import Payers, SeatChargeRepository, Sellers
from app.modules.payments.domain.seat_charge import RefundReason, SeatCharge


#: The reasons that give a share taken everything back: the club's own rules —
#: and a leave before the cut-off, which takes nothing from anybody (#637): a
#: share taken before it — only #639's fallback takes one — comes back whole.
_IN_FULL = frozenset(
    {
        RefundReason.LEFT,
        RefundReason.CALLED_OFF_AT_THE_CUT_OFF,
        RefundReason.CANCELLED_BY_THE_CLUB,
        RefundReason.CANCELLED_AFTER_YOU_LEFT,
    }
)

#: The club's cancel, which says its reason.
_CANCELLED = frozenset(
    {RefundReason.CANCELLED_BY_THE_CLUB, RefundReason.CANCELLED_AFTER_YOU_LEFT}
)


@final
class GiveTheSharesBack:
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
        because: CancelledBecause | None = None,
    ) -> Mapping[UUID, SeatCharge]:
        """Give back each of these players' share of this game: let go a share
        only held, refund a share taken. Answers each player's charge that was
        let go or a refund was decided on — a share nobody paid, or one already
        being given back, is not. ``because`` is the club's reason, on a game
        it cancelled."""

        invariant(
            (reason in _CANCELLED) == (because is not None),
            f"a {reason} refund of {game_id} because {because}",
        )
        withhold_fee = reason not in _IN_FULL
        let_go: dict[UUID, SeatCharge] = {}
        refunded: dict[UUID, SeatCharge] = {}
        for charge in await self._charges.of_game(game_id):
            if charge.player_id not in players:
                continue
            if charge.let_go(at=at, reason=reason):
                await self._charges.save(charge)
                let_go[charge.player_id] = charge
            elif charge.refund(withhold_fee=withhold_fee, at=at, reason=reason):
                await self._charges.save(charge)
                refunded[charge.player_id] = charge
        await self._email(let_go, held=True, reason=reason, because=because, at=at)
        await self._email(refunded, held=False, reason=reason, because=because, at=at)
        return {**let_go, **refunded}

    async def _email(
        self,
        given_back: Mapping[UUID, SeatCharge],
        *,
        held: bool,
        reason: RefundReason,
        because: CancelledBecause | None,
        at: Instant,
    ) -> None:
        """Each player told what came of their share: let go, if it was only
        ``held`` — *nothing was taken* — or refunded."""

        if not given_back:
            return
        sellers = await self._sellers.of({c.club_id for c in given_back.values()})
        payers = await self._payers.of(list(given_back))
        for player, charge in given_back.items():
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
                    app_link=self._app_link,
                    held=held,
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
                    held=held,
                )
            elif (
                reason is RefundReason.CANCELLED_AFTER_YOU_LEFT and because is not None
            ):
                message = game_you_left_cancelled_email(
                    to=payer.email,
                    name=payer.name,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    because=because,
                    app_link=self._app_link,
                    held=held,
                )
            elif because is not None:
                message = game_cancelled_email(
                    to=payer.email,
                    name=payer.name,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    because=because,
                    app_link=self._app_link,
                    held=held,
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
                    held=held,
                )
            await self._mail.enqueue(message, at=at)


__all__ = ["GiveTheSharesBack", "RefundReason"]
