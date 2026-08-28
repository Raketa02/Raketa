"""The two ledgers, in Redis. **The first Redis in this application.**

Chosen by what it costs to lose (``docs/adr/0093``): these are mutable, shared
across processes, and cheap to lose, so they get TTL-native storage rather than
a table. Everything the platform must be able to say later is a durable row
somewhere else, and the ports say so at length.

**These classes raise.** They are plain adapters and they report what happened;
the fail-soft posture is applied one layer out, in
``fail_soft_ledgers.py``, and the composition root never hands out an unwrapped
one. Two reasons for the split rather than a ``try`` in every method here.
First, an adapter that swallows its own failures cannot be tested — *it
returned nothing* and *it could not reach the server* are the same observation
from outside, which is exactly the confusion this module's ports exist to
prevent. Second, the posture then lives in one place for both ledgers instead of
in eleven method bodies where one can quietly be forgotten.

**The keys are the ones ``matchmaking-engine.md`` §14.1 names**, and they are
asserted in the suite. A renamed key is not an error anybody sees: it is a
ledger that is permanently empty, and a permanently empty exposure ledger looks
exactly like a quiet week.

**One hash per ``(sport, week)``, one field per player.** When
``NEWCOMER_ABSORPTION_CAP`` gets an integer it is counted here too — *same
shape, same cadence, no second ledger* (``the-newcomer-path.md`` §5) — as a
second field family inside this hash rather than a second key, so that one
expiry covers both and neither can be read half-present.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID

from redis.asyncio import Redis

from app.kernel import Sport
from app.modules.matchmaking.domain.exposure_roll import EXPOSURE_BUSY_PERCENTILE
from app.modules.matchmaking.domain.ledgers import (
    EXPOSURE_RETENTION_WEEKS,
    ExposureWeek,
)

SECONDS_PER_DAY = 24 * 60 * 60

#: How long a week's bucket lives. Read off the domain's retention rather than
#: chosen here: the number is a claim about what can still be asked, and this
#: file only knows how to spell it to a server.
EXPOSURE_TTL_SECONDS = EXPOSURE_RETENTION_WEEKS * 7 * SECONDS_PER_DAY


def exposure_key(sport: Sport, week: ExposureWeek) -> str:
    """``expo:{sport}:{week}`` — the week's bucket for one sport."""

    return f"expo:{sport.value}:{week.label}"


def busy_threshold_key(sport: Sport, week: ExposureWeek) -> str:
    """``expo:p90:{sport}:{week}`` — the scalar the roll publishes.

    The percentile is **read off the constant rather than typed into the
    string**, so moving it moves the key with it. That is the behaviour wanted:
    a threshold taken at a different quantile is a different fact, and a key
    that stayed put would go on serving the old one to every search until the
    week rolled.

    A sibling of the bucket rather than a field inside it, because it is written
    by a different writer on a different cadence and read on the request path
    without the bucket: a search asking *what counts as busy* must not pull a
    hash of every player shown this week to find out.
    """

    return f"expo:p{EXPOSURE_BUSY_PERCENTILE}:{sport.value}:{week.label}"


def suppression_key(passer_id: UUID, passed_id: UUID) -> str:
    """``suppress:{from}:{to}`` — **ordered, and the order is the meaning.**

    A pass is one-directional (``docs/adr/0128``), so the pair is not
    normalised: ``suppress:a:b`` and ``suppress:b:a`` are different facts about
    different decks, and a key shape that sorted the two ids would have made
    them one.
    """

    return f"suppress:{passer_id}:{passed_id}"


class RedisExposureLedger:
    """How often each player was shown, as one hash per ``(sport, week)``."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def record_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        if not player_ids:
            # No pipeline, no round trip, and no `EXPIRE` on a key that may not
            # exist. A search that returned nobody has nothing to record, and
            # touching the bucket anyway would extend its life for no reason.
            return

        key = exposure_key(sport, week)
        async with self._client.pipeline(transaction=False) as pipe:
            for player_id in player_ids:
                pipe.hincrby(key, str(player_id), 1)
            # After the increments, so the key exists to be expired. Refreshed
            # on every write rather than set once: retention is *three weeks of
            # exposure*, and a bucket still being written to is not one that has
            # aged out.
            pipe.expire(key, EXPOSURE_TTL_SECONDS)
            await pipe.execute()

    async def times_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        ids = list(player_ids)
        if not ids:
            return {}

        # One `HMGET` for the whole candidate set, so the read costs one round
        # trip however long the set is.
        values = await self._client.hmget(
            exposure_key(sport, week), [str(player_id) for player_id in ids]
        )
        return {
            player_id: _count(value)
            for player_id, value in zip(ids, values, strict=True)
        }

    async def all_times_shown(
        self, *, sport: Sport, week: ExposureWeek
    ) -> Mapping[UUID, int]:
        fields = await self._client.hgetall(exposure_key(sport, week))
        return {UUID(field): _count(value) for field, value in fields.items()}

    async def publish_busy_threshold(
        self, *, sport: Sport, week: ExposureWeek, threshold: int
    ) -> None:
        await self._client.set(
            busy_threshold_key(sport, week),
            threshold,
            ex=EXPOSURE_TTL_SECONDS,
        )

    async def busy_threshold(self, *, sport: Sport, week: ExposureWeek) -> int | None:
        value = await self._client.get(busy_threshold_key(sport, week))
        return None if value is None else int(value)


class RedisSuppressionLedger:
    """One key per ordered pair, and the TTL is the whole of the rule."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def suppress(
        self, *, passer_id: UUID, passed_id: UUID, for_days: int
    ) -> None:
        # The value carries nothing. Everything worth knowing about the pass —
        # that it happened, when, and where the card came from — is the durable
        # pass record; what is stored here is *the key exists*, and a payload
        # would be a second copy of a fact free to disagree with the first.
        await self._client.set(
            suppression_key(passer_id, passed_id),
            "1",
            ex=for_days * SECONDS_PER_DAY,
        )

    async def suppressed_for(
        self, *, passer_id: UUID, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        ids = list(candidate_ids)
        if not ids:
            return frozenset()

        keys = [suppression_key(passer_id, candidate_id) for candidate_id in ids]
        values = await self._client.mget(keys)
        return frozenset(
            candidate_id
            # `strict`: the reply has one slot per key by construction, and a
            # store that answered a different number of them has answered
            # something this cannot interpret rather than something it should
            # guess at.
            for candidate_id, value in zip(ids, values, strict=True)
            if value is not None
        )


def _count(value: str | None) -> int:
    """A missing field is a measured zero — the player was shown no times.

    Distinct from a missing *answer*, which is what an unreachable server
    produces and which never reaches here: the wrapper outside turns that into
    the whole answer being zero, and the ports record why the two collapse.
    """

    return 0 if value is None else int(value)


__all__ = [
    "EXPOSURE_TTL_SECONDS",
    "SECONDS_PER_DAY",
    "RedisExposureLedger",
    "RedisSuppressionLedger",
    "busy_threshold_key",
    "exposure_key",
    "suppression_key",
]
