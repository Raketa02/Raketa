"""RacketSkill v3 adaptive routing and the question bank, through the Protocol.

The engine is exercised only through ``next_step`` and ``finalize`` over a
scripted answer policy — never through its internal fusion or encoding. The
interesting behaviours here are emergent: an advanced player answers more
questions than a developing one, a layoff widens σ without moving μ, relative
performance resolves symmetrically as an offset. None can be expressed as a test
of a single function.

Split by what a constant retune should do:

* **Invariants** must survive a retune — layoff is σ-only, a beginner sees no
  technique question, a developing player never sees a discriminating one, every
  routing decision records a reason.
* **The question bank** is asserted structurally — reading order, word budget,
  jargon-free basics.
* **Properties** are generated — μ in scale, σ above the floor, confidence never
  100, the ceiling never exceeded.
"""

import random

from app.engines.assessment import (
    AnsweredQuestion,
    AskQuestion,
    Complete,
)
from app.engines.racketskill.core import SCALE_MAX, SCALE_MIN
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.engine import MAX_QUESTIONS, SIGMA_FLOOR
from app.engines.racketskill.v3.questions import (
    ENVIRONMENT_QUESTION_ID,
    EXECUTION_QUESTION_IDS,
    LAYOFF_QUESTION_ID,
    OPENING_QUESTION_ID,
    RELATIVE_QUESTION_ID,
    TACTICAL_QUESTION_IDS,
    TIER_DISCRIMINATING,
    VOLUME_QUESTION_ID,
    all_questions_for,
)
from app.kernel import SPORT_SPECS, Sport

ALL_SPORTS = tuple(Sport)


# --- The scripted-answer driver ------------------------------------------------


def run(engine: RacketSkillEngineV3, sport: Sport, policy: dict[str, str]):
    """Run a scripted policy to completion.

    ``policy`` maps a question id to the option id to answer it with. Returns the
    ordered ``AskQuestion`` steps, the transcript, and the finalised result.
    """

    transcript: list[AnsweredQuestion] = []
    asked: list[AskQuestion] = []
    while True:
        step = engine.next_step(sport=sport, transcript=tuple(transcript))
        if isinstance(step, Complete):
            break
        assert isinstance(step, AskQuestion)
        asked.append(step)
        option_id = policy[step.question.id]
        transcript.append(AnsweredQuestion(step.question.id, option_id))
        assert len(transcript) <= MAX_QUESTIONS  # never loops past the ceiling
    result = engine.finalize(sport=sport, transcript=tuple(transcript))
    return asked, tuple(transcript), result


def asked_ids(asked: list[AskQuestion]) -> list[str]:
    return [step.question.id for step in asked]


def execution_tiers(asked: list[AskQuestion]) -> list[str]:
    execution = set(EXECUTION_QUESTION_IDS.values())
    return [step.question.tier for step in asked if step.question.id in execution]


# Personas as answer policies. Every possible question id is answered so any
# routing path is covered.
BEGINNER = {OPENING_QUESTION_ID: "never-played"}

DEVELOPING = {
    OPENING_QUESTION_ID: "occasional",
    VOLUME_QUESTION_ID: "v1",
    LAYOFF_QUESTION_ID: "l0",
    ENVIRONMENT_QUESTION_ID: "env0",
    RELATIVE_QUESTION_ID: "r0",
    EXECUTION_QUESTION_IDS["basic"]: "e2",
    EXECUTION_QUESTION_IDS["standard"]: "e2",
    EXECUTION_QUESTION_IDS["discriminating"]: "e2",
    TACTICAL_QUESTION_IDS[0]: "t1",
    TACTICAL_QUESTION_IDS[1]: "t1",
}

ESTABLISHED = {
    OPENING_QUESTION_ID: "regular",
    VOLUME_QUESTION_ID: "v2",
    LAYOFF_QUESTION_ID: "l0",
    ENVIRONMENT_QUESTION_ID: "env2",
    RELATIVE_QUESTION_ID: "r1",
    EXECUTION_QUESTION_IDS["basic"]: "e3",
    EXECUTION_QUESTION_IDS["standard"]: "e3",
    EXECUTION_QUESTION_IDS["discriminating"]: "e3",
    TACTICAL_QUESTION_IDS[0]: "t2",
    TACTICAL_QUESTION_IDS[1]: "t2",
}

ADVANCED = {
    OPENING_QUESTION_ID: "frequent",
    VOLUME_QUESTION_ID: "v3",
    LAYOFF_QUESTION_ID: "l0",
    ENVIRONMENT_QUESTION_ID: "env3",
    RELATIVE_QUESTION_ID: "r3",
    EXECUTION_QUESTION_IDS["basic"]: "e4",
    EXECUTION_QUESTION_IDS["standard"]: "e4",
    EXECUTION_QUESTION_IDS["discriminating"]: "e4",
    TACTICAL_QUESTION_IDS[0]: "t3",
    TACTICAL_QUESTION_IDS[1]: "t3",
}


# --- Invariants: must survive a constant retune --------------------------------


def test_beginner_is_asked_no_technique_question_of_any_tier() -> None:
    engine = RacketSkillEngineV3()
    asked, transcript, _ = run(engine, Sport.PADEL, BEGINNER)
    assert asked_ids(asked) == [OPENING_QUESTION_ID]
    assert len(transcript) == 1
    assert not execution_tiers(asked)


def test_developing_player_never_sees_a_discriminating_question() -> None:
    engine = RacketSkillEngineV3()
    asked, _, result = run(engine, Sport.TENNIS, DEVELOPING)
    tiers = execution_tiers(asked)
    assert tiers  # a developing player still demonstrates
    assert TIER_DISCRIMINATING not in tiers
    assert result.band.name in {"New", "Developing"}


def test_advanced_player_is_asked_a_discriminating_question() -> None:
    engine = RacketSkillEngineV3()
    asked, _, _ = run(engine, Sport.SQUASH, ADVANCED)
    assert TIER_DISCRIMINATING in execution_tiers(asked)


def test_advanced_player_demonstrates_more_than_a_developing_one() -> None:
    # In this slice the length is the hard-ceiling sequence, not yet trimmed by
    # marginal-value stopping (#7), so the distinguishing behaviour is the
    # demonstration count that scales with the estimate: three against two.
    engine = RacketSkillEngineV3()
    developing_asked, _, _ = run(engine, Sport.PADEL, DEVELOPING)
    advanced_asked, _, _ = run(engine, Sport.PADEL, ADVANCED)
    assert len(execution_tiers(advanced_asked)) > len(execution_tiers(developing_asked))


def test_reaching_established_forces_a_third_demonstration() -> None:
    engine = RacketSkillEngineV3()
    asked, _, result = run(engine, Sport.BADMINTON, ESTABLISHED)
    assert result.band.name in {"Established", "Advanced"}
    assert len(execution_tiers(asked)) == 3


def test_developing_player_stops_at_two_demonstrations() -> None:
    engine = RacketSkillEngineV3()
    asked, _, _ = run(engine, Sport.TENNIS, DEVELOPING)
    assert len(execution_tiers(asked)) == 2


def test_layoff_widens_sigma_and_leaves_mu_identical_to_the_digit() -> None:
    engine = RacketSkillEngineV3()
    without = (
        AnsweredQuestion(OPENING_QUESTION_ID, "occasional"),
        AnsweredQuestion(VOLUME_QUESTION_ID, "v0"),
        AnsweredQuestion(LAYOFF_QUESTION_ID, "l0"),  # still playing — no penalty
    )
    with_layoff = (
        AnsweredQuestion(OPENING_QUESTION_ID, "occasional"),
        AnsweredQuestion(VOLUME_QUESTION_ID, "v0"),
        AnsweredQuestion(LAYOFF_QUESTION_ID, "l3"),  # more than two years ago
    )
    base = engine.finalize(sport=Sport.PADEL, transcript=without)
    delayed = engine.finalize(sport=Sport.PADEL, transcript=with_layoff)
    assert delayed.mu == base.mu  # identical to the digit
    assert delayed.sigma > base.sigma


def test_volume_is_asked_only_after_an_ambiguous_regularity_answer() -> None:
    engine = RacketSkillEngineV3()
    ambiguous, _, _ = run(engine, Sport.PADEL, DEVELOPING)  # opens with "occasional"
    unambiguous, _, _ = run(engine, Sport.PADEL, ESTABLISHED)  # opens with "regular"
    assert VOLUME_QUESTION_ID in asked_ids(ambiguous)
    assert VOLUME_QUESTION_ID not in asked_ids(unambiguous)


def test_layoff_only_when_volume_is_low_and_the_player_has_a_history() -> None:
    engine = RacketSkillEngineV3()
    # Ambiguous regularity, but volume did not come back low -> no layoff.
    not_low = dict(DEVELOPING, **{VOLUME_QUESTION_ID: "v1"})
    low = dict(DEVELOPING, **{VOLUME_QUESTION_ID: "v0"})
    not_low_asked, _, _ = run(engine, Sport.PADEL, not_low)
    low_asked, _, _ = run(engine, Sport.PADEL, low)
    assert LAYOFF_QUESTION_ID not in asked_ids(not_low_asked)
    assert LAYOFF_QUESTION_ID in asked_ids(low_asked)


def test_layoff_is_never_asked_of_a_beginner() -> None:
    engine = RacketSkillEngineV3()
    asked, _, _ = run(engine, Sport.SQUASH, BEGINNER)
    assert LAYOFF_QUESTION_ID not in asked_ids(asked)
    assert VOLUME_QUESTION_ID not in asked_ids(asked)


def test_competitive_context_precedes_any_execution_question() -> None:
    engine = RacketSkillEngineV3()
    for policy in (DEVELOPING, ESTABLISHED, ADVANCED):
        ids = asked_ids(run(engine, Sport.TENNIS, policy)[0])
        first_execution = min(
            (i for i, qid in enumerate(ids) if qid in EXECUTION_QUESTION_IDS.values()),
            default=None,
        )
        assert first_execution is not None
        assert ids.index(ENVIRONMENT_QUESTION_ID) < first_execution
        assert ids.index(RELATIVE_QUESTION_ID) < first_execution


def test_relative_performance_resolves_as_a_symmetric_offset() -> None:
    # Same environment; only the relative-performance answer is inverted. Winning
    # more should push μ up exactly as losing more pushes it down — relative is an
    # offset, never an absolute level of its own.
    engine = RacketSkillEngineV3()
    worse = dict(ESTABLISHED, **{RELATIVE_QUESTION_ID: "r0"})
    better = dict(ESTABLISHED, **{RELATIVE_QUESTION_ID: "r2"})
    even = dict(ESTABLISHED, **{RELATIVE_QUESTION_ID: "r1"})
    mu_worse = run(engine, Sport.PADEL, worse)[2].mu
    mu_even = run(engine, Sport.PADEL, even)[2].mu
    mu_better = run(engine, Sport.PADEL, better)[2].mu
    assert mu_worse < mu_even < mu_better


def test_every_routing_decision_records_a_reason_and_the_estimate() -> None:
    engine = RacketSkillEngineV3()
    for policy in (BEGINNER, DEVELOPING, ESTABLISHED, ADVANCED):
        asked, _, _ = run(engine, Sport.BADMINTON, policy)
        for step in asked:
            assert step.reason
            assert SCALE_MIN <= step.mu <= SCALE_MAX
            assert step.sigma > 0.0


# --- The question bank: reading order, word budget, jargon-free basics ---------

_JARGON = (
    "glass",
    "bandeja",
    "vibora",
    "topspin",
    "slice",
    "kick",
    "boast",
    "nick",
    "length",
    "smash",
    "clear",
    "drop shot",
    "shuttle",
    "back wall",
    "lob",
)


def test_every_question_leads_with_a_non_empty_situation() -> None:
    for sport in ALL_SPORTS:
        for question in all_questions_for(sport):
            assert question.situation.strip()
            assert question.text.strip()
            assert question.qualifier.strip()
            assert question.category.strip()


def test_no_question_body_exceeds_twenty_words_and_the_mean_is_under_fifteen() -> None:
    lengths: list[int] = []
    for sport in ALL_SPORTS:
        for question in all_questions_for(sport):
            words = len(question.text.split())
            assert words <= 20, f"{question.id} for {sport}: {words} words"
            lengths.append(words)
    assert sum(lengths) / len(lengths) < 15


def test_basic_execution_questions_use_no_sport_specific_jargon() -> None:
    for sport in ALL_SPORTS:
        for question in all_questions_for(sport):
            if question.tier != "basic":
                continue
            copy = f"{question.situation} {question.text}".lower()
            for term in _JARGON:
                assert term not in copy, f"{sport} basic question uses '{term}'"


def test_all_three_tiers_render_for_every_sport() -> None:
    for sport in ALL_SPORTS:
        tiers = {q.tier for q in all_questions_for(sport) if q.tier is not None}
        assert tiers == {"basic", "standard", "discriminating"}


def test_execution_options_are_identical_across_every_tier_and_sport() -> None:
    option_sets = set()
    for sport in ALL_SPORTS:
        for question in all_questions_for(sport):
            if question.tier is not None:
                option_sets.add(tuple((o.id, o.text) for o in question.options))
    assert len(option_sets) == 1  # the same five options everywhere


def test_doubles_and_singles_wording_matches_the_registry() -> None:
    # Padel and badminton (four players) speak of a partner; tennis and squash do
    # not, in their standard-tier execution question.
    for sport in ALL_SPORTS:
        standard = next(
            q
            for q in all_questions_for(sport)
            if q.id == EXECUTION_QUESTION_IDS["standard"]
        )
        text = f"{standard.situation} {standard.text}".lower()
        is_doubles = SPORT_SPECS[sport].players == 4
        assert ("partner" in text or "pair" in text) == is_doubles


# --- Properties: generated over random answer policies -------------------------


def test_random_policies_stay_in_bounds_and_below_the_ceiling() -> None:
    engine = RacketSkillEngineV3()
    rng = random.Random(20260813)
    option_pool: dict[str, list[str]] = {}
    for question in all_questions_for(Sport.PADEL):
        option_pool[question.id] = [o.id for o in question.options]

    for _ in range(400):
        sport = rng.choice(ALL_SPORTS)
        policy = {qid: rng.choice(options) for qid, options in option_pool.items()}
        asked, transcript, result = run(engine, sport, policy)
        assert len(transcript) <= MAX_QUESTIONS
        assert SCALE_MIN <= result.mu <= SCALE_MAX
        assert result.sigma >= SIGMA_FLOOR
        assert result.confidence <= 30  # nobody leaves onboarding above 30%
        assert result.band.lower <= result.mu <= result.band.upper or result.mu in (
            SCALE_MIN,
            SCALE_MAX,
        )
