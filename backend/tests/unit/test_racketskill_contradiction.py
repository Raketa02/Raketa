"""Contradiction detection, the tie-breaker, and how a disagreement resolves.

Exercised through ``next_step`` and ``finalize`` only, like the rest of the
engine tests. A **claim** is a statement about standing — how much you play,
what you compete in, how you do against your usual group. A **demonstration** is
a statement about what happens inside a point. A **contradiction** is a gap
beyond tolerance between the two fused sides.

The load-bearing behaviours here are the ones a constant retune must not break:
a real disagreement is noticed and an uneven profile is not, the tie-breaker is
asked once at the level the *claims* imply, and an unresolved disagreement costs
precision without a direction — inverted, it costs exactly the same. The
specific μ/σ values are hypotheses, like the golden personas, and are asserted
relationally wherever the shape rather than the digit is the point.
"""

from app.engines.assessment import (
    CALIBRATION_PRIORITY_ELEVATED,
    CALIBRATION_PRIORITY_STANDARD,
    AnsweredQuestion,
    AskQuestion,
    AssessmentResult,
    Complete,
)
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.engines.racketskill.v3.engine import (
    CONFIDENCE_REASON_CONTRADICTION,
    CONFIDENCE_REASON_LIMITED_EVIDENCE,
    CONFIDENCE_SENTENCES,
    CONTRADICTION_EXTRA_QUESTIONS,
    CONTRADICTION_SENTENCE,
    MAX_QUESTIONS,
    STOP_CEILING,
    TIE_BREAKER_REASON,
    _contradiction,
    _evidence_points,
    _target_tier,
)
from app.engines.racketskill.v3.questions import (
    ENVIRONMENT_QUESTION_ID,
    EXECUTION_QUESTION_IDS,
    LAYOFF_QUESTION_ID,
    OPENING_QUESTION_ID,
    RELATIVE_QUESTION_ID,
    TACTICAL_QUESTION_IDS,
    TIER_DISCRIMINATING,
    VOLUME_QUESTION_ID,
)
from app.kernel import Sport

SPORT = Sport.PADEL


def answers(*pairs: tuple[str, str]) -> tuple[AnsweredQuestion, ...]:
    return tuple(AnsweredQuestion(qid, option) for qid, option in pairs)


def finalize(*pairs: tuple[str, str]) -> AssessmentResult:
    return RacketSkillEngineV3().finalize(sport=SPORT, transcript=answers(*pairs))


def not_a_disagreement(result: AssessmentResult) -> bool:
    """Nothing about the result says the player's answers disagreed.

    Every rating carries a confidence sentence now, so "no disagreement" is the
    base branch — we have not seen you play yet — rather than an absent one.
    """

    assert result.confidence_reason is not None
    return result.confidence_reason.key == CONFIDENCE_REASON_LIMITED_EVIDENCE


def run(policy: dict[str, str], sport: Sport = SPORT):
    """Run a scripted answer policy to completion, as the routing tests do."""

    engine = RacketSkillEngineV3()
    transcript: list[AnsweredQuestion] = []
    asked: list[AskQuestion] = []
    while True:
        step = engine.next_step(sport=sport, transcript=tuple(transcript))
        if isinstance(step, Complete):
            break
        asked.append(step)
        transcript.append(AnsweredQuestion(step.question.id, policy[step.question.id]))
        assert len(transcript) <= MAX_QUESTIONS + CONTRADICTION_EXTRA_QUESTIONS
    result = engine.finalize(sport=sport, transcript=tuple(transcript))
    return asked, tuple(transcript), result


# Claims a player makes about their standing, and what they then demonstrate
# inside a point. The three claim answers alone decide which side of the
# tolerance a persona lands on; the two demonstrations are held fixed.
BASIC = EXECUTION_QUESTION_IDS["basic"]
STANDARD = EXECUTION_QUESTION_IDS["standard"]
DISCRIMINATING = EXECUTION_QUESTION_IDS["discriminating"]

WEAK_DEMONSTRATIONS = ((BASIC, "e0"), (STANDARD, "e0"))
STRONG_DEMONSTRATIONS = ((BASIC, "e4"), (STANDARD, "e4"))


# --- Detection: what is a disagreement and what is merely an uneven game -------


def test_a_gap_beyond_tolerance_between_the_two_sides_is_detected() -> None:
    # Competes in leagues and wins almost every time, but cannot keep an easy
    # rally going: the two sides are not describing the same player.
    result = finalize(
        (OPENING_QUESTION_ID, "frequent"),
        (ENVIRONMENT_QUESTION_ID, "env3"),
        (RELATIVE_QUESTION_ID, "r3"),
        *WEAK_DEMONSTRATIONS,
    )
    assert result.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
    assert result.confidence_reason is not None
    assert result.confidence_reason.key == CONFIDENCE_REASON_CONTRADICTION


def test_answers_that_hang_together_are_not_reported_as_a_disagreement() -> None:
    result = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env0"),
        (RELATIVE_QUESTION_ID, "r1"),
        (BASIC, "e2"),
        (STANDARD, "e2"),
    )
    assert result.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert not_a_disagreement(result)


def test_a_gap_within_tolerance_is_not_reported_as_a_disagreement() -> None:
    # A real gap — the claims sit above the demonstrations — but a small one, so
    # it is read as imprecision rather than as two different stories.
    result = finalize(
        (OPENING_QUESTION_ID, "regular"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r1"),
        (BASIC, "e1"),
        (STANDARD, "e1"),
    )
    assert result.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert not_a_disagreement(result)


def test_an_uneven_profile_widens_the_range_without_an_accusation() -> None:
    # Two players at the same Level, with the same claims. One is even across
    # the tiers; the other cannot hold an easy rally but handles the hardest
    # ball in the bank. The uneven game earns a wider range through dispersion —
    # never a disagreement, because it is not one.
    claims = (
        (OPENING_QUESTION_ID, "regular"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r1"),
    )
    uneven = finalize(*claims, (BASIC, "e0"), (DISCRIMINATING, "e4"))
    even = finalize(*claims, (BASIC, "e4"), (DISCRIMINATING, "e1"))

    assert uneven.mu == even.mu  # the same Level, to the digit
    assert uneven.sigma > even.sigma
    assert uneven.range_high - uneven.range_low > even.range_high - even.range_low
    for result in (uneven, even):
        assert result.calibration_priority == CALIBRATION_PRIORITY_STANDARD
        assert not_a_disagreement(result)


# --- The tie-breaker ------------------------------------------------------------

# Claims a player who plays several times a week, demonstrated at the bottom of
# the bank. The demonstrations drag the running estimate back under the
# Established floor, so only two are required — which leaves the tier the
# *claims* imply unasked when the disagreement is noticed, and it is the
# tie-breaker.
#
# That "only two are required" is the load-bearing half of this fixture, and it
# is why the tie-breaker exists at all: a third demonstration would be asked at
# one of the three tiers, and with three tiers in the bank a player who earns
# three has necessarily been asked the claims' own tier already. See
# ``STRONG_OVER_CLAIMER`` below for that player, who is the commoner one.
OVER_CLAIMER = {
    OPENING_QUESTION_ID: "frequent",
    VOLUME_QUESTION_ID: "v0",
    LAYOFF_QUESTION_ID: "l0",
    ENVIRONMENT_QUESTION_ID: "env0",
    RELATIVE_QUESTION_ID: "r1",
    BASIC: "e0",
    STANDARD: "e0",
    DISCRIMINATING: "e0",
    TACTICAL_QUESTION_IDS[0]: "t0",
    TACTICAL_QUESTION_IDS[1]: "t0",
}

# The same disagreement in a player whose demonstrations stay inside Established.
# They earn a third demonstration, the routing spends it on the discriminating
# tier, and so the claims are tested at their own level *by the sequence* — one
# question earlier than a tie-breaker would have done it, and with the same
# question.
STRONG_OVER_CLAIMER = {
    OPENING_QUESTION_ID: "regular",
    VOLUME_QUESTION_ID: "v2",
    LAYOFF_QUESTION_ID: "l0",
    ENVIRONMENT_QUESTION_ID: "env2",
    RELATIVE_QUESTION_ID: "r2",
    BASIC: "e1",
    STANDARD: "e0",
    DISCRIMINATING: "e0",
    TACTICAL_QUESTION_IDS[0]: "t0",
    TACTICAL_QUESTION_IDS[1]: "t0",
}


def tie_breakers(asked: list[AskQuestion]) -> list[AskQuestion]:
    return [step for step in asked if step.reason == TIE_BREAKER_REASON]


def claims_tier(transcript: tuple[AnsweredQuestion, ...]) -> str | None:
    """The tier this transcript's fused claims imply, or ``None`` if they agree."""

    sides = _contradiction(_evidence_points(transcript))
    return None if sides is None else _target_tier(sides.claims.mu)


def test_the_tie_breaker_is_asked_once_at_the_tier_the_claims_imply() -> None:
    asked, transcript, _ = run(OVER_CLAIMER)
    breakers = tie_breakers(asked)
    assert len(breakers) == 1
    # The claims describe an Established player, so the claims are tested with
    # the hardest question in the bank — not with the tier the (lower) running
    # estimate would have chosen.
    assert breakers[0].question.tier == TIER_DISCRIMINATING
    assert claims_tier(transcript) == TIER_DISCRIMINATING


def test_passing_the_tie_breaker_settles_the_disagreement() -> None:
    # Identical answers but for the tie-breaker itself: the player who does the
    # thing their claims imply leaves with their claims intact; the one who does
    # not leaves with a wider range and a raised calibration priority.
    passed_asked, _, passed = run(dict(OVER_CLAIMER, **{DISCRIMINATING: "e4"}))
    failed_asked, _, failed = run(OVER_CLAIMER)

    assert len(tie_breakers(passed_asked)) == 1
    assert len(tie_breakers(failed_asked)) == 1
    assert passed.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert not_a_disagreement(passed)
    assert failed.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
    assert failed.confidence_reason is not None


def test_a_third_demonstration_tests_the_claims_instead_of_a_tie_breaker() -> None:
    """The other way the claims get tested at their own level, and the commoner one.

    A player whose demonstrations keep the estimate inside Established earns a
    third demonstration, and with three tiers in the bank that spends the claims'
    own tier. No extra question is earned — and none is needed, because the
    question a tie-breaker would have asked has already been answered.

    The disagreement is still reported: what the tie-breaker buys is a chance to
    settle it, not the noticing of it.
    """

    asked, transcript, failed = run(STRONG_OVER_CLAIMER)

    assert tie_breakers(asked) == []
    assert claims_tier(transcript) == TIER_DISCRIMINATING
    # …and that tier was asked anyway, as a routed demonstration.
    demonstrations = [
        step
        for step in asked
        if step.reason == f"demonstration-{TIER_DISCRIMINATING}"
        and step.question.tier == TIER_DISCRIMINATING
    ]
    assert len(demonstrations) == 1
    assert failed.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
    assert not not_a_disagreement(failed)

    # Doing the thing the claims imply settles it here too, with no tie-breaker.
    _, _, passed = run(dict(STRONG_OVER_CLAIMER, **{DISCRIMINATING: "e4"}))
    assert passed.calibration_priority == CALIBRATION_PRIORITY_STANDARD
    assert not_a_disagreement(passed)


def test_a_disagreement_permits_exactly_one_question_beyond_the_ceiling() -> None:
    # Nine answers, every one of them recorded, and the claims' own tier still
    # unasked. The ceiling gives way for the tie-breaker and for nothing else:
    # the tenth question is the tie-breaker, and there is no eleventh.
    #
    # The claims come last here, which the sequence itself would never do — it
    # asks them first. That is the point: no *routed* transcript reaches the
    # ceiling with the claims' own tier still unasked, so this is the guard
    # being tested rather than the path, on a transcript the engine must handle
    # because a replayed stream is the only thing it is ever given.
    #
    # The regularity claim is modest deliberately. The minimums have to be *met*
    # for a tie-breaker to be due, and a stronger claim here lifts the fused
    # estimate over the Established floor, which asks for a third demonstration
    # this transcript does not have — so the guard would never be reached.
    engine = RacketSkillEngineV3()
    at_the_ceiling = answers(
        (BASIC, "e0"),
        (STANDARD, "e0"),
        (TACTICAL_QUESTION_IDS[0], "t0"),
        (TACTICAL_QUESTION_IDS[1], "t0"),
        (LAYOFF_QUESTION_ID, "l0"),
        (OPENING_QUESTION_ID, "tried-a-few-times"),
        (VOLUME_QUESTION_ID, "v3"),
        (ENVIRONMENT_QUESTION_ID, "env3"),
        (RELATIVE_QUESTION_ID, "r3"),
    )
    assert len(at_the_ceiling) == MAX_QUESTIONS

    step = engine.next_step(sport=SPORT, transcript=at_the_ceiling)
    assert isinstance(step, AskQuestion)
    assert step.reason == TIE_BREAKER_REASON
    assert step.question.tier == TIER_DISCRIMINATING

    answered = at_the_ceiling + answers((step.question.id, "e0"))
    stop = engine.next_step(sport=SPORT, transcript=answered)
    assert isinstance(stop, Complete)
    assert stop.reason == STOP_CEILING
    assert len(answered) == MAX_QUESTIONS + CONTRADICTION_EXTRA_QUESTIONS


def test_a_settled_disagreement_does_not_buy_a_second_tie_breaker() -> None:
    # The disagreement survives the tie-breaker here, and still earns only one:
    # the run's length is capped by the same single extra question either way.
    for policy in (
        OVER_CLAIMER,
        dict(OVER_CLAIMER, **{DISCRIMINATING: "e4"}),
        STRONG_OVER_CLAIMER,
        dict(STRONG_OVER_CLAIMER, **{DISCRIMINATING: "e4"}),
    ):
        asked, transcript, _ = run(policy)
        assert len(tie_breakers(asked)) <= 1
        assert len(transcript) <= MAX_QUESTIONS + CONTRADICTION_EXTRA_QUESTIONS


# --- How an unresolved disagreement resolves ------------------------------------


def test_an_unresolved_disagreement_widens_sigma_in_proportion_to_the_gap() -> None:
    # The same demonstrations and the same answer *structure* throughout, so
    # only the size of the disagreement differs.
    none = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env0"),
        (RELATIVE_QUESTION_ID, "r1"),
        (BASIC, "e2"),
        (STANDARD, "e2"),
    )
    small = finalize(
        (OPENING_QUESTION_ID, "regular"),
        (ENVIRONMENT_QUESTION_ID, "env2"),
        (RELATIVE_QUESTION_ID, "r1"),
        *WEAK_DEMONSTRATIONS,
    )
    large = finalize(
        (OPENING_QUESTION_ID, "frequent"),
        (ENVIRONMENT_QUESTION_ID, "env3"),
        (RELATIVE_QUESTION_ID, "r3"),
        *WEAK_DEMONSTRATIONS,
    )
    assert none.sigma < small.sigma < large.sigma
    assert none.confidence > small.confidence > large.confidence
    assert small.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
    assert large.calibration_priority == CALIBRATION_PRIORITY_ELEVATED


def test_claiming_further_from_the_demonstrations_stops_paying() -> None:
    # The claim rises by one answer, crossing the tolerance. The Level does not
    # follow it up: past the crossing the claims keep only part of their
    # precision, so a bigger claim buys a *lower* Level and a wider range.
    within = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r1"),
        *WEAK_DEMONSTRATIONS,
    )
    beyond = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r2"),  # the same claim, one notch higher
        *WEAK_DEMONSTRATIONS,
    )
    assert beyond.mu < within.mu
    assert beyond.sigma > within.sigma


def test_claiming_further_below_the_demonstrations_stops_paying_too() -> None:
    # The mirror, and the whole anti-sandbagging design: under-reporting past
    # the tolerance buys a *higher* Level and a wider range, exactly as
    # over-reporting buys a lower one. Resolution has no direction to exploit.
    within = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r1"),
        *STRONG_DEMONSTRATIONS,
    )
    beyond = finalize(
        (OPENING_QUESTION_ID, "tried-a-few-times"),  # the same claim, lower
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r3"),
        *STRONG_DEMONSTRATIONS,
    )
    assert beyond.mu > within.mu
    assert beyond.sigma > within.sigma


def test_the_same_gap_inverted_costs_exactly_the_same() -> None:
    # Two players disagreeing with themselves by the same amount, in opposite
    # directions. Everything the disagreement costs — precision, confidence,
    # calibration priority, the sentence — is identical, because the resolution
    # reads the size of the gap and never its sign.
    over = finalize(
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r2"),
        *WEAK_DEMONSTRATIONS,
    )
    under = finalize(
        (OPENING_QUESTION_ID, "tried-a-few-times"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r3"),
        *STRONG_DEMONSTRATIONS,
    )
    assert over.sigma == under.sigma
    assert over.confidence == under.confidence
    assert over.calibration_priority == under.calibration_priority
    assert over.confidence_reason == under.confidence_reason


def test_the_estimate_is_never_moved_outside_the_evidence() -> None:
    # Resolution re-weights evidence; it never applies a penalty in a direction.
    # The Level therefore stays between what the claims alone say and what the
    # demonstrations alone say — nobody is moved up, and nobody is moved down.
    over_claims = (
        (OPENING_QUESTION_ID, "occasional"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r2"),
    )
    under_claims = (
        (OPENING_QUESTION_ID, "tried-a-few-times"),
        (ENVIRONMENT_QUESTION_ID, "env1"),
        (RELATIVE_QUESTION_ID, "r3"),
    )
    for claims, demonstrations in (
        (over_claims, WEAK_DEMONSTRATIONS),
        (under_claims, STRONG_DEMONSTRATIONS),
    ):
        result = finalize(*claims, *demonstrations)
        claims_alone = finalize(*claims)
        demonstrations_alone = finalize(*demonstrations)
        assert result.calibration_priority == CALIBRATION_PRIORITY_ELEVATED
        low = min(claims_alone.mu, demonstrations_alone.mu)
        high = max(claims_alone.mu, demonstrations_alone.mu)
        assert low <= result.mu <= high


def test_the_copy_never_accuses_the_player() -> None:
    result = finalize(
        (OPENING_QUESTION_ID, "frequent"),
        (ENVIRONMENT_QUESTION_ID, "env3"),
        (RELATIVE_QUESTION_ID, "r3"),
        *WEAK_DEMONSTRATIONS,
    )
    assert result.confidence_reason is not None
    assert result.confidence_reason.sentence == CONTRADICTION_SENTENCE
    # Every branch, not only this one: a sentence the player never sees today is
    # a sentence nobody re-reads before the branch that shows it goes live.
    for sentence in CONFIDENCE_SENTENCES.values():
        assert_does_not_accuse(sentence)


def assert_does_not_accuse(sentence: str) -> None:
    for accusation in (
        "inconsistent",
        "contradict",
        "disagree with",
        "wrong",
        "incorrect",
        "honest",
        "accurate",
        "overestimat",
        "underestimat",
        "you claimed",
    ):
        assert accusation not in sentence.lower()
