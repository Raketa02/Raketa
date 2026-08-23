"""What a caller asks the Money context to do.

**Nothing says when it happened.** The instant of a movement comes from the
``Clock`` port, on the kernel's rule of one read per command. That is right for
everything Money records today, and it is a known gap for one thing it does not:
a payment provider reporting a landing knows the instant the bank posted it, and
that instant is not the instant we heard about it. ADR-0055 puts the provider
and its event mapping **out of this context's scope** by name, so the field it
would need is not being added ahead of the mouth that would fill it (ADR-0071).

**A draft is a union, not a record with optional halves.** A movement written
from nothing and a movement written to correct another one need different
inputs, and a single dataclass covering both would carry four fields that are
meaningless in one of the two cases — and typecheck in both.

**A share's arrival is a union for the same reason**, and it is the shape of
ADR-0056's own table: an open match's money is held, a private court's passes
through to the club, and cash across a counter never touched Raketa at all. The
club a share settles to is a field of the two forms that have one, so *held by
Raketa, settled to club X* is not a state anybody can write.

**A payment's channel is a third union, and it is not the arrival.** What a
caller knows is where the money came through — bought from Raketa, or handed
across a club counter. What it may not decide is **custody**, which follows what
was sold and is therefore the *match's* answer (ADR-0056): an open match's share
is held, a private court's passes through, and no payer or provider can be
allowed a say in that. ``PayForASeat`` is the one place the two are put
together, which is why the arrival above is not a command field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, final
from uuid import UUID

from app.kernel import Grosze, invariant

from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import Party
from app.modules.money.domain.reference import Reference, ReferenceKind


@final
@dataclass(frozen=True)
class NewMovement:
    """Money moving between two parties, for a reason, about a seat."""

    payer: Party
    payee: Party
    amount: Grosze
    cause: MovementCause
    reference: Reference
    seat: SeatRef | None = None
    reservation: UUID | None = None


@final
@dataclass(frozen=True)
class Compensation:
    """A correction: the named movement, reversed, under a ``REV-`` reference.

    It carries no parties, no amount and no seat — all four are read off the
    movement being corrected, so a compensation cannot quietly reverse a
    different amount than the one that was wrong. What it does carry is its own
    **cause**, because the reason a correction was needed is not the reason the
    original happened (ADR-0057).
    """

    original: Reference
    reference: Reference
    cause: MovementCause


#: One of the two things a caller can ask to be appended.
MovementDraft: TypeAlias = NewMovement | Compensation


@final
@dataclass(frozen=True)
class RecordMovementsCommand:
    """Everything one write puts on one player's ledger.

    A tuple rather than a single draft, because ADR-0056 requires an online
    share on a private court to be **two** movements and they must land
    together: a `player → Raketa` with no `Raketa → club` beside it is a float
    that reads wrong until the second half arrives.
    """

    player_id: UUID
    drafts: tuple[MovementDraft, ...]


@final
@dataclass(frozen=True)
class HeldByRaketa:
    """An open match: no court is booked, so the money is Raketa's to hold.

    This is the money ``cancelledIncomplete`` gives back whole, and without it
    the open path has no refund to give (ADR-0056).
    """


@final
@dataclass(frozen=True)
class PassedToTheClub:
    """A private split court: it is already bought, so the share passes through.

    Two movements land together and the second needs a reference of its own —
    it is a separate thing that happened, and the reconciliation reads
    references one movement at a time.
    """

    club_id: UUID
    settlement: Reference


@final
@dataclass(frozen=True)
class PaidAtTheCounter:
    """Cash handed across a club counter, marked paid by the club.

    The one movement that is `player → club` with Raketa as neither party
    (ADR-0059). Available to invited players only — a marketplace seat is always
    bought from Raketa online, because a refundable seat's money must sit
    somewhere we control — and that rule belongs to whoever offers the channel,
    not to the ledger that records it.
    """

    club_id: UUID


#: How a share reached wherever it is. See the module docstring.
ShareArrival: TypeAlias = HeldByRaketa | PassedToTheClub | PaidAtTheCounter


@final
@dataclass(frozen=True)
class RecordShareCommand:
    """One player's share of one court, however it arrived."""

    player_id: UUID
    seat: SeatRef
    amount: Grosze
    reference: Reference
    arrival: ShareArrival
    reservation: UUID | None = None


@final
@dataclass(frozen=True)
class Online:
    """Bought from Raketa. Custody is the match's answer, not this one's.

    ``settlement`` names the ``Raketa → club`` half of a pass-through, and it is
    required rather than optional because a caller cannot know whether it will
    be needed: whether the court was already bought is a fact about the match,
    read after this command was built. A reference is minted by the mouth
    reporting the landing for the same reason the payment's is — it is an
    identifier a support agent reads back to a player and a bank, and one
    derived from the payment's token here would collide with a real payment
    whose token happened to be the derived one.
    """

    settlement: Reference


@final
@dataclass(frozen=True)
class AcrossTheCounter:
    """Cash handed to the club, marked paid by the club (ADR-0059).

    It carries no club: the club is the match's, and a mark naming a different
    one would be a club marking somebody else's court paid. It overrides custody
    rather than being one, because Raketa is never a party — there is no
    position for us to hold or to have passed on.
    """


#: How the money reached whoever is holding it. See the module docstring.
PaymentChannel: TypeAlias = Online | AcrossTheCounter


@final
@dataclass(frozen=True)
class PayForASeatCommand:
    """*This money landed, for this player's seat in this match.*

    **The amount is the caller's and not the match's share.** What is recorded
    is what actually moved; a ledger that wrote down the price instead of the
    payment would be a ledger that cannot be used to settle an argument about
    either. A landing that disagrees with the share is therefore recorded as it
    arrived and left for the reconciliation to find.

    **The reference is the idempotency probe**, the same way it is in the seed
    catalog: a ledger refuses a second movement under one, so a report delivered
    twice is refused by name rather than recorded twice.
    """

    match_id: UUID
    player_id: UUID
    amount: Grosze
    reference: Reference
    channel: PaymentChannel

    def __post_init__(self) -> None:
        # Both references name money **going out of a player's hands**, so both
        # are ``PAY-``. It is not tidiness: the reconciliation reads
        # compensations *by kind*, so a share filed under ``REV-`` would be
        # counted as a correction of something, and `held` and the float would
        # both be wrong in the one place the record is the answer to a dispute
        # (ADR-0057). And a share under ``REV-`` collides with the reversal this
        # would file if the seat had gone, which is the same defect arriving as
        # a duplicate.
        invariant(
            self.reference.kind is ReferenceKind.PAYMENT,
            f"a seat payment filed under {self.reference.text}",
        )
        if isinstance(self.channel, Online):
            invariant(
                self.channel.settlement.kind is ReferenceKind.PAYMENT,
                f"a club settlement filed under {self.channel.settlement.text}",
            )


@final
@dataclass(frozen=True)
class CompensateMovementCommand:
    """Correct one movement on one player's ledger."""

    player_id: UUID
    original: Reference
    reference: Reference
    cause: MovementCause


@final
@dataclass(frozen=True)
class PseudonymisePlayerCommand:
    """Erase the player behind a ledger, and keep every movement on it."""

    player_id: UUID
