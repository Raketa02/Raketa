"""A seat: one position on the challenge's court, and how it crosses into storage.

**An empty seat is a seat** (#221). The court is a fixed list of
``2 x seats_per_side(sport)`` positions, each with a side and an occupant or
nothing. Absence would push *which side is short* to a reader that has to count,
and an A-side full with a B-side short is a different court from the reverse —
the next invitee's side is not a free choice.

**A seat carries no standing.** Whether it is waiting, lapsed or open is read off
its answer and the clock, exactly as ``Interest`` reads its own life off dates;
the challenge's standing is then read off the seats (``standing.py``). A seat
past its ``answer_by`` reads as lapsed whether or not any sweep has noticed,
which is what makes the answer to *is this still open* the same at every instant.

**A decline, a lapse and a departure all open the seat, and they are three
different facts.** The occupant stays on the seat with the answer that emptied
it, because *who said no* and *who said nothing* is the whole of the **answers
challenges** strand, and a seat that forgot which one happened could not tell
them apart. *Who left* is the third (``docs/adr/0162``): written on an
**accepted** seat of a court that had become a game, recorded and not yet
scored, and kept apart from the other two for the day something prices it.

**One string per seat on the wire.** The event codec coerces scalars only: a
``tuple[Seat, ...]`` would come back out of storage as a list of dicts and the
aggregate would be rebuilding the shape on every replay. This is
``AvailabilitySlot.code``'s precedent, with more fields in it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import final
from uuid import UUID

from app.kernel import SPORT_SPECS, Instant, Sport, instant, invariant
from app.modules.challenges.domain.origins import (
    ChallengeOrigin,
    origin_from_code,
)

#: What separates the five fields of a seat code. Not a colon and not a comma:
#: an ISO instant is one of the fields and is full of both.
_FIELD = "|"

_FIELDS = 5


@final
class Side(str, Enum):
    """Which side of the net. The organiser is always on ``A``.

    This context's own, and deliberately a second spelling of
    ``matchmaking.domain.lineups.Side``: the matcher's is *the searcher's side of
    a line-up it is ranking*, this one is *a position on a court somebody has
    been asked to sit in*, and ``challenges`` may not import ``matchmaking``.
    The two strings are equal on purpose, so the mapping at the seam is identity
    rather than a table.
    """

    A = "A"
    B = "B"


@final
class SeatAnswer(str, Enum):
    """What the person in this seat did about being asked — or, having said yes,
    about the game.

    Four values and not five: *awaiting* is the absence of an answer, and giving
    it a name would make ``None`` and ``AWAITING`` two spellings of one state
    with nothing to choose between them.

    ``LAPSED`` is recorded by the sweep and is **never** a decline. They do the
    same thing to the line-up and they are different facts: *answers challenges*
    is a Strand over challenges that got an answer inside their window, and it is
    unmeasurable if silence is filed as judgement.

    ``LEFT`` is the one answer written **over** another (``docs/adr/0162``): an
    accepted seat, on a court whose line-up had completed into a game, whose
    occupant has since left it. It opens the seat exactly as the other two do and
    is neither of them — leaving a game you agreed to is not declining an
    invitation, and nothing prices it yet.
    """

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    LAPSED = "LAPSED"
    LEFT = "LEFT"


def seats_per_side(sport: Sport) -> int:
    """How many people sit on one side of this sport's court.

    Read from the closed ``SPORT_SPECS`` registry rather than held here, because
    a second table of *how many play this* is a second place for it to be true —
    and the one that would be believed is whichever the reader opened first.
    """

    spec = invariant(SPORT_SPECS.get(sport), f"no spec for sport: {sport!r}")
    invariant(
        spec.players % 2 == 0,
        f"{sport.value} seats {spec.players} players and has no two sides",
    )
    return spec.players // 2


def court_sides(sport: Sport) -> tuple[Side, ...]:
    """The sport's court as a fixed list of sides: every ``A``, then every ``B``.

    The order is the court's shape and is part of the contract, not a
    convenience: ``ChallengeOpenedFromMutualInterest`` seats its pair in the
    **first two positions**, which puts them one per side in a singles sport and
    both on one side in a doubles one — *a one-to-one padel challenge is half a
    game*, with a whole side still to fill.
    """

    per_side = seats_per_side(sport)
    return (Side.A,) * per_side + (Side.B,) * per_side


@final
@dataclass(frozen=True, slots=True)
class Seat:
    """One position: a side, and either an occupant with their answer or nothing.

    ``answer_by`` is **this seat's own** deadline, dated when this seat was
    invited. A seat filled later starts its own day and cannot inherit a deadline
    from a send it was not part of.

    ``answer_by`` is ``None`` exactly when nobody was asked: an empty seat, the
    organiser's — accepted from birth, because they are the one proposing — and
    both seats of a challenge born from a mutual yes, where the answers were
    already given. A seat that was never asked can still be **left**, so a
    ``LEFT`` seat may carry no deadline either.
    """

    side: Side
    player_id: UUID | None = None
    answer: SeatAnswer | None = None
    answer_by: Instant | None = None
    origin: ChallengeOrigin | None = None

    def __post_init__(self) -> None:
        if self.player_id is None:
            invariant(
                self.answer is None and self.answer_by is None and self.origin is None,
                f"an empty seat carrying an answer, a deadline or an origin: {self!r}",
            )
            return
        invariant(
            self.answer in (SeatAnswer.ACCEPTED, SeatAnswer.LEFT)
            or self.answer_by is not None,
            f"a seated player with no answer and no deadline: {self!r}",
        )
        invariant(
            (self.answer_by is None) == (self.origin is None),
            f"an invitation that cannot say where it came from: {self!r}",
        )

    # -- what this seat is, read off the clock ----------------------------

    def holds(self, player_id: UUID) -> bool:
        """Whether this is that player's seat to answer for."""

        return self.player_id == player_id

    def is_accepted(self) -> bool:
        return self.answer is SeatAnswer.ACCEPTED

    def is_lapsed_at(self, now: Instant) -> bool:
        """Whether the answer window passed with nothing in it.

        True before any sweep has run, which is the point: correctness does not
        depend on a loop running, and the sweep exists to make the lapse a fact
        somebody can count rather than to make this answer right.
        """

        if self.answer is SeatAnswer.LAPSED:
            return True
        return (
            self.is_awaiting() and self.answer_by is not None and now >= self.answer_by
        )

    def is_awaiting(self) -> bool:
        """Whether this seat has been asked and has not answered, deadline aside."""

        return self.player_id is not None and self.answer is None

    def is_awaiting_at(self, now: Instant) -> bool:
        """Whether somebody's answer is still owed **and still wanted**."""

        return self.is_awaiting() and not self.is_lapsed_at(now)

    def is_open_at(self, now: Instant) -> bool:
        """Whether this seat is free for somebody new.

        A declined, lapsed or left seat is open again — which is also what makes
        its former occupant a stranger to everybody else on the court once more.
        """

        if self.player_id is None:
            return True
        return (
            self.answer in (SeatAnswer.DECLINED, SeatAnswer.LEFT)
            or self.is_lapsed_at(now)
        )

    def is_live_at(self, now: Instant) -> bool:
        """Whether somebody is still in this game through this seat."""

        return not self.is_open_at(now)

    # -- transitions, each returning the seat this one becomes ------------

    def answered(self, answer: SeatAnswer) -> "Seat":
        """The same seat, with what its occupant decided about it."""

        return replace(self, answer=answer)

    def on_side(self, side: Side) -> "Seat":
        """The same occupant, the same answer, across the net.

        **An acceptance is to the game, not to the side.** The membership is
        settled; the arrangement is still the organiser's to choose, and moving
        somebody costs their acceptance nothing.
        """

        return replace(self, side=side)

    # -- storage ----------------------------------------------------------

    @property
    def code(self) -> str:
        """The seat as one string, which is how a stream stores it."""

        return _FIELD.join(
            (
                self.side.value,
                "" if self.player_id is None else str(self.player_id),
                "" if self.answer is None else self.answer.value,
                "" if self.answer_by is None else self.answer_by.isoformat(),
                "" if self.origin is None else self.origin.code,
            )
        )

    @classmethod
    def from_code(cls, code: str) -> "Seat":
        """The seat a stored ``code`` names.

        Raises through ``invariant`` rather than returning a refusal, because
        this reads *history*: a code this cannot parse is a corrupt stream or a
        codec that changed under it, and neither is a state a caller can recover
        from by asking anybody again.
        """

        parts = code.split(_FIELD)
        invariant(len(parts) == _FIELDS, f"seat code: {code!r}")
        side, player_id, answer, answer_by, origin = parts
        invariant(side in Side.__members__, f"seat code: {code!r}")
        invariant(
            answer == "" or answer in SeatAnswer.__members__, f"seat code: {code!r}"
        )
        return cls(
            side=Side[side],
            player_id=None if player_id == "" else UUID(player_id),
            answer=None if answer == "" else SeatAnswer[answer],
            answer_by=(
                None if answer_by == "" else instant(datetime.fromisoformat(answer_by))
            ),
            origin=None if origin == "" else origin_from_code(origin),
        )


@final
@dataclass(frozen=True, slots=True)
class SeatPlan:
    """One seat as the organiser built it: a side, and who is to sit there.

    The **arrangement** is a list of these, and it is the only thing about the
    line-up this context records. *Sides only*: the forecast percentage is not
    stored, because it follows from the sides and a stored copy goes stale the
    next time a ruleset ships.

    An invitee arrives with their origin or does not arrive at all — the origin
    has no default here for the same reason it has none on the wire.
    """

    side: Side
    player_id: UUID | None = None
    origin: ChallengeOrigin | None = None

    def __post_init__(self) -> None:
        invariant(
            self.player_id is not None or self.origin is None,
            f"an empty seat carrying an origin: {self!r}",
        )
