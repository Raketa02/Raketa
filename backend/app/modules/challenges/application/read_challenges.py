"""*What have I been asked, and what have I asked for.*

One read, keyed on the reader and on nothing else. There is no argument here that
could name somebody else, which is what stops this becoming a way to ask about a
stranger's evening — the same shape ``InterestLedger`` takes, and for the same
reason.

**The standing is derived here, once, against one instant.** Folding each
challenge against its own read of the clock would let a list disagree with itself
about which of two seats had just lapsed. So the clock is read once and every
standing is computed against it.

**Ended challenges are in the list, and their standing says so.** A challenge that
lapsed this morning still happened to the person it was sent to, and a list that
quietly dropped it would be the same class of lie as a read-back that got shorter.
There is no filter parameter: a client that wants only the live ones has the
standing on every row.

**It is also the remedy for a refused send.** When a send is refused on the pair
rule the client re-reads this, because an open game of the organiser's was always
theirs to read — so naming the pair here costs nothing the refusal was protecting.

**The handles are read once too, and for a whole list** (``docs/adr/0143`` §7).
Everybody on any of these courts is one question, asked about the union — not one
per seat and not one per challenge. It is the **only** thing this read borrows
about a person: a Level, an area and a photograph are a card's, and a card is
drawn on the detail read alone, where the arrangement is still being decided.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.ports import ChallengeDirectory, PlayerHandles
from app.modules.challenges.domain.standing import Standing


@final
@dataclass(frozen=True, slots=True)
class ReadChallengesCommand:
    """*Show me my challenges.* One person, and it is the person asking."""

    reader_id: UUID


@final
@dataclass(frozen=True, slots=True)
class StandingChallenge:
    """One challenge, what it is right now, the instant that *right now* was, and
    what the people on its court are called.

    The standing travels **beside** the challenge rather than on it, because
    nothing stores one: it is a fold of the seats against a clock, and a field on
    the aggregate would be the status column ``standing.py`` refuses.

    **The moment travels with the row** because every deadline the presentation
    layer renders is read against it, and a renderer that read a second clock
    could print a seat as still open beside a standing that says it lapsed. It is
    ``GameListResponse``'s field for ``GameListResponse``'s reason, one context
    over (``docs/adr/0143`` §7).

    **The handles travel with it for the opposite reason**: they are folded
    against nothing. They are the one thing on a challenge that is not derived
    from the seats and the clock, and they ride here rather than being fetched in
    the presentation layer because a route that awaited anything would be a route
    that could await it once per seat.

    ``handles`` is keyed by player id and a seat may be missing from it — an
    account ``users`` no longer has. That is a ``null`` on the wire and a side on
    the screen, never a dropped seat.

    One type, used by the read and by both answers, because a challenge and its
    standing are one answer whether the caller just changed something or only
    asked.
    """

    challenge: Challenge
    standing: Standing
    read_at: Instant
    handles: Mapping[UUID, str]

    @property
    def ended_at(self) -> Instant | None:
        """When it ended, or ``None`` because it has not
        ([#388](https://github.com/Raketa02/Raketa/issues/388)).

        **A property and not a fourth field**, which is the one place this type
        departs from carrying what it was handed — and the reason is the same one
        that put ``read_at`` on it. The ending instant is a fold of exactly
        ``challenge`` and ``read_at``, both already here, so deriving it makes it
        impossible for a caller to pass one folded against a different instant
        from the ``standing`` beside it. ``standing`` is a field because one
        caller has already folded it: an answer writes, then reads the standing
        its own act produced, and hands it over rather than asking twice.

        **The inbox's shelf life is the whole of its readership.** *An ended
        challenge keeps its row, in place, and it leaves 24 h after the challenge
        ended* — one subtraction, ``read_at − ended_at``, and both ends of it are
        served from this one fold so the client never dates an ending off its own
        clock.

        **So it rides on the four acts as well as on the list**, because this type
        does: an answer, a fill and a withdraw all reply with the court as it now
        stands, and *the reply is the redraw*. A challenge and its standing are one
        answer whether the caller just changed something or only asked, and when it
        ended is part of that answer. The **detail** read is the one that does not
        get it — it is its own schema, and a field with no reader there is a cost.
        """

        return self.challenge.ended_at(self.read_at)

    @classmethod
    def folded(
        cls, challenge: Challenge, *, now: Instant, handles: Mapping[UUID, str]
    ) -> "StandingChallenge":
        return cls(
            challenge=challenge,
            standing=challenge.standing_at(now),
            read_at=now,
            handles=handles,
        )


@final
class ReadChallenges:
    """Every challenge this player holds a seat in, newest first."""

    def __init__(
        self,
        *,
        directory: ChallengeDirectory,
        handles: PlayerHandles,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._handles = handles
        self._clock = clock

    async def execute(
        self, command: ReadChallengesCommand
    ) -> tuple[Instant, tuple[StandingChallenge, ...]]:
        """The instant everything was read at, and the challenges as they stood.

        The instant travels back beside the rows as well as on them, because an
        empty list still has to say *when*: a client's countdowns are folded
        against it and there would otherwise be no row to read it off.

        **One handle read for the whole list**, over the union of the courts: a
        player who holds a seat in three of your challenges is asked about once,
        however many challenges there are. A list of none still asks — about
        nobody, which the adapter answers without a round trip.

        **The union is sorted on the way out**, because a set is never the source
        of a traversal (``docs/adr/0105`` §1). Nothing downstream could observe
        the order — the answer is a mapping keyed by id — and the rule is stated
        on the collection rather than on what happens to be observable, because
        that is what changes silently.
        """

        now = instant(self._clock.now())
        found = await self._directory.seating(command.reader_id)
        handles = await self._handles.handles_of(
            sorted(
                {
                    seat.player_id
                    for challenge in found
                    for seat in challenge.seats
                    if seat.player_id is not None
                }
            )
        )
        return now, tuple(
            StandingChallenge.folded(challenge, now=now, handles=handles)
            for challenge in found
        )
