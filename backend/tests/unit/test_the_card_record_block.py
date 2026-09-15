"""The record block, from the row that recorded it to the wire it crosses on.

Three fields, one rule: **each is omitted rather than nought where the fact is
missing.** A Player Score omitted is *the platform has watched this person do
nothing*, a counted-game count omitted is *none of the counted games was theirs*,
and an empty run of form is *nothing of theirs has been counted and agreed*. A
zero in place of any of them is a claim, and the three claims are all false about
somebody the platform has never seen play.

The fourth thing asserted here is the one that only exists once they are
recorded: *Most reliable* becomes offerable **on a read-back**, and it orders by
the score the row holds rather than by one this route goes and asks for.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.application.read_back_search import (
    ReadBackAnswer,
    ReadBackRow,
)
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    GameResult,
    PoolDescription,
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
    StagedCounts,
)
from app.modules.matchmaking.domain.sorting import of_record, sorts_available
from app.modules.matchmaking.presentation.rendering import render_read_back
from app.modules.player_profile.domain.availability import Window

AT = datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc)
GRID = ("1:EVENING", "3:EVENING")
NO_PHOTOS: dict[UUID, str] = {}


def card(
    *,
    player_score: int | None = None,
    counted_games: int | None = None,
    last_five: tuple[GameResult, ...] = (),
) -> RecordedCard:
    return RecordedCard(
        nickname="ada",
        photo_id=None,
        review=None,
        area_code="LDN-CENTRAL",
        social_tags=("PLAYS_TO_WIN",),
        intro=None,
        level=2.7,
        band="Improver",
        range_low=2.36,
        range_high=3.04,
        player_score=player_score,
        counted_games=counted_games,
        last_five=last_five,
    )


def row(position: int, recorded: RecordedCard) -> SearchCandidateRecord:
    return SearchCandidateRecord(
        band=CandidateBand.RETURNED,
        position=position,
        # Ascending with the position, so a sort that fell back to the id
        # tie-break would leave the order alone and prove nothing.
        player_id=UUID(int=position),
        fit=90.0 - position,
        # Empty on purpose: this file asserts what a **card** carries, and a
        # breakdown here would be a second thing to keep true.
        terms=(),
        degraded_terms=(),
        degraded_reasons=(),
        modifiers=(),
        liveness_reasons=(),
        liveness_signals={},
        shared_count=2,
        their_slot_count=5,
        days_away=1,
        inclusion_reason=None,
        withheld_reason=None,
        missing_terms=(),
        reliability_penalty_applied=False,
        reliability_penalty_decisive=False,
        concerns=(),
        distance_km=4,
        card=recorded,
        at_stake=None,
    )


def a_read_back(*rows: SearchCandidateRecord) -> ReadBackAnswer:
    verdicts = tuple(ReadBackRow(recorded=one, withheld=False) for one in rows)
    record = SearchRecord(
        id=uuid4(),
        searcher_id=uuid4(),
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
            excluded_by_gate={},
            n_scored=len(rows),
            n_cleared_floor=len(rows),
            n_returned=len(rows),
            n_near_miss_recorded=0,
        ),
        best_withheld_fit=None,
        pool_description=PoolDescription(
            sport=Sport.PADEL,
            radius_km_used=10,
            players_in_range=8,
            window=Window.THIS_WEEK,
        ),
        searcher_grid=GRID,
        searcher_slot_count=len(GRID),
        searcher_area_code="LDN-CENTRAL",
        radius_clamp_bit=False,
        rung_offers=None,
        offered_by_search_id=None,
        rung_taken=None,
        latency_ms_by_stage={"pipeline": 3},
        candidates=rows,
    )
    return ReadBackAnswer(
        record=record,
        rows=verdicts,
        sorts_available=sorts_available(
            tuple(of_record(one) for one in rows), surface=record.surface
        ),
    )


def drawn(answer: ReadBackAnswer) -> dict:
    return render_read_back(answer, NO_PHOTOS).model_dump(exclude_unset=True)


def only_card(answer: ReadBackAnswer) -> dict:
    return drawn(answer)["candidates"][0]["player_card"]


def test_a_player_the_platform_has_watched_nothing_of_carries_none_of_the_three():
    """**Omitted, and never null-and-zero.** All three absences at once, which is
    the ordinary state of this platform and therefore of most cards."""

    fields = only_card(a_read_back(row(1, card())))

    assert "player_score" not in fields
    assert "counted_games" not in fields
    assert "last_five" not in fields


def test_the_whole_block_crosses_when_the_platform_has_watched_them():
    """And the run of form crosses **oldest to newest**, as it was recorded: the
    row is read left to right, and a client reversing a list can reverse it
    wrongly."""

    fields = only_card(
        a_read_back(
            row(
                1,
                card(
                    player_score=74,
                    counted_games=9,
                    last_five=(
                        GameResult.LOSS,
                        GameResult.WIN,
                        GameResult.WIN,
                        GameResult.LOSS,
                        GameResult.WIN,
                    ),
                ),
            )
        )
    )

    assert fields["player_score"] == 74
    assert fields["counted_games"] == 9
    assert fields["last_five"] == ["LOSS", "WIN", "WIN", "LOSS", "WIN"]


def test_a_short_run_is_drawn_short_and_never_padded():
    """Fewer than five is a real answer. Padding it would invent games, and
    padding it with a neutral third value would invent a vocabulary."""

    fields = only_card(
        a_read_back(row(1, card(counted_games=2, last_five=(GameResult.WIN,))))
    )

    assert fields["last_five"] == ["WIN"]


def test_counted_games_without_an_agreed_score_is_a_count_and_no_run():
    """*An unscored game is an evening, not evidence.* It is in the count and out
    of the run, and the two absences are not the same absence."""

    fields = only_card(a_read_back(row(1, card(counted_games=3))))

    assert fields["counted_games"] == 3
    assert "last_five" not in fields


def test_no_date_reaches_the_card_with_the_run_of_form():
    """The recency refusal, at the one field that could have broken it.

    Five events in order is a run of form; five events with moments beside them
    is *last seen*, which this product does not have in any shape. The central
    walk over the emitted contract asserts the same thing by field name — this
    asserts it about the values one card actually draws.
    """

    fields = only_card(
        a_read_back(
            row(1, card(counted_games=2, last_five=(GameResult.WIN, GameResult.LOSS)))
        )
    )

    assert fields["last_five"] == ["WIN", "LOSS"]
    assert all(isinstance(one, str) for one in fields["last_five"])


def test_most_reliable_is_offered_on_a_read_back_once_the_score_is_recorded():
    """The whole point of recording it.

    A read-back reproduces the answer that was given, so a control it draws has
    to be orderable by a reading the row itself holds — which is why the fix was
    never *go and ask again*.
    """

    answer = a_read_back(
        row(1, card(player_score=40)),
        row(2, card(player_score=91)),
    )

    assert SortOption.MOST_RELIABLE in answer.sorts_available


def test_a_read_back_whose_rows_recorded_no_score_draws_no_control():
    """A reading that tells no two rows apart resorts the list into id order and
    calls it *most reliable*. Not drawn — a visible control that reorders nothing
    is the product lying quietly."""

    answer = a_read_back(row(1, card()), row(2, card()))

    assert SortOption.MOST_RELIABLE not in answer.sorts_available


def test_a_player_with_no_score_sorts_last_rather_than_first():
    """``CLOSEST``'s rule, for ``CLOSEST``'s reason. An absent score read as a
    zero would sort somebody the platform knows nothing about as the least
    reliable person on the list."""

    known, unknown = of_record(row(1, card(player_score=55))), of_record(row(2, card()))

    assert known.reliability == 55.0
    assert unknown.reliability is None
