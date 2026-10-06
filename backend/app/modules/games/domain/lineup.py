"""Who is on the court, on which side, and what kind of evening it was.

**The line-up is frozen until somebody leaves it** (``docs/adr/0162``). The
membership is settled the moment the court is booked, and the fill draws the
sides. This context takes the arrangement as it stood at that instant, and
moves it in exactly two ways, both told by ``bookings`` in the transaction of
the act: a seat is **vacated** when its occupant leaves the game (#544), and a
rescue **takes** an open seat (#545). Nothing here moves anybody on its own, and
a result is still about the two sides that played — which is why a result is
refused while a seat is open.

**An open seat is a seat.** It is drawn empty, in its place, so a four with one
seat open is still a four and the court still says which side is short. Dropping
it would publish a three-person doubles game (``docs/adr/0141``), and that
sentence survives: a seat is never dropped, and now it can be open.

**One string per seating on the wire**: the event codec coerces scalars only,
so a tuple of dataclasses comes back out of storage as a list of dicts and the
aggregate would rebuild the shape on every replay.

``GameSide`` is a **second** spelling of A and B in this repository, after
``matchmaking.domain.lineups.Side`` (``challenges`` held a third until #578). The
strings are equal on purpose so the mapping at each seam is identity rather than
a table; what differs is what the word is *about*. The matcher's is a side of a
line-up it is ranking, and this one is **the side that won or lost**.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, final
from uuid import UUID

from app.kernel import invariant

#: What separates the two fields of a seating code. A pipe rather than a colon:
#: nothing else in either field can spell it, and a uuid is full of hyphens.
_FIELD = "|"


@final
class GameSide(str, Enum):
    """Which side of the net. **Two, and the game names one of them.**"""

    A = "A"
    B = "B"

    @property
    def other(self) -> "GameSide":
        """The side across the net. The only thing this context does with a side."""

        return GameSide.B if self is GameSide.A else GameSide.A


@final
class GameKind(str, Enum):
    """Whether this game is evidence about how well anybody plays.

    **Stamped at the plan and never derived at the end.** ADR-0049's fourth
    rejected option is the reason: *a friendly is a thing people choose*, and
    reclassifying a counted game because nobody typed a score hands a player the
    exact evening they said they did not want, and gives one word two meanings —
    what you chose, and what you failed to record.
    """

    COUNTED = "COUNTED"
    FRIENDLY = "FRIENDLY"


@final
@dataclass(frozen=True, slots=True)
class Seating:
    """One position on one side: a person, or — since somebody may leave — an
    **open seat**.

    ``player_id`` is ``None`` exactly when the seat is open. A line-up completes
    before a game is planned, so an open seat never arrives at the plan; it
    arrives by a departure, and it is filled by a re-seat.
    """

    side: GameSide
    player_id: UUID | None

    @property
    def is_open(self) -> bool:
        return self.player_id is None

    def vacated(self) -> "Seating":
        """The same position, with nobody in it."""

        return Seating(side=self.side, player_id=None)

    @property
    def code(self) -> str:
        """``A|<uuid>``, or ``A|`` for an open seat. The durable spelling, and
        the only one."""

        occupant = "" if self.player_id is None else str(self.player_id)
        return f"{self.side.value}{_FIELD}{occupant}"

    @classmethod
    def from_code(cls, code: str) -> "Seating":
        parts = code.split(_FIELD)
        invariant(len(parts) == 2, f"a seating code with {len(parts)} fields: {code!r}")
        side, player_id = parts
        return cls(
            side=GameSide(side),
            player_id=None if player_id == "" else UUID(player_id),
        )


@final
@dataclass(frozen=True, slots=True)
class LineUp:
    """The court, in the order the booking handed it over.

    **Every seat is present, occupied or open, and nobody sits twice**, checked
    here rather than trusted: this is the one place the arrangement crosses out
    of the context that built it, and a court with a side missing would make
    *the opposing side* a question with no answer. A side may be **short** —
    every seat on it open — because that is what a singles court looks like
    when the opponent has left; the result refusal, not this invariant, is what
    keeps a score off it.
    """

    seatings: tuple[Seating, ...]

    def __post_init__(self) -> None:
        players = [
            seating.player_id for seating in self.seatings if seating.player_id
        ]
        invariant(
            len(players) == len(set(players)),
            "a line-up seating somebody twice",
        )
        for side in GameSide:
            invariant(
                any(seating.side is side for seating in self.seatings),
                f"a line-up with no seat on side {side.value}",
            )

    @classmethod
    def of(cls, seatings: Iterable[Seating]) -> "LineUp":
        return cls(seatings=tuple(seatings))

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> "LineUp":
        return cls(seatings=tuple(Seating.from_code(code) for code in codes))

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(seating.code for seating in self.seatings)

    @property
    def players(self) -> frozenset[UUID]:
        """Everybody on the court. **The people who may act**, and nobody else.

        The leaver is not among them: a departure opens their seat, and the
        people who may act on a game are the people on its court *now*.
        """

        return frozenset(
            seating.player_id for seating in self.seatings if seating.player_id
        )

    @property
    def is_complete(self) -> bool:
        """Whether every seat is occupied. **False while anybody has left.**"""

        return all(not seating.is_open for seating in self.seatings)

    def vacated_by(self, player_id: UUID) -> "LineUp":
        """The same court with this person's seat open. They must be on it."""

        invariant(
            self.side_of(player_id) is not None,
            "a departure by somebody who is not on the court",
        )
        return LineUp.of(
            seating.vacated() if seating.player_id == player_id else seating
            for seating in self.seatings
        )

    def seated(self, player_id: UUID, *, side: GameSide) -> "LineUp":
        """The same court with this person in the first open seat on ``side``
        — a booking's rescue (#545). They must not be on it, and the side must
        have a seat open."""

        invariant(
            self.side_of(player_id) is None,
            "a seat taken by somebody already on the court",
        )
        first_open = next(
            (
                index
                for index, seating in enumerate(self.seatings)
                if seating.side is side and seating.is_open
            ),
            None,
        )
        invariant(first_open is not None, f"no seat open on side {side.value}")
        return LineUp.of(
            Seating(side=side, player_id=player_id) if index == first_open else seating
            for index, seating in enumerate(self.seatings)
        )

    def side_of(self, player_id: UUID) -> GameSide | None:
        """Which side this person is on, or ``None`` if they are not on the court."""

        for seating in self.seatings:
            if seating.player_id == player_id:
                return seating.side
        return None

    def players_on(self, side: GameSide) -> frozenset[UUID]:
        return frozenset(
            seating.player_id
            for seating in self.seatings
            if seating.side is side and seating.player_id
        )

    def counterparts_of(self, player_id: UUID) -> frozenset[UUID]:
        """Everybody else on this court — partner and opponents alike.

        **A pair is anybody you were on a court with**: familiarity is a fact
        about two people having played, not about which way round the net they
        stood.
        """

        return self.players - {player_id}
