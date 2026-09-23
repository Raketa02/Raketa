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

**Except the one the reader cleared themselves** (``docs/adr/0173``). A called-off
court is one fact on two of the reader's lists, and the dismissal ADR-0172 §5
recorded on its game — *their act, and nobody else's fact* — clears both: this
read subtracts its reader off the same set ``GET /games`` does, asked of ``games``
about the ``CALLED_OFF`` rows only, since that is the one standing a dismissal is
admitted on. Nobody else's inbox moves, and the row a reader has not cleared keeps
its day like every ending.

**It is also the remedy for a refused send.** When a send is refused on the pair
rule the client re-reads this, because an open game of the organiser's was always
theirs to read — so naming the pair here costs nothing the refusal was protecting.

**The names are read once too, and for a whole list** (``docs/adr/0143`` §7).
Everybody on any of these courts is one question, asked about the union — not one
per seat and not one per challenge. It is the **only** thing this read borrows
about a person: a Level, an area and a photograph are a card's, and a card is
drawn on the detail read alone, where the arrangement is still being decided.

**And the games are read once, for the courts the fold says have been one**
(``docs/adr/0172`` §4). ``game_id`` is the one fact this read lacked — what lets
a Chats row and the leaver's sheet tell a court that has been a game from one
that has not — and it is read from ``games`` rather than recorded, asked about
the been-a-game subset only, so a list with none costs nothing and ``null`` is
the fold's answer rather than the other context's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, final
from uuid import UUID

from app.kernel import Clock, Instant, instant, invariant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.game_of_court import GameOfCourtQuery
from app.modules.challenges.domain.ports import ChallengeDirectory, PlayerNames
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

    **The names travel with it for the opposite reason**: they are folded
    against nothing. They are the one thing on a challenge that is not derived
    from the seats and the clock, and they ride here rather than being fetched in
    the presentation layer because a route that awaited anything would be a route
    that could await it once per seat.

    ``names`` is keyed by player id and a seat may be missing from it — an
    account ``users`` no longer has. That is a ``null`` on the wire and a side on
    the screen, never a dropped seat.

    ``game_id`` is the game this court became, and ``None`` exactly when the
    fold says its line-up never completed (``docs/adr/0172`` §4) — the same id
    through a re-seat and through the ending. It is a field rather than a
    property because it is read from another context, and it rides here for
    the names' reason: the reply is the redraw, and a redraw that could not
    say whether the court has been a game would draw the wrong sheet.

    One type, used by the read and by both answers, because a challenge and its
    standing are one answer whether the caller just changed something or only
    asked.
    """

    challenge: Challenge
    standing: Standing
    read_at: Instant
    names: Mapping[UUID, str]
    game_id: UUID | None

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

    @property
    def ended_by(self) -> UUID | None:
        """Whose act ended it, or ``None`` because it has not ended
        (``docs/adr/0172`` §3) — the same fold's third half, derived here for
        ``ended_at``'s reason: it is a fold of exactly ``challenge`` and
        ``read_at``, so a caller cannot pass one folded against a different
        instant from the standing beside it.
        """

        return self.challenge.ended_by(self.read_at)

    @classmethod
    def folded(
        cls,
        challenge: Challenge,
        *,
        now: Instant,
        names: Mapping[UUID, str],
        games: Mapping[UUID, UUID],
    ) -> "StandingChallenge":
        return cls(
            challenge=challenge,
            standing=challenge.standing_at(now),
            read_at=now,
            names=names,
            game_id=game_of(challenge, games),
        )


def game_of(challenge: Challenge, games: Mapping[UUID, UUID]) -> UUID | None:
    """The game this court became, off the answer ``games`` gave — or ``None``
    because the fold says its line-up never completed.

    **The fold decides whether to ask, and the answer decides nothing about
    that.** A court that has been a game with no game behind it is a broken
    store rather than a state — the opening runs in the acceptance's own
    transaction — and it raises rather than answering ``null``, which would
    make one absence mean two things.
    """

    if not challenge.has_become_a_game():
        return None
    return invariant(
        games.get(challenge.id),
        f"a court that has been a game, with no game behind it: {challenge.id}",
    )


def been_a_game(challenges: Iterable[Challenge]) -> list[UUID]:
    """The ids of the courts the fold says have been a game, sorted — the only
    ones ``games`` is asked about, and never a set's iteration order
    (``docs/adr/0105`` §1)."""

    return sorted(one.id for one in challenges if one.has_become_a_game())


def called_off(rows: Iterable[StandingChallenge]) -> list[UUID]:
    """The ids of the courts the fold says are ``CALLED_OFF``, sorted — the only
    ones ``games`` is asked about a dismissal on, for ``been_a_game``'s reason
    and on its rule: a dismissal is admitted on that standing alone
    (``docs/adr/0172`` §5), so nothing else can be cleared."""

    return sorted(
        row.challenge.id for row in rows if row.standing is Standing.CALLED_OFF
    )


@final
class ReadChallenges:
    """Every challenge this player holds a seat in, newest first."""

    def __init__(
        self,
        *,
        directory: ChallengeDirectory,
        names: PlayerNames,
        court_games: GameOfCourtQuery,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._names = names
        self._court_games = court_games
        self._clock = clock

    async def execute(
        self, command: ReadChallengesCommand
    ) -> tuple[Instant, tuple[StandingChallenge, ...]]:
        """The instant everything was read at, and the challenges as they stood.

        The instant travels back beside the rows as well as on them, because an
        empty list still has to say *when*: a client's countdowns are folded
        against it and there would otherwise be no row to read it off.

        **One name read for the whole list**, over the union of the courts: a
        player who holds a seat in three of your challenges is asked about once,
        however many challenges there are. A list of none still asks — about
        nobody, which the adapter answers without a round trip.

        **The union is sorted on the way out**, because a set is never the source
        of a traversal (``docs/adr/0105`` §1). Nothing downstream could observe
        the order — the answer is a mapping keyed by id — and the rule is stated
        on the collection rather than on what happens to be observable, because
        that is what changes silently.

        **One game read for the whole list too**, over the courts the fold says
        have been a game and no others (``docs/adr/0172`` §4) — **and one more,
        about the reader**, over the rows the fold says are ``CALLED_OFF`` and
        no others: which of them they have cleared (``docs/adr/0173``). The
        subtraction is here and nowhere else, after the fold, because the
        standing decides what to ask about and a dismissal exists on nothing
        but a called-off game.
        """

        now = instant(self._clock.now())
        found = await self._directory.seating(command.reader_id)
        names = await self._names.names_of(
            sorted(
                {
                    seat.player_id
                    for challenge in found
                    for seat in challenge.seats
                    if seat.player_id is not None
                }
            )
        )
        games = await self._court_games.games_of(been_a_game(found))
        rows = tuple(
            StandingChallenge.folded(challenge, now=now, names=names, games=games)
            for challenge in found
        )
        cleared = await self._court_games.dismissed_of(
            called_off(rows), by=command.reader_id
        )
        return now, tuple(row for row in rows if row.challenge.id not in cleared)
