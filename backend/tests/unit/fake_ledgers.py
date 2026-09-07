"""In-memory ledgers, so **no test in this suite needs Redis running.**

That is the acceptance criterion rather than a convenience, and it is the same
one the object store and the photo-review sidecar already meet: the API seam is
an ASGI transport over an in-memory SQLite database, with no sidecar of any
kind. A suite that only passes with a container up is a suite CI cannot be
trusted to run — and for a ledger the cost of getting that wrong is worse than
for a store, because a ledger that is simply absent looks, from the outside,
exactly like one that is working and has nothing to say.

**They model expiry, and they must.** A ledger with no TTL is not this port: a
lapsed suppression and a live one are the whole of what
``suppressed_for`` answers, and the difference between them is the only
behaviour a caller can observe. Both fakes read a `Clock` a test may move, so
*thirty-one days later* is setting a time rather than sleeping.

Shared rather than redefined per test file, for the reason the fake photo
storage is: a second fake is a second opinion about what the port promises, and
the two drift silently.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Collection, Mapping
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.matchmaking.domain.ledgers import (
    EXPOSURE_RETENTION_WEEKS,
    ExposureWeek,
)
from app.modules.matchmaking.domain.prompts import PROMPT_TTL, Prompt


class MovableClock:
    """A clock a test sets rather than waits for.

    Structural rather than a subclass of ``Clock``, which is how every other
    clock in this suite satisfies the port.
    """

    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> Instant:
        return self._at

    def set(self, at: Instant) -> None:
        self._at = at

    def advance(self, *, days: float = 0.0, seconds: float = 0.0) -> None:
        self._at = instant(self._at + timedelta(days=days, seconds=seconds))


class InMemoryExposureLedger:
    """Counts per ``(sport, week)``, expiring exactly as the Redis keys do.

    The expiry is a stamp per bucket refreshed on every write, rather than a
    rule about which weeks are old enough to drop. Those two are not the same
    model — Redis expires a key three weeks after it was last *written*, not
    three weeks after the week it names — and the contract suite runs both
    implementations through the same assertions, so the cheaper model would have
    made one of them fail a promise the other keeps.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._counts: dict[tuple[Sport, ExposureWeek], dict[UUID, int]] = {}
        # The second field family of the same bucket, and it shares that
        # bucket's expiry stamp for the reason the Redis adapter shares its key:
        # a tally that outlived the appearances it counts is a cap binding on a
        # week nobody can look at.
        self._absorbed: dict[tuple[Sport, ExposureWeek], dict[UUID, int]] = {}
        self._thresholds: dict[tuple[Sport, ExposureWeek], int] = {}
        self._expires_at: dict[tuple[str, Sport, ExposureWeek], Instant] = {}

    async def record_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        self._expire()
        if not player_ids:
            return
        bucket = self._counts.setdefault((sport, week), {})
        for player_id in player_ids:
            bucket[player_id] = bucket.get(player_id, 0) + 1
        self._touch("counts", sport, week)

    async def times_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        self._expire()
        bucket = self._counts.get((sport, week), {})
        return {player_id: bucket.get(player_id, 0) for player_id in player_ids}

    async def record_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        self._expire()
        if not player_ids:
            return
        bucket = self._absorbed.setdefault((sport, week), {})
        for player_id in player_ids:
            bucket[player_id] = bucket.get(player_id, 0) + 1
        self._touch("counts", sport, week)

    async def times_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        self._expire()
        bucket = self._absorbed.get((sport, week), {})
        return {player_id: bucket.get(player_id, 0) for player_id in player_ids}

    async def all_times_shown(
        self, *, sport: Sport, week: ExposureWeek
    ) -> Mapping[UUID, int]:
        self._expire()
        return dict(self._counts.get((sport, week), {}))

    async def publish_busy_threshold(
        self, *, sport: Sport, week: ExposureWeek, threshold: int
    ) -> None:
        self._expire()
        self._thresholds[(sport, week)] = threshold
        self._touch("thresholds", sport, week)

    async def busy_threshold(self, *, sport: Sport, week: ExposureWeek) -> int | None:
        self._expire()
        return self._thresholds.get((sport, week))

    def _touch(self, held: str, sport: Sport, week: ExposureWeek) -> None:
        self._expires_at[(held, sport, week)] = instant(
            self._clock.now() + timedelta(weeks=EXPOSURE_RETENTION_WEEKS)
        )

    def _expire(self) -> None:
        """Drop what a TTL would already have dropped.

        Evaluated lazily on every operation rather than by a sweeper, exactly as
        Redis evaluates a TTL: there is no moment at which the fake is *between*
        a key having expired and the fake noticing.
        """

        now = self._clock.now()
        for key in [k for k, at in self._expires_at.items() if at <= now]:
            held, sport, week = key
            del self._expires_at[key]
            if held == "counts":
                self._counts.pop((sport, week), None)
                self._absorbed.pop((sport, week), None)
            else:
                self._thresholds.pop((sport, week), None)


class InMemorySuppressionLedger:
    """One expiry per ordered ``(passer, passed)`` pair, and nothing else.

    Keyed one-directionally on purpose, exactly as the port is: there is nothing
    stored here that could answer *who has passed on me*.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._expires_at: dict[tuple[UUID, UUID], Instant] = {}

    async def suppress(
        self, *, passer_id: UUID, passed_id: UUID, for_days: int
    ) -> None:
        self._expires_at[(passer_id, passed_id)] = instant(
            self._clock.now() + timedelta(days=for_days)
        )

    async def suppressed_for(
        self, *, passer_id: UUID, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        now = self._clock.now()
        return frozenset(
            candidate_id
            for candidate_id in candidate_ids
            if self._expires_at.get((passer_id, candidate_id), now) > now
        )


class InMemoryPromptLedger:
    """Standing questions, with the same shared expiry the hash has.

    One expiry per **player**, refreshed by every raise, because that is what an
    ``EXPIRE`` on a hash does — and a fake whose prompts expired one at a time
    would let a test pass against a behaviour the adapter does not have.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._raised: dict[UUID, dict[tuple[Prompt, Sport | None], str | None]] = {}
        self._expires_at: dict[UUID, Instant] = {}

    async def raise_prompt(
        self,
        *,
        player_id: UUID,
        prompt: Prompt,
        sport: Sport | None = None,
        detail: str | None = None,
    ) -> None:
        self._expire()
        self._raised.setdefault(player_id, {})[(prompt, sport)] = detail
        self._expires_at[player_id] = instant(self._clock.now() + PROMPT_TTL)

    async def raised_for(
        self, *, player_id: UUID, sport: Sport
    ) -> Mapping[Prompt, str | None]:
        self._expire()
        return {
            prompt: detail
            for (prompt, about), detail in self._raised.get(player_id, {}).items()
            if about is None or about is sport
        }

    def _expire(self) -> None:
        now = self._clock.now()
        for player_id in [
            player for player, at in self._expires_at.items() if at <= now
        ]:
            del self._expires_at[player_id]
            self._raised.pop(player_id, None)
