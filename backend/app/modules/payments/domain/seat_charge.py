"""The Seat charge aggregate — event-sourced, one stream per payment for one
player's share of one game (``docs/adr/0189`` §5; the mechanics §12.2).

**Raketa's account of a payment; the provider is the ledger of record.** A
charge is born at the fill and never before — a yes moves no money — either
**held** on the player's card or **refused**, and is then moved by two kinds of
fact. Three rules shape it.

**The fill decides, the provider acts.** Whether a hold is *kept*, *taken* or
*released* is decided with the booking, in its transaction (``keep``, ``take``,
``release``); the capture or the cancellation at the provider follows the
commit, from the outbox, and is recorded when the provider answers
(``captured``, ``cancelled``). So a crash between the two leaves a decision on
the record and a subscriber that retries it, never money moved with nothing
written.

**Held until the cut-off, taken then** (#637; ADR-0189's 2026-10-10
amendment). A game that books before its club's cut-off **keeps** each hold for
the booked game (``HELD``, ``held_until`` the cut-off) and takes nothing; the
cut-off **takes** it. Before then it is **let go** (``let_go``) — a leave, a
game short at its cut-off, the club's cancel — which costs nobody anything. A
held charge is **not paid** and **not settled**: no receipt, no *Collected*, no
payout until it is taken. A game that books after its cut-off is taken at
once.

**A refused charge waits for its player.** The bank wanted them present, or
refused the card: the player can confirm **this same payment** in the app, and
once the provider holds it (``confirm``) it is held like any other — *your yes
again*. A charge that needed nothing of the provider — no method, or terms to
accept again — has no payment to confirm.

**A notice moves it only forward** (``heard``). The provider's word arrives
twice and out of order, so a reading that would take a charge backwards — a
hold heard after its capture — is the past arriving late and records nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.payments.domain.card_fee import estimated_card_fee
from app.modules.payments.domain.events import (
    SeatChargeAuthorised,
    SeatChargeCancelled,
    SeatChargeCaptured,
    SeatChargeConfirmed,
    SeatChargeFailed,
    SeatChargeFeeReported,
    SeatChargeKept,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.domain.provider import Payment, PaymentStatus, Refund
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


class SeatChargeStatus(StrEnum):
    """Where a charge stands, as its stream leaves it."""

    #: Held on the card, and not yet decided.
    AUTHORISED = "AUTHORISED"
    #: Refused at the fill; waits for its player.
    FAILED = "FAILED"
    #: The game booked before its cut-off: held for it until then (#637).
    #: **Not paid.**
    HELD = "HELD"
    #: Taken — at the cut-off, or the game booked after it: to be captured.
    TAKING = "TAKING"
    #: Taken. **Paid.**
    CAPTURED = "CAPTURED"
    #: The game did not book on it, or its held share was let go: to be
    #: cancelled.
    RELEASING = "RELEASING"
    #: Released untaken. Nobody paid.
    CANCELLED = "CANCELLED"


#: The two a player has paid in: taken, or being taken. Never ``HELD``.
PAID = frozenset({SeatChargeStatus.TAKING, SeatChargeStatus.CAPTURED})


class RefundReason(StrEnum):
    """Why a share is given back. **A share held for the booked game is let go**
    whatever the reason — nothing was taken, so nothing is refunded and no fee
    arises (#637) — and **a share already taken is refunded**, by its reason's
    amount."""

    #: The player left before the club's cut-off: a held share is let go. A
    #: share taken already — only the fallback of #639 takes one before the
    #: cut-off — is refunded less the card fee.
    LEFT = "LEFT"
    #: The game was called off at the club's cut-off: in full.
    CALLED_OFF_AT_THE_CUT_OFF = "CALLED_OFF_AT_THE_CUT_OFF"
    #: The player left after the cut-off and somebody took their seat (#545):
    #: less the card fee.
    SEAT_TAKEN = "SEAT_TAKEN"
    #: The club cancelled the booked game (#547): in full — the club bears the
    #: fees, as the seller.
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: The club cancelled a booked game the player had left after the cut-off,
    #: their seat still open and paid (#623, Q108): in full, as everybody's —
    #: told in a leaver's words, and owed no new game.
    CANCELLED_AFTER_YOU_LEFT = "CANCELLED_AFTER_YOU_LEFT"


class FailureReason(StrEnum):
    """Why a share could not be held (the mechanics §12.2, §19)."""

    #: The bank wants the player present — they confirm the payment in the app.
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    #: The bank refused the card — they confirm the payment with another one.
    DECLINED = "DECLINED"
    #: The terms in force were not accepted for the card — its brand changed,
    #: or the words did (#637) — they accept them again. The provider was
    #: never asked.
    TERMS_NEEDED = "TERMS_NEEDED"
    #: There is no method to charge. The provider was never asked.
    NO_METHOD = "NO_METHOD"


@dataclass(frozen=True, slots=True)
class RefundGiven:
    """What the provider gave back of a paid share, and the fee it kept."""

    refund_id: str
    amount_grosze: int
    fee_withheld_grosze: int
    at: Instant


@dataclass
class SeatCharge:
    """One payment for one player's share of one game."""

    charge_id: UUID
    player_id: UUID
    game_id: UUID
    club_id: UUID
    account_id: str
    payment_id: str | None
    amount_grosze: int
    sport: Sport
    starts_at: Instant
    status: SeatChargeStatus
    failure: FailureReason | None
    #: When it was born.
    opened_at: Instant
    #: The booking it was kept or taken for, once it was.
    booking_id: UUID | None = None
    #: The club's cut-off a share held for the booked game is taken at — while
    #: it is held, and kept on the record after (#637).
    held_until: Instant | None = None
    #: Why a held share was let go, when it was (#637).
    let_go_because: RefundReason | None = None
    #: When it was taken — the moment the player paid.
    taken_at: Instant | None = None
    #: Whether the refund decided on it keeps the card fee back — ``None``
    #: while none was decided (#544).
    refund_withholds_fee: bool | None = None
    #: When it was decided — the leaving, or the call-off — which is when the
    #: player was refunded, as their receipt says.
    refund_decided_at: Instant | None = None
    #: What the provider gave back, once it did.
    refund_given: RefundGiven | None = None
    #: The real fee the provider kept when it took the share (#548) — said on
    #: the capture, or reported later; ``None`` while it is not yet known.
    fee_taken_grosze: int | None = None
    #: When the hold ends unless it is taken, as the provider said when it
    #: held the share — or when its player confirmed it (ADR-0190's 2026-10-10
    #: amendment). ``None`` where it did not say.
    last_moment: Instant | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    # ---------------------------------------------------------------- birth

    @classmethod
    def held(
        cls,
        *,
        charge_id: UUID,
        player_id: UUID,
        game_id: UUID,
        club_id: UUID,
        account_id: str,
        payment: Payment,
        sport: Sport,
        starts_at: Instant,
        at: Instant,
    ) -> "SeatCharge":
        invariant(
            payment.status is PaymentStatus.AUTHORISED,
            f"a hold the provider answered {payment.status}",
        )
        authorised = SeatChargeAuthorised(
            charge_id=charge_id,
            player_id=player_id,
            game_id=game_id,
            club_id=club_id,
            account_id=account_id,
            payment_id=payment.payment_id,
            amount_grosze=payment.amount_grosze,
            sport=sport.value,
            starts_at=starts_at,
            occurred_at=at,
            last_moment=payment.last_moment,
        )
        charge = cls._born(authorised)
        charge._events.record(authorised)
        return charge

    @classmethod
    def refused(
        cls,
        *,
        charge_id: UUID,
        player_id: UUID,
        game_id: UUID,
        club_id: UUID,
        account_id: str,
        amount_grosze: int,
        sport: Sport,
        starts_at: Instant,
        reason: FailureReason,
        payment: Payment | None,
        at: Instant,
    ) -> "SeatCharge":
        """A share that could not be held: ``payment`` is the provider's answer,
        or ``None`` where it was never asked."""

        asked = reason in (
            FailureReason.AUTHENTICATION_REQUIRED,
            FailureReason.DECLINED,
        )
        invariant(
            asked == (payment is not None),
            f"a {reason} refusal with payment {payment!r}",
        )
        failed = SeatChargeFailed(
            charge_id=charge_id,
            player_id=player_id,
            game_id=game_id,
            club_id=club_id,
            account_id=account_id,
            payment_id=None if payment is None else payment.payment_id,
            amount_grosze=amount_grosze,
            sport=sport.value,
            starts_at=starts_at,
            reason=reason.value,
            decline_code=None if payment is None else payment.decline_code,
            occurred_at=at,
        )
        charge = cls._born(failed)
        charge._events.record(failed)
        return charge

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "SeatCharge":
        history = iter(events)
        opening = next(history)
        invariant(
            isinstance(opening, (SeatChargeAuthorised, SeatChargeFailed)),
            f"a seat charge stream opens {opening!r}",
        )
        assert isinstance(opening, (SeatChargeAuthorised, SeatChargeFailed))
        charge = cls._born(opening)
        for event in history:
            charge._apply(event)
        return charge

    @classmethod
    def _born(cls, opening: SeatChargeAuthorised | SeatChargeFailed) -> "SeatCharge":
        failed = isinstance(opening, SeatChargeFailed)
        return cls(
            charge_id=opening.charge_id,
            player_id=opening.player_id,
            game_id=opening.game_id,
            club_id=opening.club_id,
            account_id=opening.account_id,
            payment_id=opening.payment_id,
            amount_grosze=opening.amount_grosze,
            sport=Sport(opening.sport),
            starts_at=instant(opening.starts_at),
            status=SeatChargeStatus.FAILED if failed else SeatChargeStatus.AUTHORISED,
            failure=(
                FailureReason(opening.reason)
                if isinstance(opening, SeatChargeFailed)
                else None
            ),
            opened_at=instant(opening.occurred_at),
            last_moment=(
                instant(opening.last_moment)
                if isinstance(opening, SeatChargeAuthorised)
                and opening.last_moment is not None
                else None
            ),
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ---------------------------------------------------------------- reads

    @property
    def held_now(self) -> bool:
        """Held on the card and not yet decided — what a later fill may take."""

        return self.status is SeatChargeStatus.AUTHORISED

    @property
    def owes_a_refund(self) -> bool:
        """A refund was decided and the provider has not given it yet."""

        return self.refund_withholds_fee is not None and self.refund_given is None

    @property
    def refund_to_ask_grosze(self) -> int | None:
        """Exactly what the refund decided on this share asks the provider for
        (ADR-0190's 2026-10-10 amendment): the whole share, or the share less
        **the fee kept on this payment** — ``None`` while that fee is not yet
        known, and the refund waits for it. ``None`` with no refund owed."""

        if not self.owes_a_refund:
            return None
        if not self.refund_withholds_fee:
            return self.amount_grosze
        if self.fee_taken_grosze is None:
            return None
        return self.amount_grosze - min(self.fee_taken_grosze, self.amount_grosze)

    @property
    def given_back_grosze(self) -> int:
        """What this share gives back (#547): what the provider gave, once it
        has answered — until then what was decided, the share less the fee
        kept on it where the fee is withheld (the estimate while that is not
        yet known), never below nought — and nought with no refund decided."""

        if self.refund_given is not None:
            return self.refund_given.amount_grosze
        if self.refund_withholds_fee is None:
            return 0
        if not self.refund_withholds_fee:
            return self.amount_grosze
        fee = (
            self.fee_taken_grosze
            if self.fee_taken_grosze is not None
            else estimated_card_fee(self.amount_grosze)
        )
        return self.amount_grosze - min(fee, self.amount_grosze)

    @property
    def card_fee_grosze(self) -> int:
        """The card fee the club pays on this share (#548; the mechanics
        §16.11) — the provider's own figure once it has said one, on the
        capture or on a refund that kept it back, and until then the estimate;
        nought on a share nobody paid. A refund never returns it."""

        if self.status not in PAID:
            return 0
        if self.fee_taken_grosze is not None:
            return self.fee_taken_grosze
        if self.refund_given is not None and self.refund_given.fee_withheld_grosze:
            return self.refund_given.fee_withheld_grosze
        return estimated_card_fee(self.amount_grosze)

    @property
    def net_grosze(self) -> int:
        """What is the club's of this share (#548): what was paid, less what
        was given back, less the card fee — below nought on a share given back
        whole, whose fee the club bears; nought on a share nobody paid."""

        if self.status not in PAID:
            return 0
        return self.amount_grosze - self.given_back_grosze - self.card_fee_grosze

    @property
    def settled(self) -> bool:
        """Nothing about this share's money is still on its way (#548): no
        share held to be taken (#637), no capture still to make, no refund
        decided and not yet given. A share let go is settled."""

        return (
            self.status not in (SeatChargeStatus.HELD, SeatChargeStatus.TAKING)
            and not self.owes_a_refund
        )

    @property
    def awaits_its_player(self) -> bool:
        """Refused, with a payment the player can confirm in the app."""

        return self.status is SeatChargeStatus.FAILED and self.payment_id is not None

    # ----------------------------------------------------------------- acts

    def confirm(self, *, at: Instant, last_moment: Instant | None = None) -> bool:
        """The provider holds a payment that was refused, until
        ``last_moment``: the player confirmed it in the app. Answers whether
        anything was recorded — nothing for a charge no longer waiting."""

        if self.status is not SeatChargeStatus.FAILED or self.payment_id is None:
            return False
        self._record_that(
            SeatChargeConfirmed(
                charge_id=self.charge_id,
                player_id=self.player_id,
                occurred_at=at,
                last_moment=last_moment,
            )
        )
        return True

    def keep(self, *, booking_id: UUID, until: Instant, at: Instant) -> None:
        """The game booked on this hold before its club's cut-off, ``until``:
        it is kept for the game and taken then (#637)."""

        invariant(self.held_now, f"keeping {self.charge_id}, {self.status}")
        self._record_that(
            SeatChargeKept(
                charge_id=self.charge_id,
                player_id=self.player_id,
                booking_id=booking_id,
                until=until,
                occurred_at=at,
            )
        )

    def take(self, *, booking_id: UUID, at: Instant) -> None:
        """The share is taken: the game booked on this hold after its cut-off,
        or the cut-off came for a share held for it."""

        invariant(
            self.held_now or self.status is SeatChargeStatus.HELD,
            f"taking {self.charge_id}, {self.status}",
        )
        self._record_that(
            SeatChargeTaken(
                charge_id=self.charge_id,
                player_id=self.player_id,
                booking_id=booking_id,
                occurred_at=at,
                kept=self.status is SeatChargeStatus.HELD,
            )
        )

    def release(self, *, at: Instant) -> bool:
        """The game will not book on this charge. Answers whether anything was
        recorded — nothing for one already taken, released or settled, and
        nothing for a share held for the booked game, which is the game's to
        let go (``let_go``)."""

        if self.status not in (SeatChargeStatus.AUTHORISED, SeatChargeStatus.FAILED):
            return False
        self._record_that(
            SeatChargeReleased(
                charge_id=self.charge_id, player_id=self.player_id, occurred_at=at
            )
        )
        return True

    def let_go(self, *, at: Instant, reason: RefundReason | None = None) -> bool:
        """A share held for the booked game is given up before it is taken —
        for ``reason``: nothing was taken, so nothing is refunded and no fee
        arises (#637). Answers whether anything was recorded: nothing for a
        share not held for a game."""

        if self.status is not SeatChargeStatus.HELD:
            return False
        self._record_that(
            SeatChargeReleased(
                charge_id=self.charge_id,
                player_id=self.player_id,
                occurred_at=at,
                reason=None if reason is None else reason.value,
            )
        )
        return True

    def refund(
        self, *, withhold_fee: bool, at: Instant, reason: RefundReason | None = None
    ) -> bool:
        """Give this paid share back — less the card fee, or whole — for
        ``reason``. Answers whether anything was recorded: nothing for a share
        nobody paid, and nothing for one already being given back."""

        if self.status not in PAID or self.refund_withholds_fee is not None:
            return False
        self._record_that(
            SeatChargeRefundDecided(
                charge_id=self.charge_id,
                player_id=self.player_id,
                withhold_fee=withhold_fee,
                occurred_at=at,
                reason=None if reason is None else reason.value,
            )
        )
        return True

    def refunded(self, refund: Refund, *, at: Instant) -> bool:
        """The provider's answer to the refund decided on this share — which
        gave back what it was asked, so what was kept of the share is the rest.
        Nothing is recorded for one already answered."""

        invariant(
            self.refund_withholds_fee is not None,
            f"{self.charge_id} refunded with no refund decided",
        )
        if self.refund_given is not None:
            return False
        self._record_that(
            SeatChargeRefunded(
                charge_id=self.charge_id,
                player_id=self.player_id,
                refund_id=refund.refund_id,
                amount_grosze=refund.amount_grosze,
                fee_withheld_grosze=self.amount_grosze - refund.amount_grosze,
                occurred_at=at,
            )
        )
        return True

    def captured(self, *, at: Instant, fee_grosze: int | None = None) -> bool:
        """The provider took the share, and — where it said — the card fee on
        it. Nothing is recorded for one not being taken."""

        if self.status is not SeatChargeStatus.TAKING:
            return False
        self._record_that(
            SeatChargeCaptured(
                charge_id=self.charge_id,
                player_id=self.player_id,
                occurred_at=at,
                fee_grosze=fee_grosze,
            )
        )
        return True

    def fee_reported(self, fee_grosze: int | None, *, at: Instant) -> bool:
        """The real fee kept on a share taken while it was not yet known,
        reported now — a club on its own negotiated pricing. Nothing is
        recorded for a fee still unknown, nor for one already recorded."""

        if (
            fee_grosze is None
            or self.status is not SeatChargeStatus.CAPTURED
            or self.fee_taken_grosze is not None
        ):
            return False
        self._record_that(
            SeatChargeFeeReported(
                charge_id=self.charge_id,
                player_id=self.player_id,
                fee_grosze=fee_grosze,
                occurred_at=at,
            )
        )
        return True

    def cancelled(self, *, at: Instant) -> bool:
        """The provider released the payment untaken — because it was let go,
        or on its own: a hold it dropped, a payment nobody confirmed. Nothing
        is recorded for one taken or already settled."""

        if self.status not in (
            SeatChargeStatus.RELEASING,
            SeatChargeStatus.AUTHORISED,
            SeatChargeStatus.HELD,
            SeatChargeStatus.FAILED,
        ):
            return False
        self._record_that(
            SeatChargeCancelled(
                charge_id=self.charge_id, player_id=self.player_id, occurred_at=at
            )
        )
        return True

    def heard(self, payment: Payment, *, at: Instant) -> bool:
        """The provider's reading of this charge's payment, after a notice.
        **Only forward**: a reading this charge has already moved past is the
        past arriving late. Answers whether anything was recorded."""

        invariant(
            payment.payment_id == self.payment_id,
            f"{payment.payment_id} read for {self.charge_id}",
        )
        if payment.status is PaymentStatus.AUTHORISED:
            return self.confirm(at=at, last_moment=payment.last_moment)
        if payment.status is PaymentStatus.CAPTURED:
            return self.captured(
                at=at, fee_grosze=payment.fee_grosze
            ) or self.fee_reported(payment.fee_grosze, at=at)
        if payment.status is PaymentStatus.CANCELLED:
            return self.cancelled(at=at)
        return False

    # ----------------------------------------------------------------- fold

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, SeatChargeConfirmed):
            self.status = SeatChargeStatus.AUTHORISED
            if event.last_moment is not None:
                self.last_moment = instant(event.last_moment)
        elif isinstance(event, SeatChargeKept):
            self.status = SeatChargeStatus.HELD
            self.booking_id = event.booking_id
            self.held_until = instant(event.until)
        elif isinstance(event, SeatChargeTaken):
            self.status = SeatChargeStatus.TAKING
            self.booking_id = event.booking_id
            self.taken_at = instant(event.occurred_at)
        elif isinstance(event, SeatChargeReleased):
            self.status = SeatChargeStatus.RELEASING
            if event.reason is not None:
                self.let_go_because = RefundReason(event.reason)
        elif isinstance(event, SeatChargeCaptured):
            self.status = SeatChargeStatus.CAPTURED
            self.fee_taken_grosze = event.fee_grosze
        elif isinstance(event, SeatChargeFeeReported):
            self.fee_taken_grosze = event.fee_grosze
        elif isinstance(event, SeatChargeCancelled):
            self.status = SeatChargeStatus.CANCELLED
        elif isinstance(event, SeatChargeRefundDecided):
            self.refund_withholds_fee = event.withhold_fee
            self.refund_decided_at = instant(event.occurred_at)
        elif isinstance(event, SeatChargeRefunded):
            self.refund_given = RefundGiven(
                refund_id=event.refund_id,
                amount_grosze=event.amount_grosze,
                fee_withheld_grosze=event.fee_withheld_grosze,
                at=instant(event.occurred_at),
            )
        else:
            raise TypeError(f"Unsupported seat charge event {event!r}")
        self.version += 1
