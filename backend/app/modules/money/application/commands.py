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
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, final
from uuid import UUID

from app.kernel import Grosze

from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import Party
from app.modules.money.domain.reference import Reference


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
