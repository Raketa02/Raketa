"""The two loops that notice, and the one thing neither of them does.

**Each raises a question and changes no value.** That is the whole assertion in
both directions: the drift loop finds five searches disagreeing with a
declaration and leaves a prompt rather than rewriting it (``matchmaking-engine.md``
§6.3), and the staleness backstop finds a week months old and offers to refresh
it rather than docking anybody for it (``docs/adr/0120`` struck the dock).

Both are ``PeriodicJob``s, so both have to be **idempotent and safe beside
themselves** before they may be registered at all (``docs/adr/0092``) — asserted
here by running each twice and finding the same ledger.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.application.detect_intent_drift import (
    DRIFT_WINDOW,
    DetectIntentDrift,
)
from app.modules.matchmaking.application.offer_to_refresh_stale_grids import (
    OfferToRefreshStaleGrids,
)
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.prompts import (
    GRID_STALE_AFTER,
    INTENT_DRIFT_SEARCHES,
    Prompt,
)
from app.modules.matchmaking.domain.search_store import SearchModeReading
from app.modules.player_profile.domain.play_intent import PlayIntent
from tests.unit.fake_ledgers import InMemoryPromptLedger, MovableClock
from tests.unit.matchmaking_builders import SPORT, player, row

NOW = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)
ALICE = player(1)


class Clock:
    def now(self) -> datetime:
        return NOW


class Searches:
    """A ``SearchStore`` answering the drift loop's one read and nothing else."""

    def __init__(self, readings: tuple[SearchModeReading, ...]) -> None:
        self.readings = readings
        self.asked: list[tuple[datetime, int]] = []

    async def modes_since(self, *, since, limit):
        self.asked.append((since, limit))
        return tuple(sorted(self.readings, key=lambda r: r.at, reverse=True))[:limit]


class Declarations:
    def __init__(self, intent: PlayIntent | None) -> None:
        self._intent = intent

    async def load(self, *, player_id: UUID, sport: Sport):
        if self._intent is None:
            return None
        return type("Declared", (), {"intent": self._intent})()


class Index:
    """A ``CandidateSource`` holding one partition's rows and no others."""

    def __init__(self, rows) -> None:
        self._rows = rows

    def snapshot(self, partition: Partition) -> CandidateSnapshot:
        return CandidateSnapshot(
            partition=partition,
            rows=self._rows if partition == Partition.for_sport(SPORT) else (),
            snapshot_version=1,
            caught_up_at=NOW,
        )


def searches(mode: SearchMode, how_many: int, *, sport: Sport = SPORT):
    return tuple(
        SearchModeReading(
            searcher_id=ALICE,
            sport=sport,
            mode=mode,
            at=NOW - timedelta(hours=index + 1),
        )
        for index in range(how_many)
    )


def drift(readings, intent: PlayIntent | None = PlayIntent.FOR_FUN):
    prompts = InMemoryPromptLedger(MovableClock(NOW))
    loop = DetectIntentDrift(
        searches=Searches(readings),
        declarations=Declarations(intent),
        prompts=prompts,
        clock=Clock(),
    )
    return loop, prompts


# ---------------------------------------------------------------------------
# Intent drift — it notices, and it declines to act
# ---------------------------------------------------------------------------


async def test_a_run_of_searches_against_a_declaration_raises_a_prompt():
    loop, prompts = drift(searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES))

    report = await loop.execute()

    assert report.prompts_raised == 1
    standing = await prompts.raised_for(player_id=ALICE, sport=SPORT)
    # The prompt carries **the mode their searches keep choosing**, which is the
    # value already in play — never one the loop picked.
    assert standing == {Prompt.UPDATE_PLAY_INTENT: SearchMode.COMPETITIVE.value}


async def test_a_run_one_search_short_is_not_yet_a_pattern():
    loop, prompts = drift(searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES - 1))

    report = await loop.execute()

    assert report.prompts_raised == 0
    assert await prompts.raised_for(player_id=ALICE, sport=SPORT) == {}


async def test_a_run_that_mixes_modes_has_nothing_to_update_to():
    mixed = searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES)
    mixed = (replace(mixed[0], mode=SearchMode.FOR_FUN), *mixed[1:])
    loop, prompts = drift(mixed)

    assert (await loop.execute()).prompts_raised == 0


async def test_no_preference_is_never_drifted_from():
    """A player who declared no preference has said nothing a search can
    contradict."""

    loop, prompts = drift(
        searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES),
        intent=PlayIntent.NO_PREFERENCE,
    )

    assert (await loop.execute()).prompts_raised == 0


async def test_searches_agreeing_with_the_declaration_raise_nothing():
    loop, prompts = drift(
        searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES),
        intent=PlayIntent.COMPETITIVE,
    )

    assert (await loop.execute()).prompts_raised == 0


async def test_a_retracted_declaration_is_not_something_to_ask_about():
    loop, _ = drift(
        searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES), intent=None
    )

    assert (await loop.execute()).prompts_raised == 0


async def test_the_loop_reads_a_window_wider_than_its_own_cadence():
    """A missed tick, or a deploy, must not create a day nobody's drift was
    noticed in."""

    loop, _ = drift(searches(SearchMode.COMPETITIVE, 1))
    store = loop._searches  # noqa: SLF001 — the read is what is under test

    await loop.execute()

    (since, limit) = store.asked[0]
    assert NOW - since == DRIFT_WINDOW
    assert limit > 0, "one tick's work is bounded"


async def test_the_drift_loop_is_safe_beside_itself():
    loop, prompts = drift(searches(SearchMode.COMPETITIVE, INTENT_DRIFT_SEARCHES))

    await loop.execute()
    once = dict(await prompts.raised_for(player_id=ALICE, sport=SPORT))
    await loop.execute()

    assert dict(await prompts.raised_for(player_id=ALICE, sport=SPORT)) == once


# ---------------------------------------------------------------------------
# The availability-staleness backstop — a question, never a dock
# ---------------------------------------------------------------------------


def stale_grids(rows):
    prompts = InMemoryPromptLedger(MovableClock(NOW))
    loop = OfferToRefreshStaleGrids(
        candidates=Index(rows), prompts=prompts, clock=Clock()
    )
    return loop, prompts


async def test_a_week_months_old_is_asked_about():
    old = row(1, profile_created_at=NOW - timedelta(days=400))
    old = replace(old, grid_updated_at=NOW - GRID_STALE_AFTER - timedelta(days=1))
    loop, prompts = stale_grids((old,))

    report = await loop.execute()

    assert report.grids_examined == 1
    assert report.prompts_raised == 1
    # No sport on it: the availability grid is one week, not seven, so the
    # question has no sport to be about.
    assert await prompts.raised_for(player_id=player(1), sport=SPORT) == {
        Prompt.REFRESH_YOUR_TIMES: None
    }


async def test_a_week_inside_the_window_is_left_alone():
    fresh = replace(row(1), grid_updated_at=NOW - GRID_STALE_AFTER + timedelta(days=1))
    loop, prompts = stale_grids((fresh,))

    report = await loop.execute()

    assert report.prompts_raised == 0
    assert await prompts.raised_for(player_id=player(1), sport=SPORT) == {}


async def test_a_player_rated_in_two_sports_is_asked_once():
    """The index is keyed ``(player, sport)`` and a week is neither."""

    old_at = NOW - GRID_STALE_AFTER - timedelta(days=1)
    padel = replace(row(1), grid_updated_at=old_at)
    tennis = replace(row(1), sport=Sport.TENNIS.value, grid_updated_at=old_at)
    loop, _ = stale_grids((padel, tennis))

    report = await loop.execute()

    assert report.grids_examined == 1
    assert report.prompts_raised == 1


async def test_the_staleness_loop_is_safe_beside_itself():
    old = replace(row(1), grid_updated_at=NOW - GRID_STALE_AFTER - timedelta(days=1))
    loop, prompts = stale_grids((old,))

    await loop.execute()
    once = dict(await prompts.raised_for(player_id=player(1), sport=SPORT))
    await loop.execute()

    assert dict(await prompts.raised_for(player_id=player(1), sport=SPORT)) == once
