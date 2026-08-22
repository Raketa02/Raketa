"""The Ledger aggregate — event-sourced, one stream per player.

ADR-0055 asks the question an aggregate's stream key has to answer — *what
invariant does this aggregate protect?* — and answers it: the ledger protects a
**balance**, and a balance is per player. Everything else it can be asked is a
fold over the same movements.

**Nothing here mutates a movement, and there is no method that removes one.** A
wrong movement is corrected by ``compensate``, which appends a *second* movement
under a ``REV-`` reference (ADR-0057). ``tests/unit/test_money_is_append_only.py``
walks this class and reddens on **any** write to ``_recorded`` but the one
``append`` in ``_apply`` that replays a stored event — public or private, because
the realistic edit is a helper rather than a method somebody names ``forget``.
The rule is the whole reason the context exists and a green suite would look
identical afterwards: a prune that drops the oldest movements past a threshold no
fixture reaches passes every behavioural test in the tree.

**Everything derived is derived here and stored nowhere.** ``balance``, ``held``
and Raketa's float are folds (ADR-0056 retires ``held: true`` by name), so there
is nothing for them to drift from. The cost is that reading them means replaying
a stream, which is the trade ADR-0055 took knowingly and ADR-0018's projection
escape hatch is the answer to if it ever stops being tens of rows.

**Erasure is a read-time substitution, and it has to be.** ``pseudonymise``
appends an event; from then on every movement this aggregate hands out names an
opaque id in the player's place. The stored events are untouched — rewriting
them is the one thing an append-only store cannot do, and ADR-0055 forbids it in
the same breath as it asks for the pseudonym. What actually identifies a person
lives in Users and is erased there; what is left here is an opaque id beside a
set of amounts, which is what pseudonymisation means.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.kernel import (
    Grosze,
    Instant,
    add_grosze,
    grosze,
    instant,
    invariant,
    subtract_grosze,
)

from app.modules.money.domain.causes import MovementCause, rule_for
from app.modules.money.domain.errors import (
    DuplicateMovementReference,
    LedgerAlreadyPseudonymised,
    MovementBelongsToAnotherPlayer,
    NothingToCompensate,
)
from app.modules.money.domain.events import MovementRecorded, PlayerPseudonymised
from app.modules.money.domain.ids import ledger_stream_id
from app.modules.money.domain.movement import Movement, SeatRef
from app.modules.money.domain.parties import (
    ClubParty,
    PlayerParty,
    RaketaParty,
    party_from,
    party_id,
    party_kind,
    PartyKind,
)
from app.modules.money.domain.reference import Reference
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Ledger:
    """One player's whole money history, and every number that folds out of it."""

    id: UUID
    player_id: UUID
    pseudonym: UUID | None = None
    version: int = 0
    _recorded: list[Movement] = field(default_factory=list, repr=False, compare=False)
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    # ------------------------------------------------------------------
    # Identity and replay
    # ------------------------------------------------------------------

    @classmethod
    def for_player(cls, player_id: UUID) -> "Ledger":
        """An empty ledger for a player who has never moved any money.

        A player with no movements has **no stream**, which is the ordinary
        state of a new account and never an error — the same rule the rating
        context reads *"this stream does not exist yet"* by.
        """

        return cls(id=ledger_stream_id(player_id), player_id=player_id)

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Ledger":
        ledger = cls.__new__(cls)
        ledger.pseudonym = None
        ledger.version = 0
        ledger._recorded = []
        ledger._events = EventRecorder()
        for event in events:
            ledger._apply(event)
        invariant(
            ledger.version > 0,
            "a ledger replayed from an empty stream. A player who has moved no "
            "money has no stream, and the repository hands back an empty ledger "
            "for her rather than replaying nothing into one with no identity.",
        )
        return ledger

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ------------------------------------------------------------------
    # What a reader sees
    # ------------------------------------------------------------------

    @property
    def subject_id(self) -> UUID:
        """The id every reader of this ledger sees in the player's place."""

        return self.pseudonym if self.pseudonym is not None else self.player_id

    @property
    def is_pseudonymised(self) -> bool:
        return self.pseudonym is not None

    @property
    def movements(self) -> tuple[Movement, ...]:
        """Every movement, oldest first, with the player party as it reads now.

        Before erasure this is exactly what was stored. After it, the player
        party is the pseudonym in every one of them — and nothing else about any
        of them has changed, which is the claim ``pseudonymise`` makes.
        """

        if self.pseudonym is None:
            return tuple(self._recorded)
        return tuple(self._under_pseudonym(movement) for movement in self._recorded)

    def movements_for(self, seat: SeatRef) -> tuple[Movement, ...]:
        """This ledger's movements about one seat, oldest first."""

        return tuple(movement for movement in self.movements if movement.seat == seat)

    def movement_under(self, reference: Reference) -> Movement | None:
        """The movement this ledger filed under a reference, if it holds one."""

        for movement in self.movements:
            if movement.reference == reference:
                return movement
        return None

    # ------------------------------------------------------------------
    # The folds — derived, and stored nowhere
    # ------------------------------------------------------------------

    @property
    def balance(self) -> Grosze:
        """What this player owes Raketa, as zero or a negative number.

        ADR-0058: *one number, one sign, one query*. Only the two causes whose
        rule says so reach it — a collection that failed takes it below zero, and
        clearing a debt brings it back — because every other movement is money
        changing hands in settlement of something that happened at the same
        moment, and leaves what she owes exactly where it was.

        **It may not go above zero**, and nothing here clamps it: a positive
        balance is stored value, which is a regulated product Raketa is not
        buying, and clamping would hide the bug that produced it from the one
        assertion that exists to find it (``invariants.py``).
        """

        total = grosze(0)
        for movement in self.movements:
            if not rule_for(movement.cause).bears_on_balance:
                continue
            if movement.paid_by(self.subject_id):
                total = add_grosze(total, movement.amount)
            else:
                total = subtract_grosze(total, movement.amount)
        return total

    @property
    def is_in_debt(self) -> bool:
        """Whether this player owes anything at all."""

        return self.balance < 0

    def held_for(self, seat: SeatRef) -> Grosze:
        """What Raketa is holding for one seat, exactly as ADR-0056 writes it.

        ``Σ(player→Raketa) − Σ(Raketa→club) − Σ(Raketa→player)``. Three sums over
        positive numbers, because the direction of a movement is its parties and
        never the sign of its amount.

        On an **open** match this is the seat's share from the moment the money
        lands until the match commits and the court is bought — the money
        ``cancelledIncomplete`` gives back whole. On a **private** court it is
        zero from the same instant, because the court was already bought and the
        share passes through on arrival. Same 30 zł, two regimes, one formula.

        It can be **negative**, and that is not a defect: a refund Raketa
        advanced out of its own money on the private path leaves this seat below
        zero until the owner is charged at reconciliation. ADR-0045 names that
        position; this is where it can be read rather than estimated.
        """

        total = grosze(0)
        for movement in self.movements_for(seat):
            if isinstance(movement.payee, RaketaParty):
                total = add_grosze(total, movement.amount)
            elif isinstance(movement.payer, RaketaParty):
                total = subtract_grosze(total, movement.amount)
        return total

    def settled_to_a_club_for(self, seat: SeatRef) -> Grosze:
        """What has reached a club for one seat, from anybody."""

        total = grosze(0)
        for movement in self.movements_for(seat):
            if isinstance(movement.payee, ClubParty):
                total = add_grosze(total, movement.amount)
        return total

    def funded_by_the_player_for(self, seat: SeatRef) -> Grosze:
        """What this player put in for one seat, to Raketa or to a club."""

        total = grosze(0)
        for movement in self.movements_for(seat):
            if movement.paid_by(self.subject_id):
                total = add_grosze(total, movement.amount)
        return total

    @property
    def raketa_float(self) -> Grosze:
        """This ledger's contribution to what Raketa is holding, in total.

        ``Σ in − Σ out`` for the Raketa party, over every seat. The platform's
        whole float is the sum of these across the ledgers — a scan, which is
        what ADR-0055 says the cross-stream reads are.
        """

        total = grosze(0)
        for movement in self.movements:
            if isinstance(movement.payee, RaketaParty):
                total = add_grosze(total, movement.amount)
            elif isinstance(movement.payer, RaketaParty):
                total = subtract_grosze(total, movement.amount)
        return total

    @property
    def seats(self) -> tuple[SeatRef, ...]:
        """Every seat this ledger has moved money about, first mention first."""

        seen: list[SeatRef] = []
        for movement in self.movements:
            if movement.seat is not None and movement.seat not in seen:
                seen.append(movement.seat)
        return tuple(seen)

    # ------------------------------------------------------------------
    # The two things that happen to a ledger
    # ------------------------------------------------------------------

    def record(self, movement: Movement) -> Movement:
        """Append one movement. The only way anything gets onto a ledger.

        Two refusals, and both are about *this* stream rather than about the
        movement, which is why they are here and not in ``Movement`` itself:

        * a movement naming a different player would make a balance the fold of
          whichever half of two streams anybody read;
        * a reference this ledger already holds is the same event arriving
          twice — a duplicate webhook is one of ADR-0057's three ways money gets
          recorded wrongly, and the only one detectable at the door. Refused
          rather than recorded and compensated: a compensation says something
          happened, and nothing did.
        """

        named = movement.player
        if named is not None and named not in (self.player_id, self.subject_id):
            raise MovementBelongsToAnotherPlayer()
        if self.movement_under(movement.reference) is not None:
            raise DuplicateMovementReference(movement.reference.text)

        # A movement arriving for an erased player is written **under the
        # pseudonym**, not under the id it was addressed to. A chargeback does
        # not stop arriving because an account closed, and whatever writes it
        # will be holding the player id it has always held — refusing it would
        # make erasure a thing that breaks the ledger, and storing the id it
        # carried would put the identifier back.
        if self.pseudonym is not None:
            movement = self._under_pseudonym(movement)

        self._record_that(
            MovementRecorded(
                ledger_id=self.id,
                player_id=self.player_id,
                movement_id=movement.id,
                payer_kind=party_kind(movement.payer).value,
                payer_id=party_id(movement.payer),
                payee_kind=party_kind(movement.payee).value,
                payee_id=party_id(movement.payee),
                amount=int(movement.amount),
                seat_match_id=(
                    None if movement.seat is None else movement.seat.match_id
                ),
                seat_index=None if movement.seat is None else movement.seat.index,
                reservation_id=movement.reservation,
                reference=movement.reference.text,
                cause=movement.cause.value,
                occurred_at=movement.occurred_at,
            )
        )
        return movement

    def compensate(
        self,
        *,
        original: Reference,
        movement_id: UUID,
        reference: Reference,
        cause: MovementCause,
        at: Instant,
    ) -> Movement:
        """Correct a movement by reversing it, never by amending it.

        The original stands: nothing is edited and nothing is deleted
        (ADR-0055). What is appended is a **second** movement with the parties
        the other way round, the same amount, and **its own cause** — the reason
        the correction was needed, which is not the reason the original
        happened. ``shareOnline`` compensated by ``claimLapsed`` is the shape
        ADR-0081 names: the money arrived, the seat had gone, and a slow bank
        does not get to silently keep 30 zł.

        The reference must be a ``REV-`` one. That is not decoration — the
        reconciliation reads compensations by kind, and a correction filed under
        ``PAY-`` is one it would count as a payment.
        """

        held = self.movement_under(original)
        if held is None:
            raise NothingToCompensate(original.text)
        if not reference.is_compensation:
            raise NothingToCompensate(reference.text)

        return self.record(
            Movement(
                id=movement_id,
                payer=held.payee,
                payee=held.payer,
                amount=held.amount,
                seat=held.seat,
                reservation=held.reservation,
                reference=reference,
                cause=cause,
                occurred_at=at,
            )
        )

    def pseudonymise(self, *, pseudonym: UUID, at: Instant) -> None:
        """Replace the player behind this ledger, and keep every movement.

        See the module docstring for why this is a substitution on the way out
        rather than a rewrite of what is stored.
        """

        if self.pseudonym is not None:
            raise LedgerAlreadyPseudonymised()
        self._record_that(
            PlayerPseudonymised(
                ledger_id=self.id,
                player_id=self.player_id,
                pseudonym=pseudonym,
                occurred_at=at,
            )
        )

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, MovementRecorded):
            self.id = event.ledger_id
            self.player_id = event.player_id
            self._recorded.append(_rebuild(event))
        elif isinstance(event, PlayerPseudonymised):
            self.id = event.ledger_id
            self.player_id = event.player_id
            self.pseudonym = event.pseudonym
        self.version += 1

    def _under_pseudonym(self, movement: Movement) -> Movement:
        assert self.pseudonym is not None  # only called from `movements`
        real = PlayerParty(self.player_id)
        masked = PlayerParty(self.pseudonym)
        if movement.payer != real and movement.payee != real:
            return movement
        return Movement(
            id=movement.id,
            payer=masked if movement.payer == real else movement.payer,
            payee=masked if movement.payee == real else movement.payee,
            amount=movement.amount,
            seat=movement.seat,
            reservation=movement.reservation,
            reference=movement.reference,
            cause=movement.cause,
            occurred_at=movement.occurred_at,
        )


def _rebuild(event: MovementRecorded) -> Movement:
    """One stored event back into the value it was written from."""

    seat = (
        None
        if event.seat_match_id is None or event.seat_index is None
        else SeatRef(match_id=event.seat_match_id, index=event.seat_index)
    )
    return Movement(
        id=event.movement_id,
        payer=party_from(PartyKind(event.payer_kind), event.payer_id),
        payee=party_from(PartyKind(event.payee_kind), event.payee_id),
        amount=grosze(event.amount),
        seat=seat,
        reservation=event.reservation_id,
        reference=Reference.parse(event.reference),
        cause=MovementCause(event.cause),
        occurred_at=instant(event.occurred_at),
    )
