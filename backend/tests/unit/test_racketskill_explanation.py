"""The explained result: factor rows, uncertainty rows, the confidence reason.

Exercised through ``finalize`` only, like the rest of the engine tests. The
load-bearing property is that the explanation is *computed*: every direction is
one evidence category fused on its own and compared against the final estimate,
so retuning a constant moves the arrows and no copy is edited anywhere. A row
that says something the arithmetic does not is the bug this whole slice exists to
make impossible.

The specific levels and σ contributions are hypotheses, like the golden personas,
and are asserted relationally wherever the shape rather than the digit is what
matters.
"""

from dataclasses import fields

import pytest

from app.engines.assessment import (
    CALIBRATION_PRIORITY_ELEVATED,
    FACTOR_DIRECTION_DOWN,
    FACTOR_DIRECTION_NEUTRAL,
    FACTOR_DIRECTION_UP,
    AnsweredQuestion,
    AssessmentResult,
    ResultFactor,
    UncertaintyFactor,
)
from app.engines.racketskill.core import band_for
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.engine import (
    CONFIDENCE_REASON_CONTRADICTION,
    CONFIDENCE_REASON_LIMITED_EVIDENCE,
    CONFIDENCE_REASON_TIME_AWAY,
    CONFIDENCE_SENTENCES,
    FACTOR_DIRECTION_TOLERANCE,
    UNCERTAINTY_ANSWERS_DISAGREED,
    UNCERTAINTY_TIME_AWAY,
    UNCERTAINTY_UNEVEN_PROFILE,
)
from app.engines.racketskill.v3 import questions as bank
from app.engines.racketskill.v3.questions import (
    ENVIRONMENT_QUESTION_ID,
    EXECUTION_QUESTION_IDS,
    FACTOR_COMPETITIVE_CONTEXT,
    FACTOR_MATCH_EXECUTION,
    FACTOR_RECENT_ACTIVITY,
    FACTOR_TACTICAL_EXECUTION,
    LAYOFF_QUESTION_ID,
    NEVER_PLAYED_OPTION_ID,
    OPENING_QUESTION_ID,
    RELATIVE_QUESTION_ID,
    TACTICAL_QUESTION_IDS,
    TIER_BASIC,
    TIER_DISCRIMINATING,
    TIER_STANDARD,
    VOLUME_QUESTION_ID,
)
from app.kernel import Sport

SPORT = Sport.PADEL

BASIC = EXECUTION_QUESTION_IDS[TIER_BASIC]
STANDARD = EXECUTION_QUESTION_IDS[TIER_STANDARD]
DISCRIMINATING = EXECUTION_QUESTION_IDS[TIER_DISCRIMINATING]


def finalize(*pairs: tuple[str, str]) -> AssessmentResult:
    transcript = tuple(AnsweredQuestion(qid, option) for qid, option in pairs)
    return RacketSkillEngineV3().finalize(sport=SPORT, transcript=transcript)


def directions(result: AssessmentResult) -> dict[str, str]:
    return {row.key: row.direction for row in result.factors}


def widener(result: AssessmentResult, key: str) -> UncertaintyFactor | None:
    for row in result.uncertainty_factors:
        if row.key == key:
            return row
    return None


BEGINNER = ((OPENING_QUESTION_ID, NEVER_PLAYED_OPTION_ID),)

# Competes in leagues and wins almost every time, but cannot keep an easy rally
# going: the claims say one thing and the demonstrations say another.
DISAGREEING = (
    (OPENING_QUESTION_ID, "frequent"),
    (ENVIRONMENT_QUESTION_ID, "env3"),
    (RELATIVE_QUESTION_ID, "r3"),
    (BASIC, "e0"),
    (STANDARD, "e0"),
)

# Plays now and then, has not had a match in months, and last played regularly
# more than two years ago. Everything else about the profile hangs together.
_RETURNING = (
    (OPENING_QUESTION_ID, "occasional"),
    (VOLUME_QUESTION_ID, "v0"),
    (ENVIRONMENT_QUESTION_ID, "env1"),
    (RELATIVE_QUESTION_ID, "r1"),
    (BASIC, "e3"),
    (STANDARD, "e2"),
    (TACTICAL_QUESTION_IDS[0], "t1"),
)


def returning_after(layoff_option: str) -> tuple[tuple[str, str], ...]:
    return ((LAYOFF_QUESTION_ID, layoff_option), *_RETURNING)


# --- Factor rows: one per category answered, direction computed ----------------


def test_a_row_appears_for_every_category_answered_and_for_no_other() -> None:
    assert [row.key for row in finalize(*BEGINNER).factors] == [FACTOR_RECENT_ACTIVITY]

    full = finalize(*returning_after("l0"))
    assert [row.key for row in full.factors] == [
        FACTOR_RECENT_ACTIVITY,
        FACTOR_COMPETITIVE_CONTEXT,
        FACTOR_MATCH_EXECUTION,
        FACTOR_TACTICAL_EXECUTION,
    ]


def test_the_two_competitive_context_questions_fuse_into_one_row() -> None:
    # Environment and relative performance are one piece of evidence — an offset
    # on a level — so they are one row, not two that could disagree on screen.
    result = finalize(*DISAGREEING)
    context = [row for row in result.factors if row.key == FACTOR_COMPETITIVE_CONTEXT]
    assert len(context) == 1


def test_every_direction_is_the_row_own_level_against_the_final_estimate() -> None:
    # The invariant, across every persona in this file: a direction is never
    # anything but the row's own level compared against the number the player is
    # shown. Nothing can be authored into it.
    for pairs in (BEGINNER, DISAGREEING, returning_after("l3"), returning_after("l0")):
        result = finalize(*pairs)
        for row in result.factors:
            difference = row.level - result.mu
            if difference > FACTOR_DIRECTION_TOLERANCE:
                assert row.direction == FACTOR_DIRECTION_UP
            elif difference < -FACTOR_DIRECTION_TOLERANCE:
                assert row.direction == FACTOR_DIRECTION_DOWN
            else:
                assert row.direction == FACTOR_DIRECTION_NEUTRAL


def test_the_rows_tell_the_story_the_disagreement_is_made_of() -> None:
    # What the player claimed pulled up, what they demonstrated pulled down, and
    # the estimate landed between them. The rows are the arithmetic, legibly.
    result = finalize(*DISAGREEING)
    assert directions(result) == {
        FACTOR_RECENT_ACTIVITY: FACTOR_DIRECTION_UP,
        FACTOR_COMPETITIVE_CONTEXT: FACTOR_DIRECTION_UP,
        FACTOR_MATCH_EXECUTION: FACTOR_DIRECTION_DOWN,
    }


def test_changing_an_engine_constant_changes_the_directions_with_no_copy_edited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The acceptance criterion, taken literally: retune what an execution answer
    # is worth and the arrow follows the arithmetic. No sentence, label or key
    # anywhere is touched — the explanation cannot drift from the numbers,
    # because nobody is in a position to let it.
    before = finalize(*DISAGREEING)
    assert directions(before)[FACTOR_MATCH_EXECUTION] == FACTOR_DIRECTION_DOWN

    for tier in (TIER_BASIC, TIER_STANDARD):
        monkeypatch.setitem(
            bank._EXECUTION_BASE, tier, bank._EXECUTION_BASE[tier] + 2.5
        )
    after = finalize(*DISAGREEING)

    assert directions(after)[FACTOR_MATCH_EXECUTION] == FACTOR_DIRECTION_UP
    assert [row.label for row in after.factors] == [row.label for row in before.factors]
    assert [row.key for row in after.factors] == [row.key for row in before.factors]


# --- Uncertainty rows: what widened the range instead of moving the estimate ---


def test_what_widens_uncertainty_is_listed_apart_from_what_moves_the_estimate() -> None:
    # A layoff moves nothing and widens the range, so it is never a factor row;
    # it appears only among the things that widened uncertainty.
    result = finalize(*returning_after("l3"))
    assert FACTOR_RECENT_ACTIVITY in directions(result)
    assert widener(result, UNCERTAINTY_TIME_AWAY) is not None
    assert {row.key for row in result.factors}.isdisjoint(
        {row.key for row in result.uncertainty_factors}
    )


def test_a_layoff_reports_the_sigma_it_actually_added() -> None:
    away = finalize(*returning_after("l3"))
    still_playing = finalize(*returning_after("l0"))

    row = widener(away, UNCERTAINTY_TIME_AWAY)
    assert row is not None
    assert row.sigma_added > 0.0
    assert away.sigma > still_playing.sigma
    # The row accounts for the whole of the difference it claims credit for.
    assert row.sigma_added == pytest.approx(away.sigma - still_playing.sigma, abs=5e-4)
    # And the Level is untouched: a break widens the range, never lowers you.
    assert away.mu == still_playing.mu


def test_a_layoff_the_floor_absorbs_is_not_reported_as_having_widened_anything() -> (
    None
):
    # A break inside the last year disappears entirely into the σ floor, so the
    # range the player sees is identical to never having been away. Saying "we
    # widened your range" there would be the explanation inventing an effect.
    absorbed = finalize(*returning_after("l1"))
    still_playing = finalize(*returning_after("l0"))

    assert absorbed.sigma == still_playing.sigma
    assert widener(absorbed, UNCERTAINTY_TIME_AWAY) is None
    assert absorbed.uncertainty_factors == still_playing.uncertainty_factors


def test_an_uneven_game_is_listed_as_widening_and_never_as_a_disagreement() -> None:
    # Cannot hold an easy rally, handles the hardest ball in the bank. The range
    # widens and the row says so; nothing calls it a disagreement, because the
    # tolerance read it — correctly — as one uneven profile.
    uneven = finalize(
        (OPENING_QUESTION_ID, "regular"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r1"),
        (BASIC, "e0"),
        (DISCRIMINATING, "e4"),
    )
    assert widener(uneven, UNCERTAINTY_UNEVEN_PROFILE) is not None
    assert widener(uneven, UNCERTAINTY_ANSWERS_DISAGREED) is None
    assert uneven.confidence_reason is not None
    assert uneven.confidence_reason.key == CONFIDENCE_REASON_LIMITED_EVIDENCE


def test_an_unresolved_disagreement_is_listed_with_the_sigma_it_added() -> None:
    result = finalize(*DISAGREEING)
    row = widener(result, UNCERTAINTY_ANSWERS_DISAGREED)
    assert row is not None
    assert row.sigma_added > 0.0


def test_nothing_widened_means_nothing_is_listed() -> None:
    assert finalize(*BEGINNER).uncertainty_factors == ()


# --- The confidence reason: one branch per situation that produces it ----------


def test_the_sentence_branches_on_the_situation_that_actually_produced_it() -> None:
    branches = {
        CONFIDENCE_REASON_LIMITED_EVIDENCE: finalize(*BEGINNER),
        CONFIDENCE_REASON_TIME_AWAY: finalize(*returning_after("l3")),
        CONFIDENCE_REASON_CONTRADICTION: finalize(*DISAGREEING),
    }
    for expected_key, result in branches.items():
        assert result.confidence_reason is not None
        assert result.confidence_reason.key == expected_key
        assert result.confidence_reason.sentence == CONFIDENCE_SENTENCES[expected_key]

    sentences = {
        result.confidence_reason.sentence  # type: ignore[union-attr]
        for result in branches.values()
    }
    assert len(sentences) == len(branches)  # a different one for each situation


def test_every_result_carries_a_reason_even_when_nothing_went_wrong() -> None:
    # "Not enough match evidence yet" is the case every onboarding rating shares,
    # so the sentence is never absent — a blank space where an explanation should
    # be reads as the platform having nothing to say for its own number.
    for pairs in (BEGINNER, DISAGREEING, returning_after("l0"), returning_after("l3")):
        assert finalize(*pairs).confidence_reason is not None


def test_the_dominant_widener_authors_the_sentence() -> None:
    # Away for more than two years, and claims that sit a little beyond the
    # tolerance from the demonstrations. Both widened the range; the layoff
    # widened it more, so the layoff is what the player is told about — the
    # branch is chosen by the arithmetic, not by an authored precedence.
    both = finalize(
        (LAYOFF_QUESTION_ID, "l3"),
        (OPENING_QUESTION_ID, "regular"),
        (ENVIRONMENT_QUESTION_ID, "env2"),
        (RELATIVE_QUESTION_ID, "r1"),
        (BASIC, "e0"),
        (STANDARD, "e0"),
    )
    away = widener(both, UNCERTAINTY_TIME_AWAY)
    disagreed = widener(both, UNCERTAINTY_ANSWERS_DISAGREED)
    assert away is not None and disagreed is not None
    assert away.sigma_added > disagreed.sigma_added

    assert both.confidence_reason is not None
    assert both.confidence_reason.key == CONFIDENCE_REASON_TIME_AWAY
    # The disagreement still costs what it costs; only the sentence is the
    # layoff's, because that is the situation that actually produced the range.
    assert both.calibration_priority == CALIBRATION_PRIORITY_ELEVATED


# --- No presentation, and the band's own boundaries ----------------------------


def test_the_payload_carries_no_presentation_values() -> None:
    # Colours, glyphs and ordering are the client's. A server that ships a hex
    # code ships a design decision two clients then cannot override.
    presentation = (
        "colour",
        "color",
        "icon",
        "glyph",
        "emoji",
        "order",
        "sort",
        "rank",
        "position",
        "style",
        "variant",
        "severity",
    )
    for cls in (ResultFactor, UncertaintyFactor, AssessmentResult):
        for field in fields(cls):
            assert not any(word in field.name.lower() for word in presentation), (
                f"{cls.__name__}.{field.name} looks like presentation"
            )


def test_the_band_boundaries_travel_on_the_result() -> None:
    # The structural fix for a card printing a band name that disagreed with the
    # number beside it: there is no second source to read them from.
    # The printed bands are not contiguous — 1,5 to 1,6 and 2,6 to 2,7 are gaps —
    # so a Level can sit between two of them and still be banded. What must hold
    # is that the band travelling on the result is the one the model's own
    # `band_for` assigns to the Level beside it, with that band's own edges.
    for pairs in (BEGINNER, DISAGREEING, returning_after("l3")):
        result = finalize(*pairs)
        expected = band_for(result.mu)
        assert result.band.name == expected.label
        edges = (result.band.lower, result.band.upper)
        assert edges == (expected.lower, expected.upper)


def test_the_explanation_is_deterministic() -> None:
    assert finalize(*DISAGREEING) == finalize(*DISAGREEING)
