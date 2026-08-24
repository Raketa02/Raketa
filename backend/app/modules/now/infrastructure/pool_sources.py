"""``RatedPlayers`` and ``ClubRegulars``: where the cascade's pool comes from.

Two reads that exist only because the cascade asks its question from the
opposite end to everything else on this screen. Now composes *matches for a
player*; the cascade composes *players for a match*, and neither of the two
stores it needs was ever asked that way round.

**Together they are one file for ``StandbyThroughMatches``'s reason**: both
answer *who*, both are read once per dispatch, and both are the reach rather
than the rule — which candidate stands on which rung is ``domain/cascade.py``'s,
and neither of these knows a rung exists.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventStore
from app.kernel import Instant, Sport

from app.modules.matches.domain.ports import MatchRepository
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)


class RatedPlayersFromRatingStreams:
    """Everybody holding a rating at one sport, read off the opening events.

    **The one read in the product that goes against the rating streams' key.**
    A Skill rating's stream id is ``uuid5(player, sport)``, which is what makes
    ``find_for`` and ``exists_for`` one lookup with no index — and it is exactly
    what makes *who holds one* unanswerable from an id. So this asks the store
    the other question it can answer: a stream's **opening event** carries the
    player and the sport as payload, and ``find_aggregate_ids_by_first_event``
    already exists for the mirror-image lookup ``find_all_for`` makes.

    It answers **ids only, and not Levels.** A Level is a stream replay each,
    and the ladder needs one only for a candidate who has survived the cheap
    half of the pool filter — so replaying them here would pay for everybody the
    band is about to refuse.

    **One query and not one per player.** The first draft read the matched
    stream ids and then loaded each stream to find out whose it was, which is an
    N+1 over a sport's whole population on a question that is a single indexed
    read. ``find_first_event_field`` is the port method that fixes it, and it
    exists because a derived stream id cannot be reversed.

    **The remaining cost is stated rather than hidden**: the result still grows
    with the sport's whole population, and ``POOL_LIMIT`` above it is what
    bounds the work rather than this query. That is the same shape
    ``CityMatchesFromMatches`` has and `Raketa02/Raketa#109` already records —
    there is no city to scope by, so *everyone* is the honest answer.
    """

    def __init__(self, events: DomainEventStore) -> None:
        self._events = events

    async def at(self, sport: Sport) -> tuple[UUID, ...]:
        """Every player with a rating at this sport, oldest rating first.

        The order is the store's — *ordered by when the stream opened* — and it
        is kept rather than re-sorted because nothing downstream reads it: the
        ladder sorts the pool by rung and fit, and the only thing an order here
        could do is make a truncation stable, which ``_rungs`` does for itself.
        """

        found = await self._events.find_first_event_field(
            aggregate_type=RATING_AGGREGATE,
            # Both spellings are ``RatingInitialised``'s field names as the
            # codec writes them — the same coupling ``_opening_key`` carries one
            # file over, and it fails the same way: a rename returns nothing,
            # which reads as *nobody plays this sport* rather than as an error.
            payload_equals={"sport": sport.value},
            field="player_id",
        )
        parsed = (_a_player(value) for value in found)
        return tuple(one for one in parsed if one is not None)


def _a_player(value: str) -> UUID | None:
    """A stored payload string as a player id, or nothing.

    ``None`` rather than a raise, on the rule the whole read follows: a payload
    that has drifted from its event class reads as *nobody plays this sport*,
    which is the ordinary answer for a quiet city and the safe direction for a
    background job to fail in.
    """

    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


class ClubRegularsFromMatches:
    """Who has played at one club — **rung 5**, as far as the product can see it.

    ADR-0061 words the rung *"compatible players who use this club often"* and
    ships it as **play history at that club**, which is the only source there is.
    *Often* is deliberately not a threshold: the rung is an **ordering** and not
    a claim, so one past match at the club is what puts somebody on it, and a
    cut-off invented in an adapter would be a number nobody wrote down deciding
    who hears about a seat.

    **A seat held, and not a seat paid.** Somebody who held a seat at that club
    and left still knows the place, which is the whole of what this rung is
    about; counting only the paid ones would be a claim about money in a rung
    about familiarity.
    """

    def __init__(self, matches: MatchRepository) -> None:
        self._matches = matches

    async def at(self, *, club_id: UUID, before: Instant) -> frozenset[UUID]:
        """Everybody who has held a seat at a match at this club, before now.

        ``before`` is the match's *start* rather than its end: a match being
        played this evening is not yet history, and counting it would put the
        people in tonight's other court on the rung for a seat freeing in it.

        One read for the whole club, which is ``for_club``'s own shape. It is
        the widest query a dispatch makes after the rated population, and like
        that one it is bounded by ``POOL_LIMIT`` rather than by itself.
        """

        return frozenset(
            seat.player_id
            for match in await self._matches.for_club(club_id)
            if match.start < before
            for seat in match.seats
            if seat.player_id is not None
        )
