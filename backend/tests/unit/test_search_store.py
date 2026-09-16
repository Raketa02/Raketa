"""The search record: written whole, read back narrow.

Two claims, and the second is an authorization rule rather than a query
optimisation: **the searcher may read their own ``RETURNED`` rows and nothing
else.** *A player may ask why somebody was shown; nobody may ask who was
withheld* — so the near-miss band has no read path at all, and a stranger's
``search_id`` answers exactly as an unknown one does.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.matchmaking.domain.relaxation import (
    RelaxationAsk,
    Rung,
    RungOffer,
)
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    GameResult,
    InclusionReason,
    LineupRecord,
    PoolDescription,
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
    WithheldReason,
)
from app.modules.matchmaking.infrastructure.search_model import (
    SearchCandidateORM,
    SearchORM,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_search_store import (
    SqlAlchemySearchStore,
)
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.photos import PhotoReviewDecision

AT = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)
#: The week the search ran on. Four cells across four days, which ``window_of``
#: reads as ``THIS_WEEK`` — the same window the pool description carries, because
#: the read-back **re-derives** it from this grid rather than reading the label.
GRID = ("1:EVENING", "3:EVENING", "5:EVENING", "6:MORNING")
#: The searcher's own coarse area, as ``area_code_of`` spells one. Recorded
#: beside the grid and read back the same way: it is the second half of the one
#: comparison a card is licensed to make.
MY_AREA = "A+05218+002123"
OFFERED_BY = UUID("22222222-2222-2222-2222-222222222222")
SEARCHER = UUID("11111111-1111-1111-1111-111111111111")
STRANGER = UUID("22222222-2222-2222-2222-222222222222")
PHOTO = UUID("33333333-3333-3333-3333-333333333333")


def _candidate(band: CandidateBand, position: int) -> SearchCandidateRecord:
    return SearchCandidateRecord(
        band=band,
        position=position,
        player_id=uuid4(),
        fit=72.5,
        terms=({"term": "LEVEL_FIT", "weight": 29.9, "value": 1.0},),
        degraded_terms=("RELIABILITY",),
        degraded_reasons=("NOT_YET_ON_THIS_PLATFORM",),
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
        concerns=("SOCIAL_VIBE",),
        distance_km=4,
        # The card is recorded on the row that showed it, so a near miss — shown
        # to nobody — carries none, and neither does it carry a counted game's
        # price.
        card=(
            RecordedCard(
                name="ada",
                photo_id=PHOTO,
                review=PhotoReviewDecision.FLAGGED,
                area_code="LDN-CENTRAL",
                social_tags=("PLAYS_TO_WIN",),
                # And the line, for the record block's reason below.
                intro="Moved from Wrocław in May.",
                level=2.7,
                band="Improver",
                range_low=2.36,
                range_high=3.04,
                # The record block, whole, because the round trip below is an
                # equality: a field the fixture leaves at its default is a field
                # the store could drop and nothing would say so.
                player_score=71,
                counted_games=6,
                last_five=(GameResult.LOSS, GameResult.WIN, GameResult.WIN),
            )
            if band is CandidateBand.RETURNED
            else None
        ),
        at_stake=(
            AtStake(win_delta=0.07, loss_delta=-0.05)
            if band is CandidateBand.RETURNED
            else None
        ),
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
        searcher_grid=GRID,
        searcher_slot_count=len(GRID),
        searcher_area_code=MY_AREA,
        radius_clamp_bit=True,
        rung_offers=(
            RungOffer(
                rung=Rung.A,
                ask=RelaxationAsk.TIMES,
                candidates_above_floor=3,
                window=Window.ANY,
                slot="2:EVENING",
            ),
            RungOffer(
                rung=Rung.B,
                ask=RelaxationAsk.RADIUS,
                candidates_above_floor=5,
                window=Window.THIS_WEEK,
                radius_km=15,
            ),
        ),
        offered_by_search_id=OFFERED_BY,
        rung_taken=Rung.B,
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

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None
    rows = read.returned
    assert [row.position for row in rows] == [1, 2]
    assert rows[0].terms[0]["term"] == "LEVEL_FIT"
    assert rows[0].degraded_terms == ("RELIABILITY",)
    # Index-aligned with it, and stored rather than re-derived: a read-back
    # never recomputes, so whose gap it was has to be on the row.
    assert rows[0].degraded_reasons == ("NOT_YET_ON_THIS_PLATFORM",)
    assert rows[0].liveness_signals["INTEREST_RECEIVED"] is None
    assert rows[0].inclusion_reason is InclusionReason.ZERO_EXPOSURE


async def test_the_whole_row_that_was_shown_comes_back(store):
    """**The record is self-contained**, because nothing it was assembled from
    remembers what it said an hour ago.

    A name changes, a Level moves, a player leaves an area, and a Level delta
    is priced against ratings that keep moving — so a read-back that re-read them
    would answer a different search and call it the same one. The card, the
    concerns, the distance and the at-stake block are on the row.
    """

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    row = (await adapter.find(search_id=record.id, searcher_id=SEARCHER)).returned[0]

    assert row.card is not None
    assert row.card.name == "ada"
    assert row.card.photo_id == PHOTO, "an id, never a URL"
    assert row.card.social_tags == ("PLAYS_TO_WIN",)
    assert (row.card.level, row.card.range_low, row.card.range_high) == (
        2.7,
        2.36,
        3.04,
    ), "a Level read back without the range it was shown with"
    assert row.concerns == ("SOCIAL_VIBE",)
    assert row.distance_km == 4
    assert row.at_stake == AtStake(win_delta=0.07, loss_delta=-0.05)
    # The record block, which is on the row for the same reason: a Player Score
    # moves, a run of form gains a game, and a counted-game count only grows.
    assert row.card.player_score == 71
    assert row.card.counted_games == 6
    assert row.card.last_five == (GameResult.LOSS, GameResult.WIN, GameResult.WIN)


async def test_a_card_written_before_the_record_block_reads_back_without_one(store):
    """**Soft keys, for ``review``'s reason and not for a range's.**

    A card blob written before the block existed carries none of the three, and
    *this search showed no record* is exactly what each absence already means —
    so nothing is invented by reading an older card as one that printed none,
    which is what it did. A range read this way would be different: a card that
    stated a Level always stated how sure of it the platform was.
    """

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    stored = (
        await session.execute(
            select(SearchCandidateORM).where(
                SearchCandidateORM.search_id == record.id,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
            )
        )
    ).scalars()
    for candidate in stored:
        candidate.player_card = {
            key: value
            for key, value in candidate.player_card.items()
            if key not in {"player_score", "counted_games", "last_five"}
        }
    await session.commit()

    row = (await adapter.find(search_id=record.id, searcher_id=SEARCHER)).returned[0]

    assert row.card is not None
    assert row.card.name == "ada", "an older card stopped reading at all"
    assert row.card.player_score is None
    assert row.card.counted_games is None
    assert row.card.last_five == ()


async def test_a_card_written_before_the_intro_reads_back_without_one(store):
    """The same soft key, one field over (``docs/adr/0170``): a blob written
    before the line existed showed no line, and *no intro* is what its absence
    already means."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    stored = (
        await session.execute(
            select(SearchCandidateORM).where(
                SearchCandidateORM.search_id == record.id,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
            )
        )
    ).scalars()
    for candidate in stored:
        candidate.player_card = {
            key: value for key, value in candidate.player_card.items() if key != "intro"
        }
    await session.commit()

    row = (await adapter.find(search_id=record.id, searcher_id=SEARCHER)).returned[0]

    assert row.card is not None
    assert row.card.name == "ada", "an older card stopped reading at all"
    assert row.card.intro is None


async def test_the_search_row_comes_back_whole_beside_its_candidates(store):
    """One read, one search: a second method for the envelope would be a second
    chance to fetch one search's counters beside another's candidates."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None
    assert read.id == record.id
    assert read.at == AT, "a stored moment reads back as the UTC it was written as"
    assert read.sport is Sport.PADEL
    assert read.mode is SearchMode.COMPETITIVE
    assert read.counts.n_returned == 2
    assert read.counts.excluded_by_gate == {"BLOCKED": 1}
    assert read.pool_description.window is Window.THIS_WEEK
    assert read.best_withheld_fit == 41.0
    # The searcher's own area, as **this** search ran on it. A read-back that
    # re-read the profile would say *in your area* about the area they live in
    # now, over a search that was answered before they moved.
    assert read.searcher_area_code == MY_AREA


async def test_a_search_recorded_before_the_area_was_kept_reads_back_without_one(
    store,
):
    """``None`` is *not recorded*, and it is the only absence there is.

    Rows written before the column existed have no area, and searches are kept
    for ever — so the state is standing rather than a migration's leftover. What
    it must never become on the way back is an empty code: every real code
    compares unequal to one, which is *never in your area* said quietly.
    """

    adapter, session = store
    record = replace(_record(), searcher_area_code=None)

    await adapter.record(record)
    await session.commit()

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None
    assert read.searcher_area_code is None


def _a_line_up(*, seated: tuple[UUID, ...] | None) -> SearchRecord:
    """A line-up's record: the shortlist's, on the surface layer 4 belongs to."""

    return replace(
        _record(),
        surface=SearchSurface.LINEUP,
        lineup=LineupRecord(
            combinations=4,
            refused_by_gate=1,
            refused_by_floor=0,
            max_fit_rank_seated=None if not seated else 2,
            rows=(),
            seated=seated,
        ),
    )


async def test_layer_four_records_who_sat_down_and_reads_it_back(store):
    """**The seated are on layer 4**, since the returned band became the pool
    ([#407](https://github.com/Raketa02/Raketa/issues/407)). In the order they
    were seated, and an empty tuple is *nobody tonight* — which is not the
    absence below."""

    adapter, session = store
    seated = (uuid4(), uuid4())
    record = _a_line_up(seated=seated)

    await adapter.record(record)
    await session.commit()

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None and read.lineup is not None
    assert read.lineup.seated == seated
    assert read.lineup.max_fit_rank_seated == 2


async def test_a_line_up_recorded_before_the_seated_were_kept_reads_back_without_them(
    store,
):
    """``None`` is *not recorded*, and never *nobody*.

    A row written while the returned band was the seated in seat order carries
    no ``seated`` key in its blob, and searches are kept for ever — so the
    state is standing rather than a migration's leftover, exactly as the area
    code's is.
    """

    adapter, session = store
    record = _a_line_up(seated=None)

    await adapter.record(record)
    await session.commit()
    async with session.begin_nested():
        row = (
            await session.execute(select(SearchORM).where(SearchORM.id == record.id))
        ).scalar_one()
        assert "seated" not in row.lineup, "an unrecorded fact was written as null"

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None and read.lineup is not None
    assert read.lineup.seated is None


def test_layer_four_cannot_seat_nobody_and_read_a_deepest_rank():
    """The two facts about the seated are one fact in two columns."""

    from app.kernel import InvariantViolated

    with pytest.raises(InvariantViolated):
        LineupRecord(
            combinations=0,
            refused_by_gate=0,
            refused_by_floor=0,
            max_fit_rank_seated=3,
            rows=(),
            seated=(),
        )


def test_an_area_code_is_recorded_or_absent_and_never_blank():
    """The invariant that keeps the two absences apart at the source."""

    from app.kernel import InvariantViolated

    with pytest.raises(InvariantViolated):
        replace(_record(), searcher_area_code="")


async def test_the_near_miss_band_is_stored_and_has_no_read_path(store):
    """Layer 3 is engine-internal. It is in the table, and there is no method
    here that could return it — not to the searcher, not to anybody."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()

    read = await adapter.find(search_id=record.id, searcher_id=SEARCHER)

    assert read is not None
    assert all(row.band is CandidateBand.RETURNED for row in read.candidates)
    assert len(read.candidates) == 2, "the near-miss row came back"
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

    foreign = await adapter.find(search_id=record.id, searcher_id=STRANGER)
    unknown = await adapter.find(search_id=uuid4(), searcher_id=SEARCHER)

    assert foreign is None is unknown


async def test_a_search_discloses_the_sport_it_showed_somebody_in(store):
    """The read the player record is entitled through (``docs/adr/0159``).

    **Sports and not searches**: the caller needs the partition to re-evaluate a
    gate in, and a hundred padel searches of the same pair are one partition.
    """

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()
    shown = record.candidates[0].player_id

    assert await adapter.sports_shown_in(
        searcher_id=SEARCHER, player_id=shown
    ) == frozenset({Sport.PADEL})


async def test_a_near_miss_discloses_nothing(store):
    """A player withheld from a search was shown to nobody, so nothing about
    them was disclosed — layer 3 has no read path here either."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()
    withheld = next(
        row.player_id
        for row in record.candidates
        if row.band is CandidateBand.NEAR_MISS
    )

    assert (
        await adapter.sports_shown_in(searcher_id=SEARCHER, player_id=withheld)
        == frozenset()
    )


async def test_a_disclosure_belongs_to_the_searcher_who_was_shown_it(store):
    """Somebody else's search discloses nothing to this reader, which is the
    difference between a disclosure and a directory of everybody the platform has
    ever shown to anybody."""

    adapter, session = store
    record = _record()
    await adapter.record(record)
    await session.commit()
    shown = record.candidates[0].player_id

    assert (
        await adapter.sports_shown_in(searcher_id=STRANGER, player_id=shown)
        == frozenset()
    )


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
            degraded_reasons=(),
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
            concerns=(),
            distance_km=None,
            card=None,
            at_stake=None,
        )


def test_a_basis_and_the_reasons_beside_it_may_not_be_different_lengths():
    """The two columns are **one fact**, and a row where they drifted is a basis
    nobody can read.

    Refused at the write rather than at the wire: the renderer zips them
    strictly, which would surface a row that was already stored wrong as a
    five-hundred on a read-back a month later — and the row is immutable, so
    there would be nothing to do about it.
    """

    from app.kernel import InvariantViolated

    with pytest.raises(InvariantViolated):
        SearchCandidateRecord(
            band=CandidateBand.RETURNED,
            position=1,
            player_id=uuid4(),
            fit=50.0,
            terms=(),
            degraded_terms=("RELIABILITY",),
            degraded_reasons=(),
            modifiers=(),
            liveness_reasons=(),
            liveness_signals={},
            shared_count=0,
            their_slot_count=0,
            days_away=None,
            inclusion_reason=None,
            withheld_reason=None,
            missing_terms=(),
            reliability_penalty_applied=False,
            reliability_penalty_decisive=False,
            concerns=(),
            distance_km=None,
            card=RecordedCard(
                name="ada",
                photo_id=None,
                review=None,
                area_code="LDN-CENTRAL",
                social_tags=(),
                intro=None,
                level=2.7,
                band="Improver",
                range_low=2.36,
                range_high=3.04,
                player_score=None,
                counted_games=None,
                last_five=(),
            ),
            at_stake=None,
        )


def test_a_near_miss_may_not_carry_a_card():
    """A near miss was **shown to nobody**, so there is no card it could have
    shown — and a row carrying one would be layer 3 holding a person's name
    for a screen it may never reach."""

    from app.kernel import InvariantViolated

    with pytest.raises(InvariantViolated):
        SearchCandidateRecord(
            band=CandidateBand.NEAR_MISS,
            position=1,
            player_id=uuid4(),
            fit=20.0,
            terms=(),
            degraded_terms=(),
            degraded_reasons=(),
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
            concerns=(),
            distance_km=None,
            card=RecordedCard(
                name="ada",
                photo_id=None,
                review=None,
                area_code="LDN-CENTRAL",
                social_tags=(),
                intro=None,
                level=2.7,
                band="Improver",
                range_low=2.36,
                range_high=3.04,
                player_score=None,
                counted_games=None,
                last_five=(),
            ),
            at_stake=None,
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
                        "searcher_grid",
                        "searcher_slot_count",
                        "searcher_area_code",
                        "radius_clamp_bit",
                        "rung_offers",
                        "offered_by_search_id",
                        "rung_taken",
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
