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
the club's cut-off is refunded **less exactly the fee kept on their payment**
the moment somebody takes their seat (#545, #641) — never an estimate: while
that fee is not yet known the refund waits for it. One who left **before** it
with their share taken already — only #639's fallback takes one that early —
gets **everything back**: leaving before the cut-off costs nobody anything
(Q113). A game **called off at its cut-off** gives a share taken **everything
back** — the fallback of
#639 — and so does a game **the club cancelled** (#547) after its cut-off, its
reason said in the email, to everybody still in and to **a leaver whose seat
it left open and paid**, who is told in a leaver's words and promised no new
game (#623, Q108). Each player is emailed — every notice about money is — and
**the seat-taken refund is emailed when it is made** (``EmailTheSeatTakenRefund``),
since only then is its sum known to the grosz.

**A late leaver is told the figure when they leave** (``TellTheLateLeaver``,
#641; the mechanics §13): nothing comes back yet, and the email says what will
if somebody takes the seat — or no figure while the fee is not yet known.

**Nothing here commits**: the act is the caller's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.application.events import DeliveryContext
from app.application.ports import MailQueue
from app.kernel import Instant, instant, invariant
from app.modules.payments.application.seat_charge_emails import (
    CancelledBecause,
    game_called_off_email,
    game_cancelled_email,
    game_you_left_cancelled_email,
    left_after_the_cut_off_email,
    left_the_game_email,
    seat_taken_email,
    seat_taken_nothing_taken_email,
)
from app.modules.payments.domain.events import SeatChargeRefunded
from app.modules.payments.domain.ports import (
    Payers,
    SeatChargeRepository,
    Seller,
    Sellers,
)
from app.modules.payments.domain.seat_charge import (
    PAID,
    RefundReason,
    SeatCharge,
    SeatChargeStatus,
)


#: The reasons that give a share taken everything back: the club's own rules —
#: and a leave before the cut-off, which takes nothing from anybody (#637): a
#: share taken before it — only #639's fallback takes one — comes back whole.
_IN_FULL = frozenset(
    {
        RefundReason.LEFT,
        RefundReason.CALLED_OFF_AT_THE_CUT_OFF,
        RefundReason.CANCELLED_BY_THE_CLUB,
        RefundReason.CANCELLED_AFTER_YOU_LEFT,
        RefundReason.CALLED_OFF_BY_THE_SENDER,
    }
)

#: The club's cancel, which says its reason.
_CANCELLED = frozenset(
    {RefundReason.CANCELLED_BY_THE_CLUB, RefundReason.CANCELLED_AFTER_YOU_LEFT}
)


def _club_named(seller: Seller | None) -> str:
    """The seller as an email names it — *the club* for one gone."""

    return "the club" if seller is None else seller.name


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
        if reason is not RefundReason.SEAT_TAKEN:
            # A seat-taken refund is emailed when it is made, to the grosz.
            await self._email(
                refunded, held=False, reason=reason, because=because, at=at
            )
        return {**let_go, **refunded}

    async def one_seat(
        self, game_id: UUID, payer: UUID, *, cover: bool, at: Instant
    ) -> SeatCharge | None:
        """**Somebody took a seat this payer paid** (#545, #752): give back
        **one** of their charges on the game, less exactly the fee kept on it —
        never everything they paid, since a friends game's sender pays several
        seats. Their own share, for a leaver's seat; with ``cover``, one of
        the sender's covers — or, every cover given back already, his own
        share, which is what pays his own seat with *Whole court* — and
        **nothing while a cover of his is still held**: the cut-off lets one
        go for the taker's own payment then (``SettleTheCovers``). A share only
        held is let go, as ``execute`` does. Answers the charge given back."""

        charges = [
            charge
            for charge in await self._charges.of_game(game_id)
            if charge.player_id == payer
        ]
        if cover:
            if any(
                charge.cover
                and (
                    charge.status in (SeatChargeStatus.HELD, SeatChargeStatus.CHECKED)
                    or charge.to_fix
                )
                for charge in charges
            ):
                return None
            order = sorted(charges, key=lambda charge: not charge.cover)
        else:
            order = [charge for charge in charges if not charge.cover]
        reason = RefundReason.SEAT_TAKEN
        for charge in order:
            if charge.let_go(at=at, reason=reason):
                await self._charges.save(charge)
                await self._email(
                    {payer: charge}, held=True, reason=reason, because=None, at=at
                )
                return charge
            if charge.refund(withhold_fee=True, at=at, reason=reason):
                # Emailed when it is made, to the grosz.
                await self._charges.save(charge)
                return charge
        return None

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
            club = _club_named(seller)
            # A share only checked, or refused at its holding (#639), had
            # nothing held on the card to let go.
            on_the_card = not held or charge.released_at is not None
            if reason is RefundReason.LEFT:
                message = left_the_game_email(
                    to=payer.email,
                    nickname=payer.nickname,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    share_grosze=charge.amount_grosze,
                    app_link=self._app_link,
                    held=held,
                    on_the_card=on_the_card,
                )
            elif reason is RefundReason.SEAT_TAKEN:
                # Only a share let go: one refunded is emailed when it is made.
                message = seat_taken_nothing_taken_email(
                    to=payer.email,
                    nickname=payer.nickname,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    share_grosze=charge.amount_grosze,
                    app_link=self._app_link,
                )
            elif (
                reason is RefundReason.CANCELLED_AFTER_YOU_LEFT and because is not None
            ):
                message = game_you_left_cancelled_email(
                    to=payer.email,
                    nickname=payer.nickname,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    because=because,
                    app_link=self._app_link,
                    held=held,
                    on_the_card=on_the_card,
                )
            elif because is not None:
                message = game_cancelled_email(
                    to=payer.email,
                    nickname=payer.nickname,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    because=because,
                    app_link=self._app_link,
                    held=held,
                    on_the_card=on_the_card,
                )
            else:
                message = game_called_off_email(
                    to=payer.email,
                    nickname=payer.nickname,
                    club=club,
                    sport=charge.sport,
                    starts_at=charge.starts_at,
                    refunded_grosze=charge.amount_grosze,
                    app_link=self._app_link,
                    held=held,
                    on_the_card=on_the_card,
                )
            await self._mail.enqueue(message, at=at)


@final
class EmailTheSeatTakenRefund:
    """*You've been refunded 38,24 zł · your seat was taken* — emailed **when
    the refund is made** (#641): the share less exactly the fee kept on the
    payment is known to the grosz only then, since a fee not yet known makes
    the refund wait. An outbox subscriber to ``SeatChargeRefunded``, added per
    delivery run over its session; a refund for any other reason was emailed
    when it was decided."""

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

    async def __call__(
        self, event: SeatChargeRefunded, context: DeliveryContext
    ) -> None:
        charge = await self._charges.load(event.charge_id)
        if (
            charge is None
            or charge.refund_reason is not RefundReason.SEAT_TAKEN
            or charge.refund_given is None
        ):
            return
        payer = (await self._payers.of([charge.player_id])).get(charge.player_id)
        if payer is None:
            return
        seller = (await self._sellers.of([charge.club_id])).get(charge.club_id)
        await self._mail.enqueue(
            seat_taken_email(
                to=payer.email,
                nickname=payer.nickname,
                club=_club_named(seller),
                sport=charge.sport,
                starts_at=charge.starts_at,
                share_grosze=charge.amount_grosze,
                refunded_grosze=charge.refund_given.amount_grosze,
                fee_kept_grosze=charge.refund_given.fee_withheld_grosze,
                app_link=self._app_link,
            ),
            at=instant(event.occurred_at),
        )


@final
class TellTheLateLeaver:
    """*You left the game* — after the club's cut-off (#641; the mechanics §13):
    the share stays paid and the seat is offered to others, and the email says
    what comes back if somebody takes it — the share less exactly the fee kept
    on the payment — or no figure and no clause while that fee is not yet
    known: a club on its own negotiated pricing, or a share the cut-off has not
    finished taking. **Nothing here commits**: the leaving is the caller's."""

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

    async def execute(self, game_id: UUID, player_id: UUID, *, at: Instant) -> None:
        shares = [
            charge
            for charge in await self._charges.of_game(game_id)
            if charge.player_id == player_id
            # Their own share: a friends game's sender's covers are no seat of
            # his to leave (#752).
            and not charge.cover
            and (charge.status in PAID or charge.status is SeatChargeStatus.HELD)
        ]
        payer = (await self._payers.of([player_id])).get(player_id)
        if not shares or payer is None:
            return
        share = shares[-1]
        seller = (await self._sellers.of([share.club_id])).get(share.club_id)
        await self._mail.enqueue(
            left_after_the_cut_off_email(
                to=payer.email,
                nickname=payer.nickname,
                club=_club_named(seller),
                sport=share.sport,
                starts_at=share.starts_at,
                share_grosze=share.amount_grosze,
                refund_grosze=share.less_the_fee_kept_grosze,
                fee_kept_grosze=share.fee_kept_grosze,
                app_link=self._app_link,
            ),
            at=at,
        )


__all__ = [
    "EmailTheSeatTakenRefund",
    "GiveTheSharesBack",
    "RefundReason",
    "TellTheLateLeaver",
]
