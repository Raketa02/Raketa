"""The search record: written whole, read back narrow.

Two claims, and the second is an authorization rule rather than a query
optimisation: **the searcher may read their own ``RETURNED`` rows and nothing
else.** *A player may ask why somebody was shown; nobody may ask who was
withheld* — so the near-miss band has no read path at all, and a stranger's
``search_id`` answers exactly as an unknown one does.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    InclusionReason,
    PoolDescription,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
    WithheldReason,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_search_store import (
    SqlAlchemySearchStore,
)
from app.modules.player_profile.domain.availability import Window

AT = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)
SEARCHER = UUID("11111111-1111-1111-1111-111111111111")
STRANGER = UUID("22222222-2222-2222-2222-222222222222")


def _candidate(band: CandidateBand, position: int) -> SearchCandidateRecord:
    return SearchCandidateRecord(
        band=band,
        position=position,
        player_id=uuid4(),
        fit=72.5,
        terms=({"term": "LEVEL_FIT", "weight": 29.9, "value": 1.0},),
        degraded_terms=("RELIABILITY",),
        modifiers=({"code": "CALIBRATION_VALUE", "points": 4.0},),
        liveness_reasons=("NEWCOMER_LIFT",),
        liveness_signals={"NEWCOMER_LIFT": True, "INTEREST_RECEIVED": None},
        shared_count=2,
        their_slot_count=5,
        days_away=1,
        inclusion_reason=(
            InclusionReason.ZERO_EXPOSURE
            if band is CandidateBand.RETURNED
            else None
        ),
        withheld_reason=(
            None if band is CandidateBand.RETURNED else WithheldReason.BELOW_FLOOR
        ),
        missing_terms=() if band is CandidateBand.RETURNED else ("SOCIAL_VIBE",),
        reliability_penalty_applied=False,
        reliability_penalty_decisive=False,
    )


def _record(searcher_id: UUID = SEARCHER) -> SearchRecord:
    returned = tuple(_candidate(CandidateBand.RETURNED, n) for n in (1, 2))
    near = tuple(_candidate(CandidateBand.NEAR_MISS, n) for n in (1,))
    return SearchRecord(
        id=uuid4(),
        searcher_id=searcher_id,
        sport=Sport.PADEL,
        mode=SearchMode.COMPETITIVE,
        intent_read=None,
        surface=SearchSurface.SHORTLIST,
        initiation=SearchInitiation.HUMAN,
        at=AT,
        engine_version="matchfit-v1",
        ruleset_version="r2026-08-26-a",
        snapshot_version=42,
        trace_id="trace-1",
        index_stale=False,
        counts=StagedCounts(
            n_generated=9,
            excluded_by_gate={"BLOCKED": 1},
            n_scored=8,
            n_cleared_floor=2,
            n_returned=2,
            n_near_miss_recorded=1,
        ),
        best_withheld_fit=41.0,
        pool_description=PoolDescription(
            sport=Sport.PADEL,
            radius_km_used=10,
            players_in_range=8,
            window=Window.THIS_WEEK,
        ),
        searcher_slot_count=4,
        radius_clamp_bit=False,
        latency_ms_by_stage={"pipeline": 3},
        candidates=returned + near,
    )


@pytest.fixture
async def store(session_factory):
    async with session_factory() as session:
        yield SqlAlchemySearchStore(session), session


async def test_a_record_round_trips_through_the_columns_it_is_stored_in(store):
    """The opaque blobs come back as the mappings they were written as — a row
    stamped with a ruleset nobody runs any more must still read."""

    adapter, session = store
    record = _record()

    await adapter.record(record)
    await session.commit()

    rows = await adapter.returned_rows_for(
        search_id=record.id, searcher_id=SEARCHER
    )

    assert [row.position for row in rows] == [1, 2]
    assert rows[0].terms[0]["term"] == "LEVEL_FIT"
    assert rows[0].degraded_terms == ("RELIABILITY",)
    assert rows[0].liveness_signals["INTEREST_RECEIVED"] is None
    assert rows[0].inclusion_reason is InclusionReason.ZERO_EXPOSURE


async def test_the_near_miss_band_is_stored_and_has_no_read_path(store):
    """Layer 3 is engine-internal. It is in the table, and there is no method
    here that could return it — not to the searcher, not to anybody."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    rows = await adapter.returned_rows_for(
        search_id=record.id, searcher_id=SEARCHER
    )

    assert all(row.band is CandidateBand.RETURNED for row in rows)
    assert len(rows) == 2, "the near-miss row came back"
    assert not hasattr(adapter, "near_misses_for")


async def test_a_stranger_reads_nothing_and_cannot_tell_why(store):
    """A search that belongs to somebody else, a search that does not exist and
    a search that returned nobody are **deliberately indistinguishable** — an
    answer that separated them would tell a caller whether a stranger's id is
    real."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    foreign = await adapter.returned_rows_for(
        search_id=record.id, searcher_id=STRANGER
    )
    unknown = await adapter.returned_rows_for(
        search_id=uuid4(), searcher_id=SEARCHER
    )

    assert foreign == () == unknown


async def test_the_store_does_not_commit_for_its_caller(store):
    """The transaction boundary is a decision about the **command**, and here it
    is load-bearing: the record is committed before the response returns, by the
    use case, in the request's own transaction."""

    adapter, session = store
    await adapter.record(_record())

    assert session.in_transaction(), "the store committed on its caller's behalf"


def test_a_returned_row_may_not_carry_a_withheld_reason():
    """The two bands are two different facts, and the type refuses a row that
    claims both."""

    from app.kernel import InvariantViolated

    with pytest.raises(InvariantViolated):
        SearchCandidateRecord(
            band=CandidateBand.RETURNED,
            position=1,
            player_id=uuid4(),
            fit=50.0,
            terms=(),
            degraded_terms=(),
            modifiers=(),
            liveness_reasons=(),
            liveness_signals={},
            shared_count=0,
            their_slot_count=0,
            days_away=None,
            inclusion_reason=None,
            withheld_reason=WithheldReason.BELOW_FLOOR,
            missing_terms=(),
            reliability_penalty_applied=False,
            reliability_penalty_decisive=False,
        )


def test_the_redaction_detector_must_agree_with_the_rows_written():
    """``n_returned`` is compared against the count of ``RETURNED`` rows to spot
    an erasure that removed a candidate from a search that survived — so a
    detector seeded with a number that never matched would report a redaction on
    the day it shipped."""

    from app.kernel import InvariantViolated

    record = _record()
    with pytest.raises(InvariantViolated):
        SearchRecord(
            **{
                **{
                    field: getattr(record, field)
                    for field in (
                        "id",
                        "searcher_id",
                        "sport",
                        "mode",
                        "intent_read",
                        "surface",
                        "initiation",
                        "at",
                        "engine_version",
                        "ruleset_version",
                        "snapshot_version",
                        "trace_id",
                        "index_stale",
                        "best_withheld_fit",
                        "pool_description",
                        "searcher_slot_count",
                        "radius_clamp_bit",
                        "latency_ms_by_stage",
                        "candidates",
                    )
                },
                "counts": StagedCounts(
                    n_generated=9,
                    excluded_by_gate={},
                    n_scored=8,
                    n_cleared_floor=2,
                    n_returned=99,
                    n_near_miss_recorded=1,
                ),
            }
        )
