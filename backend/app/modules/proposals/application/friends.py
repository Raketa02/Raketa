"""The *friend* tag on every face a proposals read draws (``docs/adr/0202`` §2):
the deck's tiles, a game's details, Home's booked games, Fill in and the
result. ``DeckPeople`` knows no reader, so each read marks its reader's friends
on the people it is about to send — **one question for the whole set**, and
only the reader's: nothing a read sends says who else is friends with whom.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TypeVar
from uuid import UUID

from app.kernel import Sport
from app.modules.proposals.domain.ports import DeckPerson, ReaderRelations

K = TypeVar("K", UUID, tuple[Sport, UUID])


async def with_the_readers_friends(
    people: Mapping[K, DeckPerson], *, reader: UUID, relations: ReaderRelations
) -> dict[K, DeckPerson]:
    """``people`` with every friend of the reader's marked. Keyed by the person
    or, on Home and a booked game, by the sport and the person."""

    def person_of(key: K) -> UUID:
        return key[1] if isinstance(key, tuple) else key

    friends = await relations.friends_among(
        reader, {person_of(key) for key in people}
    )
    return {
        key: replace(person, friend=True) if person_of(key) in friends else person
        for key, person in people.items()
    }
