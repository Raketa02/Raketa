"""The Seat charge aggregate — event-sourced, one stream per payment for one
player's share of one game (``docs/adr/0189`` §5; the mechanics §12.2).

**Rakieta's account of a payment; the provider is the ledger of record.** A
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

**A game that fills far ahead is checked** (#639; Q113). A card hold made
without its player lasts days — 4 days 18 hours on a Visa, 7 on a Mastercard —
and a hold **reaches** the cut-off only when its last moment is at least six
hours after it (``reaches``). One that does not is **checked** (``check``):
let go at once, which proves the money was there that day, and held again on a
new payment at its **Holding time**, four days before the cut-off
(``hold_again``) — or refused there (``holding_refused``), when its player has
their time to fix the card, and confirms or not. Closed by a leave before then,
it lets nothing go: nothing is held. A holding that still would not reach the
cut-off is taken at its last safe moment (``taken_by``) — the fallback,
which the documented windows never call for.

**A refused charge waits for its player.** The bank wanted them present, or
refused the card: the player can confirm **this same payment** in the app, and
once the provider holds it (``confirm``) it is held like any other — *your yes
again*. A charge that needed nothing of the provider — no method, or terms to
accept again — has no payment to confirm.

**A notice moves it only forward** (``heard``). The provider's word arrives
twice and out of order, so a reading that would take a charge backwards — a
hold heard after its capture — is the past arriving late and records nothing.

**No figure is an estimate** (#641; the mechanics §12.1, Q113). The fee kept on
a share is the provider's own, said on the capture or reported later; until
then the club's card fee, what a refund less it gives back, and what is the
club's are *not yet known* (``None``), and the share is not settled — the
payout waits for the fee, as a refund less it does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum
from typing import Final, Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant
from app.modules.payments.domain.events import (
    SeatChargeAuthorised,
    SeatChargeCancelled,
    SeatChargeCaptured,
    SeatChargeChecked,
    SeatChargeConfirmed,
    SeatChargeFailed,
    SeatChargeFeeReported,
    SeatChargeHeldAgain,
    SeatChargeHoldingRefused,
    SeatChargeKept,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.domain.provider import Payment, PaymentStatus, Refund
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: A hold **reaches** the club's cut-off when its last moment is at least this
#: long after it (#639; Q113): Stripe captures its own delayed payments about
#: six hours before a hold lapses. Domain, never configuration.
REACH_MARGIN: Final = timedelta(hours=6)

#: A checked share is held again this long before the cut-off — its **Holding
#: time** (#639; Q113): inside the shortest documented window, a Visa held
#: without its player for 4 days 18 hours, with margin. Domain, never
#: configuration.
HOLDING_LEAD: Final = timedelta(days=4)


def reaches(last_moment: Instant | None, *, cut_off: Instant) -> bool:
    """Whether a hold lasting until ``last_moment`` can be taken at the
    club's cut-off — ``True`` where the provider did not say when it ends."""

    return last_moment is None or last_moment - cut_off >= REACH_MARGIN


def holding_time(cut_off: Instant) -> Instant:
    """When a checked share is held again: four days before the cut-off."""

    return instant(cut_off - HOLDING_LEAD)


def taken_by(last_moment: Instant | None, *, cut_off: Instant) -> Instant:
    """When a share held now is taken: the club's cut-off — or, **the
    fallback**, a hold that would not reach it is taken at its **last safe
    moment**, its last moment less six hours, whichever comes first. The
    documented windows never call for it once a share is held at its Holding
    time (Q113)."""

    if reaches(last_moment, cut_off=cut_off):
        return cut_off
    assert last_moment is not None
    return min(cut_off, instant(last_moment - REACH_MARGIN))


class SeatChargeStatus(StrEnum):
    """Where a charge stands, as its stream leaves it."""

    #: Held on the card, and not yet decided.
    AUTHORISED = "AUTHORISED"
    #: Refused at the fill — or at its Holding time (#639); waits for its
    #: player.
    FAILED = "FAILED"
    #: The game booked before its cut-off on a hold that would not last until
    #: it: let go at once — a Card check — and held again at its Holding time
    #: (#639). **Not paid**, and nothing is held.
    CHECKED = "CHECKED"
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
    #: cut-off — is refunded in full.
    LEFT = "LEFT"
    #: The game was called off at the club's cut-off: in full.
    CALLED_OFF_AT_THE_CUT_OFF = "CALLED_OFF_AT_THE_CUT_OFF"
    #: The player left after the cut-off and somebody took their seat (#545):
    #: less exactly the fee kept on their payment (#641).
    SEAT_TAKEN = "SEAT_TAKEN"
    #: The club cancelled the booked game (#547): in full — the club bears the
    #: fees, as the seller.
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: The club cancelled a booked game the player had left after the cut-off,
    #: their seat still open and paid (#623, Q108): in full, as everybody's —
    #: told in a leaver's words, and owed no new game.
    CANCELLED_AFTER_YOU_LEFT = "CANCELLED_AFTER_YOU_LEFT"
    #: A friends game its sender called off before the cut-off (#751): every
    #: hold and cover let go — nothing was taken.
    CALLED_OFF_BY_THE_SENDER = "CALLED_OFF_BY_THE_SENDER"
    #: **A cover whose seat its own player paid** (#751; ``docs/adr/0202`` §6):
    #: let go at the cut-off, never before — told nobody, since the sender
    #: agreed to it only as the most they would pay.
    SEAT_PAID_BY_ITS_PLAYER = "SEAT_PAID_BY_ITS_PLAYER"


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
    #: When a share held for the booked game is taken — the club's cut-off, or
    #: a holding's last safe moment (#639) — while it is held or checked, and
    #: kept on the record after (#637).
    held_until: Instant | None = None
    #: A checked share's Holding time — when it is held again (#639). ``None``
    #: on a share never checked; kept on the record after.
    hold_at: Instant | None = None
    #: When it was taken — the moment the player paid.
    taken_at: Instant | None = None
    #: Whether the refund decided on it keeps the card fee back — ``None``
    #: while none was decided (#544).
    refund_withholds_fee: bool | None = None
    #: When it was decided — the leaving, or the call-off — which is when the
    #: player was refunded, as their receipt says.
    refund_decided_at: Instant | None = None
    #: Why it was decided — ``None`` on a refund recorded before it was said.
    refund_reason: RefundReason | None = None
    #: What the provider gave back, once it did.
    refund_given: RefundGiven | None = None
    #: The real fee the provider kept when it took the share (#548) — said on
    #: the capture, or reported later; ``None`` while it is not yet known.
    fee_taken_grosze: int | None = None
    #: When the hold ends unless it is taken, as the provider said when it
    #: held the share — or when its player confirmed it (ADR-0190's 2026-10-10
    #: amendment). ``None`` where it did not say.
    last_moment: Instant | None = None
    #: When a share held for the booked game was let go untaken — its receipt
    #: *held · released* (#641). ``None`` for every other charge: one taken,
    #: or a hold released because the game did not book on it.
    released_at: Instant | None = None
    #: **A Cover** (#751; ``docs/adr/0202`` §6): a friends game's sender's hold
    #: for a seat that isn't theirs — the payer is ``player_id``. Held, taken
    #: and let go by the steps every share uses.
    cover: bool = False
    #: Why a share held for the booked game was let go, once it was — ``None``
    #: on every other charge, and on a let-go recorded without a reason.
    let_go_because: RefundReason | None = None
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
        cover: bool = False,
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
            cover=cover,
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
        cover: bool = False,
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
            cover=cover,
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
            cover=opening.cover,
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
    def fee_kept_grosze(self) -> int | None:
        """Exactly the fee kept on this payment, never more than the share —
        *1,76 zł* on a 40 zł share paid by a business card. ``None`` while it
        is not yet known, and on a share not taken (#641)."""

        if self.status not in PAID or self.fee_taken_grosze is None:
            return None
        return min(self.fee_taken_grosze, self.amount_grosze)

    @property
    def less_the_fee_kept_grosze(self) -> int | None:
        """This share less **exactly the fee kept on this payment** — what a
        leaver after the cut-off gets back if somebody takes their seat
        (Q113): *38,24 zł* of a 40 zł share a business card kept 1,76 zł on.
        ``None`` wherever ``fee_kept_grosze`` is."""

        fee = self.fee_kept_grosze
        return None if fee is None else self.amount_grosze - fee

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
        return self.less_the_fee_kept_grosze

    @property
    def given_back_grosze(self) -> int | None:
        """What this share gives back (#547): what the provider gave, once it
        has answered — until then what was decided, the share or the share
        less the fee kept on it — and nought with no refund decided. ``None``
        while a refund less the fee waits for a fee not yet known (#641)."""

        if self.refund_given is not None:
            return self.refund_given.amount_grosze
        if self.refund_withholds_fee is None:
            return 0
        if not self.refund_withholds_fee:
            return self.amount_grosze
        return self.less_the_fee_kept_grosze

    @property
    def card_fee_grosze(self) -> int | None:
        """The card fee the club pays on this share (#548; the mechanics
        §16.11) — the provider's own figure, said on the capture, reported
        later or kept back by a refund; nought on a share nobody paid, and
        ``None`` while it is not yet known (#641). A refund never returns
        it."""

        if self.status not in PAID:
            return 0
        if self.fee_taken_grosze is not None:
            return self.fee_taken_grosze
        if self.refund_given is not None and self.refund_given.fee_withheld_grosze:
            return self.refund_given.fee_withheld_grosze
        return None

    @property
    def net_grosze(self) -> int | None:
        """What is the club's of this share (#548): what was paid, less what
        was given back, less the card fee — below nought on a share given back
        whole, whose fee the club bears; nought on a share nobody paid; and
        ``None`` while the fee, or a refund less it, is not yet known."""

        if self.status not in PAID:
            return 0
        given_back, fee = self.given_back_grosze, self.card_fee_grosze
        if given_back is None or fee is None:
            return None
        return self.amount_grosze - given_back - fee

    @property
    def settled(self) -> bool:
        """Nothing about this share's money is still on its way (#548): no
        share held to be taken (#637) or checked to be held (#639), no capture
        still to make, no refund
        decided and not yet given — and no fee kept on a share taken still to
        be told (#641), so what is the club's is known. A share let go is
        settled."""

        return (
            self.status
            not in (
                SeatChargeStatus.CHECKED,
                SeatChargeStatus.HELD,
                SeatChargeStatus.TAKING,
            )
            and not self.owes_a_refund
            and self.net_grosze is not None
        )

    @property
    def awaits_its_player(self) -> bool:
        """Refused, with a payment the player can confirm in the app."""

        return self.status is SeatChargeStatus.FAILED and self.payment_id is not None

    @property
    def refused_at_its_holding(self) -> bool:
        """Checked at the fill and refused at its Holding time (#639): the
        booked game's, whose player has their time to fix the card — let go
        with the game (``let_go``), never as an undecided hold."""

        return self.status is SeatChargeStatus.FAILED and self.booking_id is not None

    @property
    def to_fix(self) -> bool:
        """Refused at its Holding time, and not yet kept again — whether or not
        its player confirmed it (#639): the booked game's to keep or let go."""

        return self.booking_id is not None and self.status in (
            SeatChargeStatus.AUTHORISED,
            SeatChargeStatus.FAILED,
        )

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

    def keep(
        self, *, booking_id: UUID, until: Instant, at: Instant, fixed: bool = False
    ) -> None:
        """The game booked on this hold before its club's cut-off: it is kept
        for the game and taken at ``until`` (#637) — or, ``fixed``, a share
        refused at its Holding time that its player confirmed in time (#639)."""

        invariant(self.held_now, f"keeping {self.charge_id}, {self.status}")
        self._record_that(
            SeatChargeKept(
                charge_id=self.charge_id,
                player_id=self.player_id,
                booking_id=booking_id,
                until=until,
                occurred_at=at,
                fixed=fixed,
            )
        )

    def check(
        self, *, booking_id: UUID, until: Instant, hold_at: Instant, at: Instant
    ) -> None:
        """The game booked on this hold before its club's cut-off, ``until``,
        and the hold would not last until it: a **Card check** — let go at once,
        and held again at ``hold_at`` (#639)."""

        invariant(self.held_now, f"checking {self.charge_id}, {self.status}")
        assert self.payment_id is not None
        invariant(hold_at < until, f"{self.charge_id} held at {hold_at}, {until}")
        self._record_that(
            SeatChargeChecked(
                charge_id=self.charge_id,
                player_id=self.player_id,
                booking_id=booking_id,
                payment_id=self.payment_id,
                until=until,
                hold_at=hold_at,
                occurred_at=at,
            )
        )

    def hold_again(self, payment: Payment, *, until: Instant, at: Instant) -> None:
        """The Holding time came and the provider holds the share again on
        ``payment`` — a checked share, or one refused there for want of terms or
        a method, which asked the provider nothing (#639): kept for the game
        and taken at ``until``."""

        invariant(
            self.status is SeatChargeStatus.CHECKED
            or (self.refused_at_its_holding and self.payment_id is None),
            f"holding {self.charge_id} again, {self.status}",
        )
        invariant(
            payment.status is PaymentStatus.AUTHORISED,
            f"a holding the provider answered {payment.status}",
        )
        self._record_that(
            SeatChargeHeldAgain(
                charge_id=self.charge_id,
                player_id=self.player_id,
                payment_id=payment.payment_id,
                until=until,
                occurred_at=at,
                last_moment=payment.last_moment,
            )
        )

    def holding_refused(
        self, reason: FailureReason, *, payment: Payment | None, at: Instant
    ) -> bool:
        """The Holding time came and the share could not be held (#639):
        ``payment`` is the provider's answer, or ``None`` where it was never
        asked. Answers whether anything was recorded — nothing for a share
        refused there already for the same want of terms or a method."""

        asked = reason in (
            FailureReason.AUTHENTICATION_REQUIRED,
            FailureReason.DECLINED,
        )
        invariant(
            asked == (payment is not None),
            f"a {reason} refusal with payment {payment!r}",
        )
        if self.refused_at_its_holding and self.payment_id is None:
            if payment is None and reason is self.failure:
                return False
        else:
            invariant(
                self.status is SeatChargeStatus.CHECKED,
                f"{self.charge_id} refused at its holding while {self.status}",
            )
        self._record_that(
            SeatChargeHoldingRefused(
                charge_id=self.charge_id,
                player_id=self.player_id,
                game_id=self.game_id,
                payment_id=None if payment is None else payment.payment_id,
                amount_grosze=self.amount_grosze,
                reason=reason.value,
                decline_code=None if payment is None else payment.decline_code,
                occurred_at=at,
            )
        )
        return True

    def take_at_the_cut_off(self, *, at: Instant) -> bool:
        """The club's cut-off came: a share held for the booked game is taken
        (#637). Answers whether anything was recorded — nothing for a share
        not held."""

        if self.status is not SeatChargeStatus.HELD:
            return False
        assert self.booking_id is not None
        self.take(booking_id=self.booking_id, at=at)
        return True

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
        nothing for a share held, checked or refused at its Holding time for the
        booked game, which is the game's to let go (``let_go``)."""

        if (
            self.status not in (SeatChargeStatus.AUTHORISED, SeatChargeStatus.FAILED)
            or self.to_fix
        ):
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
        arises (#637). A share only **checked** is closed — nothing is held, so
        nothing is let go — and one refused at its Holding time lets its
        payment go (#639). Answers whether anything was recorded: nothing for a
        share not held for a game."""

        if (
            self.status not in (SeatChargeStatus.HELD, SeatChargeStatus.CHECKED)
            and not self.to_fix
        ):
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
        elif isinstance(event, SeatChargeChecked):
            self.status = SeatChargeStatus.CHECKED
            self.booking_id = event.booking_id
            self.held_until = instant(event.until)
            self.hold_at = instant(event.hold_at)
            # The check's hold is let go: nothing is held until the holding.
            self.last_moment = None
        elif isinstance(event, SeatChargeHeldAgain):
            self.status = SeatChargeStatus.HELD
            self.payment_id = event.payment_id
            self.held_until = instant(event.until)
            self.last_moment = (
                None if event.last_moment is None else instant(event.last_moment)
            )
            self.failure = None
        elif isinstance(event, SeatChargeHoldingRefused):
            self.status = SeatChargeStatus.FAILED
            self.payment_id = event.payment_id
            self.failure = FailureReason(event.reason)
            self.last_moment = None
        elif isinstance(event, SeatChargeTaken):
            self.status = SeatChargeStatus.TAKING
            self.booking_id = event.booking_id
            self.taken_at = instant(event.occurred_at)
        elif isinstance(event, SeatChargeReleased):
            if self.status is SeatChargeStatus.HELD:
                self.released_at = instant(event.occurred_at)
            if event.reason is not None:
                self.let_go_because = RefundReason(event.reason)
            # A checked share holds nothing to let go: it is closed at once.
            self.status = (
                SeatChargeStatus.CANCELLED
                if self.status is SeatChargeStatus.CHECKED
                else SeatChargeStatus.RELEASING
            )
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
            self.refund_reason = (
                None if event.reason is None else RefundReason(event.reason)
            )
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
