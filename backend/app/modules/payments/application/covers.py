"""**The Cover** — a friends game's sender's hold for a seat that isn't theirs
(#751; ``docs/adr/0202`` §6; the friends mechanics §8.1–§8.3, §10.3).

**At send, the whole court on the sender's card, all or nothing, with them
present** (``HoldTheCourt``). Their own share and **one cover per other seat**
are each a Seat charge — one hold per seat, today's hold, take and let-go steps
(call 1), so nothing is ever captured in part — authorised together on the
club's account. Every one held: each is kept until the cut-off (or checked, far
ahead, and held at its Holding time, as any seat charge is), the most they
agreed to is recorded with their terms acceptance (``MaximumAgreed``), and the
sender is emailed. **One refused: nothing is booked** — every hold just made is
let go, and each refused payment waits for its payer to confirm it in the app
(a bank that wants them present); confirmed, it is the hold the next send takes
rather than asking the bank again.

**A cover stays held until the cut-off** (call 7), and only there is it decided
(``SettleTheCovers``): **taken for a seat without its own payment, let go
otherwise.** Covers are never let go and held again in between: that would need
a new hold on the sender's card without them there, the day an accepted friend
left. They are interchangeable — the same payer, game and amount — so the
cut-off lets go one cover for each seat whose own player's share is held or
taken, and the take that follows takes the rest with everybody's shares.

**The holds are asked inline, because their answer is the response**, and
before anything is written (``docs/adr/0190`` §4); the capture and the
cancellation follow the commit, from the outbox. **The court is claimed before
the money** (``proposals``' send), so a refused card undoes the claim, and its
answers are asked again under the same keys and recorded as nothing booked
(``books`` false). **Nothing here commits.**
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import MailQueue
from app.kernel import Instant, Sport, invariant
from app.modules.payments.application.seat_charge_emails import court_held_email
from app.modules.payments.application.seat_charges import (
    RefusedSeat,
    held_for_the_game,
    held_on_the_card,
)
from app.modules.payments.application.setup import key_hour
from app.modules.payments.domain.errors import SeatChargeNotFound
from app.modules.payments.domain.ports import (
    Payers,
    PaymentMethodRepository,
    SeatChargeRepository,
    Seller,
    Sellers,
)
from app.modules.payments.domain.provider import Payment, PaymentProvider
from app.modules.payments.domain.seat_charge import (
    PAID,
    FailureReason,
    RefundReason,
    SeatCharge,
    SeatChargeStatus,
)
from app.shared.ids import new_uuid

#: The refusals that asked the provider nothing — no method, terms to accept
#: again: every other seat would be refused the same, so none is asked.
_ASKED_NOTHING = frozenset({FailureReason.NO_METHOD, FailureReason.TERMS_NEEDED})


@final
@dataclass(frozen=True, slots=True)
class CourtToHold:
    """A friends game being sent, as its money knows it."""

    #: The booking's own id, which every charge is made for.
    game_id: UUID
    club_id: UUID
    sport: Sport
    starts_at: Instant
    share_grosze: int
    #: The court it is booked on, for the email.
    court_name: str
    #: Every seat: the sender's share, and a cover for each of the others.
    seats: int
    #: *Pay the whole court* — for the email; the holds are the same.
    whole_court: bool
    #: The club's cut-off while it is ahead — the sender's share and every
    #: cover are **held** until then — or ``None`` for a game sent after it.
    free_to_leave_until: Instant | None
    #: Sent after the cut-off, when the covers are decided instead: the last
    #: invitation's end, never past the start. ``None`` before the cut-off,
    #: when the cut-off decides them.
    covers_until: Instant | None = None

    def __post_init__(self) -> None:
        invariant(self.seats >= 2, f"a court of {self.seats} seats held")
        invariant(
            (self.free_to_leave_until is None) == (self.covers_until is not None),
            f"{self.game_id}: covers held until {self.covers_until} with the "
            f"cut-off {self.free_to_leave_until} ahead",
        )


@final
@dataclass(frozen=True, slots=True)
class CourtHeld:
    """Every seat held for the game — ``refused`` empty — or nothing booked:
    ``refused`` names each payment refused, the sender's to confirm."""

    #: Every charge the game is held on, the sender's share first.
    charges: tuple[UUID, ...]
    refused: tuple[RefusedSeat, ...]

    @property
    def all_held(self) -> bool:
        return not self.refused


def send_key(
    game_id: UUID, payer: UUID, *, seat: int, attempt: int, at: Instant
) -> str:
    """The key one seat's hold at send is asked under: the game, the payer, the
    seat — nought their own share, then each cover — the attempt and the hour,
    so a request retried is answered the same holds and the next send after a
    refusal asks afresh."""

    return f"rakieta-send-{game_id}-{payer}-{seat}-{attempt}-{key_hour(at)}"


@final
class HoldTheCourt:
    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        charges: SeatChargeRepository,
        sellers: Sellers,
        payers: Payers,
        provider: PaymentProvider,
        mail: MailQueue,
        app_link: str,
    ) -> None:
        self._methods = methods
        self._charges = charges
        self._sellers = sellers
        self._payers = payers
        self._provider = provider
        self._mail = mail
        self._app_link = app_link

    async def execute(
        self, court: CourtToHold, payer: UUID, *, at: Instant, books: bool = True
    ) -> CourtHeld:
        """``books`` false records the answers as nothing booked — every hold
        made let go, every refusal kept for the sender to confirm — whatever
        the provider says: the caller's booking did not stand."""

        seller = (await self._sellers.of([court.club_id])).get(court.club_id)
        invariant(
            seller is not None and seller.account_id is not None,
            f"a friends game sent at {court.club_id}, which takes no payments",
        )
        assert seller is not None and seller.account_id is not None
        made_before = await self._charges.of_game(court.game_id)
        if any(charge.player_id != payer for charge in made_before):
            # Somebody else's send: the id names nothing of this payer's.
            raise SeatChargeNotFound()
        # Payments the sender confirmed in the app since the last send: the
        # holds this one takes, their bank asked nothing again.
        confirmed = [charge for charge in made_before if charge.held_now]
        share = next((c for c in confirmed if not c.cover), None)
        covers = [c for c in confirmed if c.cover][: court.seats - 1]

        held: dict[int, Payment] = {}
        refused: dict[int, tuple[FailureReason, Payment | None]] = {}
        for seat in range(court.seats):
            if (seat == 0 and share is not None) or 0 < seat <= len(covers):
                continue
            outcome = await held_on_the_card(
                payer,
                methods=self._methods,
                provider=self._provider,
                seller=seller,
                amount_grosze=court.share_grosze,
                description=f"{court.sport.value.title()} · {seller.name}",
                game_id=court.game_id,
                key=send_key(
                    court.game_id,
                    payer,
                    seat=seat,
                    attempt=len(made_before),
                    at=at,
                ),
            )
            if isinstance(outcome, Payment):
                held[seat] = outcome
                continue
            refused[seat] = outcome
            if outcome[0] in _ASKED_NOTHING:
                break

        if refused or not books:
            return await self._nothing_booked(
                court, payer, held=held, refused=refused, seller=seller, at=at
            )
        made = {
            seat: self._a_hold(court, payer, payment, seat=seat, seller=seller, at=at)
            for seat, payment in held.items()
        }
        every = [
            share if share is not None else made[0],
            *covers,
            *(made[seat] for seat in sorted(made) if seat > 0),
        ]
        checked = await self._held_for_the_game(court, every, at=at)
        method = await self._methods.load(payer)
        method.agree_to_the_maximum(
            booking_id=court.game_id,
            amount_grosze=court.share_grosze * court.seats,
            at=at,
        )
        await self._methods.save(method)
        await self._email(court, payer, seller=seller, held_from=checked, at=at)
        return CourtHeld(charges=tuple(c.charge_id for c in every), refused=())

    async def _held_for_the_game(
        self, court: CourtToHold, every: Sequence[SeatCharge], *, at: Instant
    ) -> Instant | None:
        """Every hold the game's: the share kept until the cut-off and every
        cover with it — or, sent after it, the share taken now and every cover
        kept until the invitations end — each checked where it would not last
        (``held_for_the_game``). Answers the share's Holding time when it was
        only checked."""

        checked: Instant | None = None
        for charge in every:
            if court.free_to_leave_until is not None:
                until: Instant | None = court.free_to_leave_until
            else:
                until = court.covers_until if charge.cover else None
            hold_at = held_for_the_game(
                charge, booking_id=court.game_id, until=until, at=at
            )
            if hold_at is not None and not charge.cover:
                checked = hold_at
            await self._charges.save(charge)
        return checked

    async def _nothing_booked(
        self,
        court: CourtToHold,
        payer: UUID,
        *,
        held: dict[int, Payment],
        refused: dict[int, tuple[FailureReason, Payment | None]],
        seller: Seller,
        at: Instant,
    ) -> CourtHeld:
        """A refused card books nothing: every hold just made is let go, and
        each refusal recorded — its payment the sender's to confirm. A hold
        they confirmed before stays theirs for the next send."""

        assert seller.account_id is not None
        for seat, payment in held.items():
            charge = self._a_hold(
                court, payer, payment, seat=seat, seller=seller, at=at
            )
            charge.release(at=at)
            await self._charges.save(charge)
        seats: list[RefusedSeat] = []
        for seat, (reason, answer) in sorted(refused.items()):
            charge = SeatCharge.refused(
                charge_id=new_uuid(),
                player_id=payer,
                game_id=court.game_id,
                club_id=court.club_id,
                account_id=seller.account_id,
                amount_grosze=court.share_grosze,
                sport=court.sport,
                starts_at=court.starts_at,
                reason=reason,
                payment=answer,
                at=at,
                cover=seat > 0,
            )
            await self._charges.save(charge)
            seats.append(RefusedSeat(charge_id=charge.charge_id, reason=reason))
        return CourtHeld(charges=(), refused=tuple(seats))

    @staticmethod
    def _a_hold(
        court: CourtToHold,
        payer: UUID,
        payment: Payment,
        *,
        seat: int,
        seller: Seller,
        at: Instant,
    ) -> SeatCharge:
        assert seller.account_id is not None
        return SeatCharge.held(
            charge_id=new_uuid(),
            player_id=payer,
            game_id=court.game_id,
            club_id=court.club_id,
            account_id=seller.account_id,
            payment=payment,
            sport=court.sport,
            starts_at=court.starts_at,
            at=at,
            cover=seat > 0,
        )

    async def _email(
        self,
        court: CourtToHold,
        payer: UUID,
        *,
        seller: Seller,
        held_from: Instant | None,
        at: Instant,
    ) -> None:
        found = (await self._payers.of([payer])).get(payer)
        if found is None:
            return
        await self._mail.enqueue(
            court_held_email(
                to=found.email,
                nickname=found.nickname,
                club=seller.name,
                court=court.court_name,
                sport=court.sport,
                starts_at=court.starts_at,
                share_grosze=court.share_grosze,
                seats=court.seats,
                whole_court=court.whole_court,
                held_until=court.free_to_leave_until,
                held_from=held_from,
                app_link=self._app_link,
            ),
            at=at,
        )


@final
class SettleTheCovers:
    """**At the cut-off, each cover is taken or let go** (#751; call 7): one
    cover is **let go for each seat whose own player paid** — their share held
    or taken — and every other is left held, for the take that follows to take
    with everybody's shares. A cover refused at its Holding time goes first, so
    a held one is what pays an empty seat. Asked only once the moment covers
    are decided has come — the cut-off, or a game sent after it, when its
    invitations end. **No commit.**"""

    def __init__(self, *, charges: SeatChargeRepository) -> None:
        self._charges = charges

    async def execute(self, game_id: UUID, *, at: Instant) -> int:
        """Answers how many covers were let go."""

        charges = await self._charges.of_game(game_id)
        covers = [
            charge
            for charge in charges
            if charge.cover
            and charge.booking_id == game_id
            and (
                charge.status in (SeatChargeStatus.HELD, SeatChargeStatus.CHECKED)
                or charge.to_fix
            )
        ]
        if not covers:
            return 0
        payer = covers[0].player_id
        let_go_already = sum(
            1
            for charge in charges
            if charge.cover
            and charge.let_go_because is RefundReason.SEAT_PAID_BY_ITS_PLAYER
        )
        paid_by_their_own = sum(
            1
            for charge in charges
            if not charge.cover
            and charge.player_id != payer
            and charge.booking_id == game_id
            and (charge.status in PAID or charge.status is SeatChargeStatus.HELD)
        )
        # A held cover is the one an empty seat is paid with.
        covers.sort(key=lambda charge: charge.status is SeatChargeStatus.HELD)
        let_go = 0
        for cover in covers[: max(0, paid_by_their_own - let_go_already)]:
            if cover.let_go(at=at, reason=RefundReason.SEAT_PAID_BY_ITS_PLAYER):
                await self._charges.save(cover)
                let_go += 1
        return let_go


__all__ = [
    "CourtHeld",
    "CourtToHold",
    "HoldTheCourt",
    "SettleTheCovers",
    "send_key",
]
