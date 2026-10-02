"""The Seat charge aggregate — event-sourced, one stream per payment for one
player's share of one game (``docs/adr/0189`` §5; the mechanics §12.2).

**Raketa's account of a payment; the provider is the ledger of record.** A
charge is born at the fill and never before — a yes moves no money — either
**held** on the player's card or **refused**, and is then moved by two kinds of
fact. Three rules shape it.

**The fill decides, the provider acts.** Whether a hold is *taken* or *released*
is decided with the booking, in its transaction (``take``, ``release``); the
capture or the cancellation at the provider follows the commit, from the
outbox, and is recorded when the provider answers (``captured``,
``cancelled``). So a crash between the two leaves a decision on the record and a
subscriber that retries it, never money moved with nothing written.

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
    #: The game booked: to be captured.
    TAKING = "TAKING"
    #: Taken. **Paid.**
    CAPTURED = "CAPTURED"
    #: The game did not book on it: to be cancelled.
    RELEASING = "RELEASING"
    #: Released untaken. Nobody paid.
    CANCELLED = "CANCELLED"


#: The two a player has paid in: taken, or being taken.
PAID = frozenset({SeatChargeStatus.TAKING, SeatChargeStatus.CAPTURED})


class FailureReason(StrEnum):
    """Why a share could not be held (the mechanics §12.2, §19)."""

    #: The bank wants the player present — they confirm the payment in the app.
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    #: The bank refused the card — they confirm the payment with another one.
    DECLINED = "DECLINED"
    #: The card's brand changed since the terms were accepted — they accept
    #: them again. The provider was never asked.
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
    #: The booking it was taken for, once it was.
    booking_id: UUID | None = None
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
    #: The card fee the provider said it took on the capture (#548).
    fee_taken_grosze: int | None = None
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
    def given_back_grosze(self) -> int:
        """What this share gives back (#547): what the provider gave, once it
        has answered — until then what was decided, the share less the card
        fee's estimate where the fee is withheld, never below nought — and
        nought with no refund decided."""

        if self.refund_given is not None:
            return self.refund_given.amount_grosze
        if self.refund_withholds_fee is None:
            return 0
        if not self.refund_withholds_fee:
            return self.amount_grosze
        return self.amount_grosze - min(
            estimated_card_fee(self.amount_grosze), self.amount_grosze
        )

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
        capture still to make, no refund decided and not yet given."""

        return self.status is not SeatChargeStatus.TAKING and not self.owes_a_refund

    @property
    def awaits_its_player(self) -> bool:
        """Refused, with a payment the player can confirm in the app."""

        return self.status is SeatChargeStatus.FAILED and self.payment_id is not None

    # ----------------------------------------------------------------- acts

    def confirm(self, *, at: Instant) -> bool:
        """The provider holds a payment that was refused: the player confirmed
        it in the app. Answers whether anything was recorded — nothing for a
        charge no longer waiting."""

        if self.status is not SeatChargeStatus.FAILED or self.payment_id is None:
            return False
        self._record_that(
            SeatChargeConfirmed(
                charge_id=self.charge_id, player_id=self.player_id, occurred_at=at
            )
        )
        return True

    def take(self, *, booking_id: UUID, at: Instant) -> None:
        """The game booked on this hold."""

        invariant(self.held_now, f"taking {self.charge_id}, {self.status}")
        self._record_that(
            SeatChargeTaken(
                charge_id=self.charge_id,
                player_id=self.player_id,
                booking_id=booking_id,
                occurred_at=at,
            )
        )

    def release(self, *, at: Instant) -> bool:
        """The game will not book on this charge. Answers whether anything was
        recorded — nothing for one already taken, released or settled."""

        if self.status not in (SeatChargeStatus.AUTHORISED, SeatChargeStatus.FAILED):
            return False
        self._record_that(
            SeatChargeReleased(
                charge_id=self.charge_id, player_id=self.player_id, occurred_at=at
            )
        )
        return True

    def refund(self, *, withhold_fee: bool, at: Instant) -> bool:
        """Give this paid share back — less the card fee, or whole. Answers
        whether anything was recorded: nothing for a share nobody paid, and
        nothing for one already being given back."""

        if self.status not in PAID or self.refund_withholds_fee is not None:
            return False
        self._record_that(
            SeatChargeRefundDecided(
                charge_id=self.charge_id,
                player_id=self.player_id,
                withhold_fee=withhold_fee,
                occurred_at=at,
            )
        )
        return True

    def refunded(self, refund: Refund, *, at: Instant) -> bool:
        """The provider's answer to the refund decided on this share. Nothing
        is recorded for one already answered."""

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
                fee_withheld_grosze=refund.fee_withheld_grosze,
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

    def cancelled(self, *, at: Instant) -> bool:
        """The provider released the payment untaken — because it was let go,
        or on its own: a hold it dropped, a payment nobody confirmed. Nothing
        is recorded for one taken or already settled."""

        if self.status not in (
            SeatChargeStatus.RELEASING,
            SeatChargeStatus.AUTHORISED,
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
            return self.confirm(at=at)
        if payment.status is PaymentStatus.CAPTURED:
            return self.captured(at=at, fee_grosze=payment.fee_grosze)
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
        elif isinstance(event, SeatChargeTaken):
            self.status = SeatChargeStatus.TAKING
            self.booking_id = event.booking_id
            self.taken_at = instant(event.occurred_at)
        elif isinstance(event, SeatChargeReleased):
            self.status = SeatChargeStatus.RELEASING
        elif isinstance(event, SeatChargeCaptured):
            self.status = SeatChargeStatus.CAPTURED
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
