"""What the two ephemeral ledgers promise, over **every** implementation.

One suite, parameterised over the in-memory ledgers the HTTP suite runs against
and the Redis adapters that ship — the idiom ``tests/demands/`` established for
the outward ports, applied inward. A ledger with an implementation nothing runs
the contract against is a ledger whose second implementation is free to mean
something else, and here the two differ in the only way that matters: one holds
Python objects and one holds a hash of strings under a TTL.

**No test here needs Redis running.** The adapters run against
``tests/unit/fake_redis.py``, which models the two semantics they depend on —
expiry against a movable clock, and ``HINCRBY`` creating what it increments —
and nothing else.

The suite is in three parts:

1. **The promises**, over every implementation.
2. **The posture**: an unreachable store degrades ordering and repetition, and
   never excludes anybody or empties a surface.
3. **The shapes**: the keys and TTLs the Redis adapters actually write, which
   only the Redis ones can be asked about.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.matchmaking.domain.ledgers import (
    EPHEMERAL_LEDGERS,
    EXPOSURE_RETENTION_WEEKS,
    LEDGER_FAIL_POSTURE,
    ExposureLedger,
    ExposureWeek,
    SuppressionLedger,
    week_of,
)
from app.modules.matchmaking.domain.ports import FailPosture
from app.modules.matchmaking.infrastructure.fail_soft_ledgers import (
    FailSoftExposureLedger,
    FailSoftSuppressionLedger,
)
from app.modules.matchmaking.infrastructure.redis_ledgers import (
    RedisExposureLedger,
    RedisSuppressionLedger,
    busy_threshold_key,
    exposure_key,
    suppression_key,
)
from tests.unit.fake_ledgers import (
    InMemoryExposureLedger,
    InMemorySuppressionLedger,
    MovableClock,
)
from tests.unit.fake_redis import BrokenRedis, FakeRedis

#: A Wednesday, so a week's arithmetic never lands on a boundary by accident.
NOW = instant(datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc))
WEEK = week_of(NOW)
DAY_SECONDS = 24 * 60 * 60


class Ledgers:
    """One pairing of the two ledgers with the clock they both read."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.clock = MovableClock(NOW)
        if kind == "in-memory":
            self.redis: FakeRedis | None = None
            self.exposure = InMemoryExposureLedger(self.clock)
            self.suppression = InMemorySuppressionLedger(self.clock)
        else:
            self.redis = FakeRedis()
            self.exposure = RedisExposureLedger(self.redis)
            self.suppression = RedisSuppressionLedger(self.redis)

    def advance(self, *, days: float) -> None:
        """Move both clocks together, so *later* means one thing.

        The in-memory ledgers read the injected clock; the Redis ones read the
        server's, which the fake keeps. A test that moved one and not the other
        would be asserting different sentences against the two implementations.
        """

        self.clock.advance(days=days)
        if self.redis is not None:
            self.redis.advance(days * DAY_SECONDS)


@pytest.fixture(params=["in-memory", "redis"])
def ledgers(request) -> Ledgers:
    return Ledgers(request.param)


# ---------------------------------------------------------------------------
# The ports, declared
# ---------------------------------------------------------------------------


def test_both_ledgers_say_how_they_fail():
    assert set(LEDGER_FAIL_POSTURE) == set(EPHEMERAL_LEDGERS)


def test_both_ledgers_fail_soft():
    """The one classification this module exists to get right.

    ``docs/adr/0095``'s *a gate that cannot be evaluated excludes* reads like it
    should reach these two and must not: applying it to a courtesy would empty
    the deck rather than protect anybody.
    """

    assert LEDGER_FAIL_POSTURE[ExposureLedger] is FailPosture.SOFT
    assert LEDGER_FAIL_POSTURE[SuppressionLedger] is FailPosture.SOFT


def test_every_implementation_answers_the_port_it_claims(ledgers):
    assert isinstance(ledgers.exposure, ExposureLedger)
    assert isinstance(ledgers.suppression, SuppressionLedger)


def test_neither_port_can_answer_a_question_about_the_past():
    """Neither ledger is the evidence for anything.

    Structural, because a comment saying so is a comment somebody adds a method
    beside. The exposure ledger offers no way to ask *when* somebody was shown,
    and the suppression ledger offers no way to ask *whether a pass ever
    happened* — both of those are durable rows elsewhere (``docs/adr/0104``,
    ``docs/adr/0128``), and a shape here that could answer either is how a TTL
    quietly becomes a system of record.
    """

    exposure_methods = {
        name for name in dir(ExposureLedger) if not name.startswith("_")
    }
    suppression_methods = {
        name for name in dir(SuppressionLedger) if not name.startswith("_")
    }

    assert exposure_methods == {
        "record_shown",
        "times_shown",
        # The absorption tally is a second **count**, not a second question: it
        # answers *how often*, in this week's bucket, exactly as the appearance
        # count does. Nothing here can say when somebody was volunteered, or to
        # whom, and both of those are on the durable search row.
        "record_shown_to_a_newcomer",
        "times_shown_to_a_newcomer",
        "all_times_shown",
        "publish_busy_threshold",
        "busy_threshold",
    }
    assert suppression_methods == {"suppress", "suppressed_for"}


# ---------------------------------------------------------------------------
# Exposure
# ---------------------------------------------------------------------------


async def test_a_player_nobody_has_seen_is_a_measured_zero(ledgers):
    """Absence is answered, never omitted.

    A caller asking about five candidates gets five answers, so it can never
    read *not in the mapping* as *the store had nothing to say* — the reading
    that would let an outage look like a pool of newcomers.
    """

    ids = [uuid4() for _ in range(3)]

    counts = await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=ids
    )

    assert counts == {player_id: 0 for player_id in ids}


async def test_appearances_add_up(ledgers):
    shown = uuid4()
    other = uuid4()

    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown, other]
    )
    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown]
    )

    counts = await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown, other]
    )

    assert counts == {shown: 2, other: 1}


async def test_one_player_named_twice_in_a_write_is_counted_twice(ledgers):
    """A collection, not a set: one player can appear in two answers at once."""

    shown = uuid4()

    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown, shown]
    )

    counts = await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown]
    )

    assert counts[shown] == 2


async def test_recording_nobody_is_a_legal_no_op(ledgers):
    """A search that returned nobody still finished."""

    await ledgers.exposure.record_shown(sport=Sport.PADEL, week=WEEK, player_ids=[])

    assert await ledgers.exposure.all_times_shown(sport=Sport.PADEL, week=WEEK) == {}


async def test_sports_do_not_share_a_bucket(ledgers):
    player = uuid4()

    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[player]
    )

    tennis = await ledgers.exposure.times_shown(
        sport=Sport.TENNIS, week=WEEK, player_ids=[player]
    )

    assert tennis[player] == 0


async def test_weeks_do_not_share_a_bucket(ledgers):
    """The bucket is a function of ``now``; nothing rolls it.

    Which is why the roll job has no bucket to open: last week's key is a
    different key and expires on its own.
    """

    player = uuid4()
    last_week = week_of(instant(NOW - timedelta(weeks=1)))

    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=last_week, player_ids=[player]
    )

    this_week = await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[player]
    )

    assert this_week[player] == 0


async def test_a_bucket_is_gone_once_it_ages_past_retention(ledgers):
    """Three weeks, and losing it costs nobody a fact."""

    player = uuid4()
    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[player]
    )

    ledgers.advance(days=7 * EXPOSURE_RETENTION_WEEKS + 1)

    counts = await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[player]
    )

    assert counts[player] == 0


async def test_the_roll_reads_the_whole_bucket(ledgers):
    """``all_times_shown`` is the roll's input: every player, one count each."""

    first, second = uuid4(), uuid4()
    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[first, second, second]
    )

    assert await ledgers.exposure.all_times_shown(sport=Sport.PADEL, week=WEEK) == {
        first: 1,
        second: 2,
    }


async def test_no_roll_has_published_a_threshold_yet(ledgers):
    assert await ledgers.exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) is None


async def test_the_threshold_is_read_back_as_it_was_published(ledgers):
    await ledgers.exposure.publish_busy_threshold(
        sport=Sport.PADEL, week=WEEK, threshold=8
    )

    assert await ledgers.exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) == 8


async def test_republishing_the_threshold_replaces_it(ledgers):
    """The roll runs N times per interval; the last one to write wins, cleanly."""

    await ledgers.exposure.publish_busy_threshold(
        sport=Sport.PADEL, week=WEEK, threshold=8
    )
    await ledgers.exposure.publish_busy_threshold(
        sport=Sport.PADEL, week=WEEK, threshold=9
    )

    assert await ledgers.exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) == 9


# ---------------------------------------------------------------------------
# The absorption tally — the second field family in the same bucket
# ---------------------------------------------------------------------------


async def test_the_absorption_tally_starts_at_a_measured_zero(ledgers):
    """Nobody has been volunteered to anybody, and the answer says so per id."""

    volunteered = uuid4()

    assert await ledgers.exposure.times_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    ) == {volunteered: 0}


async def test_the_two_counts_are_separate_and_neither_reads_the_other(ledgers):
    """One bucket, two families, and a search that is not a newcomer's adds to
    exactly one of them.

    This is what makes the cap's own falsifier answerable: *appearances* and
    *appearances in a newcomer's list* are different denominators, and a tally
    that moved with every search would be the first count under a second name.
    """

    volunteered = uuid4()

    await ledgers.exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered, volunteered]
    )
    await ledgers.exposure.record_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    )

    assert await ledgers.exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    ) == {volunteered: 2}
    assert await ledgers.exposure.times_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    ) == {volunteered: 1}


async def test_the_roll_counts_appearances_and_never_the_tally(ledgers):
    """``all_times_shown`` is the roll's input, and the roll's percentile is over
    *how often people were shown* — a bucket that handed it both families would
    count half the population twice and move the busy threshold with it."""

    volunteered = uuid4()

    await ledgers.exposure.record_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    )

    assert await ledgers.exposure.all_times_shown(sport=Sport.PADEL, week=WEEK) == {}


async def test_the_tally_expires_with_the_appearances_beside_it(ledgers):
    """One bucket, one expiry. A tally that outlived its week would bind a cap
    on absorption nobody can look up."""

    volunteered = uuid4()
    await ledgers.exposure.record_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    )

    ledgers.advance(days=EXPOSURE_RETENTION_WEEKS * 7 + 1)

    assert await ledgers.exposure.times_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[volunteered]
    ) == {volunteered: 0}


# ---------------------------------------------------------------------------
# Suppression
# ---------------------------------------------------------------------------


async def test_nothing_is_suppressed_to_begin_with(ledgers):
    passer, candidate = uuid4(), uuid4()

    assert (
        await ledgers.suppression.suppressed_for(
            passer_id=passer, candidate_ids=[candidate]
        )
        == frozenset()
    )


async def test_a_pass_keeps_them_out_of_the_deck(ledgers):
    passer, passed, other = uuid4(), uuid4(), uuid4()

    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    assert await ledgers.suppression.suppressed_for(
        passer_id=passer, candidate_ids=[passed, other]
    ) == frozenset({passed})


async def test_a_suppression_lapses(ledgers):
    """Thirty days, and then it is simply gone.

    The row saying the pass happened is kept elsewhere and is durable — that is
    the whole of *the gate is the cache, the evidence is the row*.
    """

    passer, passed = uuid4(), uuid4()
    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    ledgers.advance(days=31)

    assert (
        await ledgers.suppression.suppressed_for(
            passer_id=passer, candidate_ids=[passed]
        )
        == frozenset()
    )


async def test_a_suppression_is_still_live_the_day_before_it_lapses(ledgers):
    passer, passed = uuid4(), uuid4()
    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    ledgers.advance(days=29)

    assert await ledgers.suppression.suppressed_for(
        passer_id=passer, candidate_ids=[passed]
    ) == frozenset({passed})


async def test_a_pass_reaches_only_the_passers_own_deck(ledgers):
    """One-directional (``docs/adr/0128``): my pass costs the other person nothing.

    They can still be dealt me tomorrow — and the port has no shape that could
    say otherwise, which is what keeps the boundary from depending on a caller
    remembering it.
    """

    passer, passed = uuid4(), uuid4()
    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    assert (
        await ledgers.suppression.suppressed_for(
            passer_id=passed, candidate_ids=[passer]
        )
        == frozenset()
    )


async def test_passing_again_after_a_lapse_starts_a_new_window(ledgers):
    """A second pass means nothing *more* — it means the same thing, again.

    Nothing counts passes, so nothing can grow a penalty out of them. Where
    repetition leads is a Block.
    """

    passer, passed = uuid4(), uuid4()
    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)
    ledgers.advance(days=31)
    await ledgers.suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    ledgers.advance(days=29)

    assert await ledgers.suppression.suppressed_for(
        passer_id=passer, candidate_ids=[passed]
    ) == frozenset({passed})


# ---------------------------------------------------------------------------
# The posture: an outage degrades ordering and repetition, and nothing else
# ---------------------------------------------------------------------------


def _unreachable() -> tuple[FailSoftExposureLedger, FailSoftSuppressionLedger]:
    broken = BrokenRedis()
    return (
        FailSoftExposureLedger(RedisExposureLedger(broken)),
        FailSoftSuppressionLedger(RedisSuppressionLedger(broken)),
    )


async def test_an_outage_never_empties_a_deck():
    """The sentence this whole posture exists for.

    Applying *a gate that cannot be evaluated excludes* here would suppress
    everybody, which empties the deck rather than protecting anybody.
    """

    _, suppression = _unreachable()
    candidates = [uuid4() for _ in range(5)]

    assert (
        await suppression.suppressed_for(passer_id=uuid4(), candidate_ids=candidates)
        == frozenset()
    )


async def test_an_outage_never_excludes_anybody_from_a_shortlist():
    exposure, _ = _unreachable()
    candidates = [uuid4() for _ in range(5)]

    counts = await exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=candidates
    )

    assert counts == {candidate: 0 for candidate in candidates}


async def test_an_outage_costs_the_spread_and_says_nothing_else():
    exposure, _ = _unreachable()

    assert await exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) is None
    assert await exposure.all_times_shown(sport=Sport.PADEL, week=WEEK) == {}


async def test_an_outage_on_the_write_path_never_fails_the_thing_that_wrote():
    """A search that could not be recorded in the ledger is still a search.

    The record that matters is the durable search row, and it is written
    somewhere else. Losing the exposure write costs next week's spread.
    """

    exposure, suppression = _unreachable()

    await exposure.record_shown(sport=Sport.PADEL, week=WEEK, player_ids=[uuid4()])
    await exposure.publish_busy_threshold(sport=Sport.PADEL, week=WEEK, threshold=8)
    await suppression.suppress(passer_id=uuid4(), passed_id=uuid4(), for_days=30)


async def test_a_working_ledger_is_unchanged_by_the_wrapper():
    """Fail-soft adds a posture, never a behaviour."""

    clock = MovableClock(NOW)
    exposure = FailSoftExposureLedger(InMemoryExposureLedger(clock))
    player = uuid4()

    await exposure.record_shown(sport=Sport.PADEL, week=WEEK, player_ids=[player])
    counts = await exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[player]
    )

    assert counts[player] == 1


# ---------------------------------------------------------------------------
# The shapes only the Redis adapters have
# ---------------------------------------------------------------------------


def test_the_keys_are_the_ones_the_spec_names():
    """``expo:{sport}:{week}`` and ``suppress:{from}:{to}``.

    Written down as an assertion because a key shape is the one part of a cache
    nothing else can check: a renamed key is not an error, it is a ledger that
    is permanently empty and looks exactly like a quiet week.
    """

    passer, passed = uuid4(), uuid4()

    assert exposure_key(Sport.PADEL, ExposureWeek(2026, 35)) == "expo:PADEL:2026-W35"
    # The percentile in the threshold's key is read off the constant, so moving
    # the quantile moves the key rather than leaving it serving the old fact.
    assert (
        busy_threshold_key(Sport.PADEL, ExposureWeek(2026, 35))
        == "expo:p90:PADEL:2026-W35"
    )
    assert suppression_key(passer, passed) == f"suppress:{passer}:{passed}"


async def test_a_week_of_exposure_is_one_key():
    """One hash per ``(sport, week)``, so one expiry covers the whole week.

    It is also where ``NEWCOMER_ABSORPTION_CAP``'s tally lands when it gets an
    integer — *same shape, same cadence, no second ledger* — as a second field
    family in this hash rather than a key that could expire apart from it.
    """

    redis = FakeRedis()
    exposure = RedisExposureLedger(redis)

    await exposure.record_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[uuid4(), uuid4()]
    )

    assert redis.keys_held() == {exposure_key(Sport.PADEL, WEEK)}

    await exposure.record_shown_to_a_newcomer(
        sport=Sport.PADEL, week=WEEK, player_ids=[uuid4()]
    )

    assert redis.keys_held() == {exposure_key(Sport.PADEL, WEEK)}


async def test_every_written_key_carries_a_ttl():
    """A ledger key with no expiry is a durable row nobody meant to write."""

    redis = FakeRedis()
    exposure = RedisExposureLedger(redis)
    suppression = RedisSuppressionLedger(redis)

    await exposure.record_shown(sport=Sport.PADEL, week=WEEK, player_ids=[uuid4()])
    await exposure.publish_busy_threshold(sport=Sport.PADEL, week=WEEK, threshold=8)
    await suppression.suppress(passer_id=uuid4(), passed_id=uuid4(), for_days=30)

    assert redis.keys_held()
    for key in redis.keys_held():
        assert redis.ttl_of(key) is not None, key


async def test_the_exposure_ttl_is_retention_and_not_a_week():
    redis = FakeRedis()
    exposure = RedisExposureLedger(redis)

    await exposure.record_shown(sport=Sport.PADEL, week=WEEK, player_ids=[uuid4()])

    expected = EXPOSURE_RETENTION_WEEKS * 7 * DAY_SECONDS
    assert redis.ttl_of(exposure_key(Sport.PADEL, WEEK)) == expected


async def test_the_suppression_ttl_is_the_days_it_was_given():
    redis = FakeRedis()
    suppression = RedisSuppressionLedger(redis)
    passer, passed = uuid4(), uuid4()

    await suppression.suppress(passer_id=passer, passed_id=passed, for_days=30)

    assert redis.ttl_of(suppression_key(passer, passed)) == 30 * DAY_SECONDS
