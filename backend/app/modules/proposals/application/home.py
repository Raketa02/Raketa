"""**Home**: the reader's games from the moment they fill, each with its status
and money line, and how many of them need the reader (#542; the mechanics §3,
§14.1; the screens A8).

**A read, recorded nowhere, and the clock is read once.** Every status, money
line and *needs you* here is folded against one instant (``domain/home.py``), and
that instant travels back as ``read_at`` — so a card's *free to leave until* and
its status cannot be read against two clocks.

**Set reads, never one per card**: the reader's bookings, then each game's
result in one question about the set, the clubs' names in one, and the people on
every card in one per sport — a person's Level is per sport, and a card draws it.

**Home sends what Home draws, and reads no more** (#613): the bookings are read
only from the earliest hour a game can still ask anything of its players
(``on_home_since``), and of those a card is sent only while it is live, ended
less than a day after its hour, or needs the reader (``on_home``) — so how many
are folded no longer grows with every game played. **A score put on the table
again reaches further back**: a correction re-dates its side's score and may be
made again while the other side has not answered, so an older game is still
read when the Games context says a score may still wait on it
(``GameResults.waiting_among``) — asked about ids alone, and folded only for
the few it names. Every card that needs the reader is sent, so the badge counts
what it counted before.

**The games that need the reader** are the cards that need them and, beside
them, every payment they have to confirm — a game still filling, which is not on
Home, but which the mechanics count among the games that need you (§3): its seat
is the reader's only until somebody else takes it.

**Classic play's games are not here**: a game a challenge's line-up opened has
no booking. Its card is ``GET /games``'.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.proposals.application.booked_people import people_on
from app.modules.proposals.application.payments_to_confirm import owed_by
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedState,
    on_home,
    on_home_since,
    state_of,
)
from app.modules.proposals.domain.ports import (
    ClubNames,
    DeckPeople,
    DeckPerson,
    GameResults,
    PlayerBookings,
    ProposalDirectory,
    ProposalRepository,
)


@final
@dataclass(frozen=True, slots=True)
class HomeGame:
    """One card on Home."""

    game: BookedGame
    state: BookedState
    #: ``None`` for a club that no longer exists, with the card kept.
    club_name: str | None


@final
@dataclass(frozen=True, slots=True)
class Home:
    #: The instant every status and money line was folded against.
    read_at: Instant
    #: Soonest game first.
    games: tuple[HomeGame, ...]
    #: The cards that need the reader, and their payments to confirm.
    needing_you: int
    #: Everybody on every card, each in the sport of the card they are on.
    people: Mapping[tuple[Sport, UUID], DeckPerson]


@final
class ReadHome:
    def __init__(
        self,
        *,
        bookings: PlayerBookings,
        results: GameResults,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        people: DeckPeople,
        clubs: ClubNames,
        clock: Clock,
    ) -> None:
        self._bookings = bookings
        self._results = results
        self._proposals = proposals
        self._directory = directory
        self._people = people
        self._clubs = clubs
        self._clock = clock

    async def execute(self, reader: UUID) -> Home:
        now = instant(self._clock.now())
        since = on_home_since(now)
        booked = [
            *await self._older_still_waiting(since, reader=reader, now=now),
            *await self._bookings.of_player(reader, since=since),
        ]
        # A game still waiting for its club, or never booked by it, has none.
        results = await self._results.of(
            [game.game_id for game in booked if game.game_id is not None],
            reader=reader,
            now=now,
        )
        names = await self._clubs.names_of({game.club_id for game in booked})
        cards = [
            card
            for card in (
                HomeGame(
                    game=game,
                    state=state_of(
                        game,
                        None if game.game_id is None else results.get(game.game_id),
                        now=now,
                    ),
                    club_name=names.get(game.club_id),
                )
                for game in booked
            )
            if on_home(card.game, card.state, now=now)
        ]
        owed = await owed_by(
            reader, proposals=self._proposals, directory=self._directory, now=now
        )
        return Home(
            read_at=now,
            games=tuple(cards),
            needing_you=sum(card.state.needs_you for card in cards) + len(owed),
            people=await people_on([card.game for card in cards], self._people),
        )

    async def _older_still_waiting(
        self, since: Instant, *, reader: UUID, now: Instant
    ) -> list[BookedGame]:
        """The reader's games whose hour started before ``since`` that a score
        may still wait on — the only older ones that can still ask anything of
        anybody — soonest first, and by id among games at one hour, as every
        one of them starts before the games read from ``since``."""

        older = await self._bookings.games_before(reader, before=since)
        if not older:
            return []
        waiting = await self._results.waiting_among(older, now=now)
        found: list[BookedGame] = []
        for game_id in waiting:
            game = await self._bookings.find(older[game_id])
            if game is not None:
                found.append(game)
        return sorted(found, key=lambda game: (game.start, game.booking_id))
