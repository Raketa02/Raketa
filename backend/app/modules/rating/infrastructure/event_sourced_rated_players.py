"""``RatedPlayerQuery`` over the rating streams.

**Addressed, never searched.** A rating's stream id is derived from
``(player, sport)``, so reading a batch's figures is one ``load_stream`` per pair
rather than a query with a predicate — and a player who has never been rated in
that sport is a stream that does not exist, which is the same answer as *absent
from the reply* with nothing to translate. *Whether* they are rated needs no
figure, so ``rated_in`` asks the store once which of every pair's streams exist,
and replays none of them; and a row of people in every sport, ``ratings_of_each``,
loads every pair's stream in one addressed batch and replays each (#814).

**It replays and remembers nothing.** No version is recorded, so an aggregate
that came out of here cannot be saved through the repository beside it: the
narrowness is the point of the port, and this is where it is real rather than
promised.

**Both reads walk their subject in a declared order** — the batch over sorted
ids, the per-player read over ``Sport`` itself — and neither *answer* could tell,
because a mapping has no order. What is ordered is the **sequence of stream
loads**, which is what a trace, a lock ordering or a future retry would care
about, and a declared walk costs nothing to keep (``docs/adr/0105``).
"""

from __future__ import annotations

from typing import Collection, Mapping, Sequence, final
from uuid import UUID

from app.application.events.store import StoredDomainEvent
from app.application.ports import DomainEventStore
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.ports import RatedSport
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)


@final
class EventSourcedRatedPlayers:
    """``RatedPlayerQuery`` over ``DomainEventStore``."""

    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def estimates_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, SkillEstimate]:
        found: dict[UUID, SkillEstimate] = {}
        # Sorted, so a batch is replayed in the same order on every process. The
        # answer is a mapping and could not care, but the *reads* are what a
        # future trace or a lock ordering would care about, and a sorted walk
        # costs nothing to keep (``docs/adr/0105``).
        for player_id in sorted(set(player_ids)):
            rating = await self._replayed(player_id, sport)
            if rating is not None:
                found[player_id] = rating.estimate
        return found

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, RatedSport]:
        """Every sport this player holds a rating in, replayed one stream each.

        **Four addressed loads and never a search.** A rating's stream id is
        derived from ``(player, sport)``, so *which sports is this person rated
        in* is answered by asking about each of them: a sport with no stream is a
        sport they hold no rating in, which is the same answer as *absent from
        the mapping* with nothing to translate.

        The walk is over ``Sport`` itself, so a fifth sport added to the registry
        is read here without anybody remembering to widen a list.
        """

        held: dict[Sport, RatedSport] = {}
        for sport in Sport:
            rating = await self._replayed(player_id, sport)
            if rating is None:
                continue
            held[sport] = _published(rating)
        return held

    async def published_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, RatedSport]:
        """A court's published ratings in one sport — the batch walk, sorted, with
        the per-player read's payload. One translation for both reads, so a
        seat and a record sheet cannot print two versions of one stream."""

        found: dict[UUID, RatedSport] = {}
        for player_id in sorted(set(player_ids)):
            rating = await self._replayed(player_id, sport)
            if rating is not None:
                found[player_id] = _published(rating)
        return found

    async def ratings_of_each(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, Mapping[Sport, RatedSport]]:
        """A row of people's published ratings in every sport: every pair's
        stream in **one** addressed load (``load_streams``), each replayed as
        ``_replayed`` replays one, through the one ``_published`` translation.

        The pairs are ``rated_in``'s walk (``_pairs``), so the statement binds
        its ids in one order on every process; and each player's sports are
        filled in ``Sport``'s own order."""

        pairs = _pairs(player_ids)
        if not pairs:
            return {}
        streams = await self._event_store.load_streams(
            aggregate_type=RATING_AGGREGATE, aggregate_ids=list(pairs)
        )
        held: dict[UUID, dict[Sport, RatedSport]] = {}
        for stream_id, (player_id, sport) in pairs.items():
            rating = _folded(streams.get(stream_id, ()))
            if rating is not None:
                held.setdefault(player_id, {})[sport] = _published(rating)
        return held

    async def rated_in(
        self, player_ids: Collection[UUID]
    ) -> Mapping[Sport, frozenset[UUID]]:
        """A list's dots: which of every pair's streams exist, in **one**
        addressed question to the store, and nothing replayed.

        *Rated in that sport* is *that stream exists* — exactly when
        ``_replayed`` answers something other than ``None``, without the load
        and the fold. The pairs are derived in the file's declared walk, sorted
        ids then ``Sport``, so the statement binds its ids in one order on every
        process; and the answer is read back over the pairs asked about, so a
        stream the store named that nobody asked about could not join it.
        """

        pairs = _pairs(player_ids)
        present = await self._event_store.streams_present(
            aggregate_type=RATING_AGGREGATE, aggregate_ids=list(pairs)
        )
        rated: dict[Sport, set[UUID]] = {sport: set() for sport in Sport}
        for stream_id, (player_id, sport) in pairs.items():
            if stream_id in present:
                rated[sport].add(player_id)
        return {sport: frozenset(players) for sport, players in rated.items()}

    async def _replayed(self, player_id: UUID, sport: Sport) -> SkillRating | None:
        """One pair's rating, replayed, or ``None`` where the stream does not exist.

        The whole of *addressed, never searched*, written once: both reads above
        would otherwise each spell how a rating is found, and the first of the two
        to be changed would win for whichever consumer went through it.
        """

        return _folded(
            await self._event_store.load_stream(
                aggregate_type=RATING_AGGREGATE,
                aggregate_id=skill_rating_id(player_id, sport),
            )
        )


def _pairs(player_ids: Collection[UUID]) -> dict[UUID, tuple[UUID, Sport]]:
    """Every pair's stream id for a batch, in the file's declared walk —
    sorted ids, then ``Sport`` — spelled once for every batch read."""

    return {
        skill_rating_id(player_id, sport): (player_id, sport)
        for player_id in sorted(set(player_ids))
        for sport in Sport
    }


def _folded(stored: Sequence[StoredDomainEvent]) -> SkillRating | None:
    """A loaded stream as its rating, or ``None`` where it holds nothing — how
    a rating is found, spelled once for a load and for a batch's."""

    if not stored:
        return None
    return SkillRating.from_history(record.event for record in stored)


def _published(rating: SkillRating) -> RatedSport:
    """The published form of one rating, and the only place it is spelled.

    Both outward reads that answer in figures a screen prints go through here,
    so the record sheet and a game's seat cannot come to two readings of one
    stream — and ``counted_results`` is the aggregate's own count, which is what
    keeps *what this certainty rests on* moving in step with the Level beside it.
    """

    return RatedSport(
        sport=rating.sport,
        mu=rating.mu,
        confidence=rating.confidence,
        range_low=rating.range_low,
        range_high=rating.range_high,
        band_name=rating.band_name,
        counted_results=rating.counted_results,
    )


__all__ = ["EventSourcedRatedPlayers"]
