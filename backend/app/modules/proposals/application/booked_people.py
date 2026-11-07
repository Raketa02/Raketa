"""Everybody on some booked games, as their tiles draw them — what Home and a
booked game's details both read (#542).

**One read per sport**, since a tile carries the person's Level in the game's
sport, and **in the sport's own order**, so the reads run alike on every process
(``docs/adr/0105``).
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import groupby
from uuid import UUID

from app.kernel import Sport
from app.modules.proposals.domain.home import BookedGame
from app.modules.proposals.domain.ports import DeckPeople, DeckPerson


async def people_on(
    games: Sequence[BookedGame], people: DeckPeople
) -> dict[tuple[Sport, UUID], DeckPerson]:
    """Everybody on these games, keyed by the sport of the game they are on."""

    found: dict[tuple[Sport, UUID], DeckPerson] = {}
    by_sport = sorted(games, key=lambda game: list(Sport).index(game.sport))
    for sport, of_the_sport in groupby(by_sport, key=lambda game: game.sport):
        # A friends game draws its invited seats' friends too (#751).
        players = sorted(
            {
                player
                for game in of_the_sport
                for side in game.planned_sides
                for player in side
            }
        )
        for player, person in (await people.people(players, sport=sport)).items():
            found[(sport, player)] = person
    return found
