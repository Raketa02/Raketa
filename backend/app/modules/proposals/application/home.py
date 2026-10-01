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
from app.modules.proposals.domain.home import BookedGame, BookedState, state_of
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
        booked = await self._bookings.of_player(reader)
        results = await self._results.of(
            [game.game_id for game in booked], reader=reader, now=now
        )
        names = await self._clubs.names_of({game.club_id for game in booked})
        cards = [
            HomeGame(
                game=game,
                state=state_of(game, results.get(game.game_id), now=now),
                club_name=names.get(game.club_id),
            )
            for game in booked
        ]
        owed = await owed_by(
            reader, proposals=self._proposals, directory=self._directory, now=now
        )
        return Home(
            read_at=now,
            games=tuple(cards),
            needing_you=sum(card.state.needs_you for card in cards) + len(owed),
            people=await people_on(booked, self._people),
        )
