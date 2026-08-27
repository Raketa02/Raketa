"""The matcher's outward demands, run against every implementation of each.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/matcher_demands.py`` is
enrolled here automatically, the null objects included, so registering a real
adapter either satisfies the demand or turns the build red. There is no skipped
test to go stale.

**This is ADR-0098's *contract suite*, and the directory is not called that on
purpose.** ``docs/environments.md`` already has a **Contract** tier and it means
``openapi.player.json`` drift — the thing ``make test-drift`` proves still fires.
Two suites called *contract*, one about what a client generates from and one
about what an unwritten context owes us, is how a green build starts being read
as the wrong assurance. These are the matcher's **demands**, which is the word
the register and ``MATCHER_DEMANDS`` already use.
"""

from __future__ import annotations

from dataclasses import fields
from inspect import signature
from datetime import datetime, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.matcher_demands import (
    REGISTERED_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import InvariantViolated, Sport, instant
from app.modules.matchmaking.domain.errors import GateDataUnavailable
from app.modules.matchmaking.domain.ports import (
    FAIL_POSTURE,
    MATCHER_DEMANDS,
    PAIRWISE_COUNTERPART_BOUND,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    ChallengeOrigin,
    FailPosture,
    MatchHistoryQuery,
    OpenChallenge,
    OutcomeTally,
    PairwiseCounterpart,
    PairwiseOutcome,
    PlayerScoreQuery,
    PlayerScoreReading,
    RatioStrand,
    SentFromSearch,
    SentOutsideASearch,
    SportsmanshipStrand,
)
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.users.domain.events import UserRegistered
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


# ---------------------------------------------------------------------------
# AccountHoldQuery — one live boolean per player, and nothing else
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_a_hold_read_answers_with_ids_the_caller_asked_about(
    implementation, session
):
    """The gate answers in ids, about the players it was handed, and stops.

    Both directions travel in one collection — the searcher's own id beside the
    candidates' — because ``docs/adr/0095`` points the hold both ways and asking
    once is what stops one direction being forgotten. Today nobody comes back,
    and that absence is measured rather than invented: nothing in this repository
    can open a case.
    """

    port = implementation.build(session)
    asked = (new_uuid(), new_uuid())

    held = await port.held_among(asked)

    assert held <= set(asked)


# ---------------------------------------------------------------------------
# AccountStatusQuery — the set of accounts that may not be shown
# ---------------------------------------------------------------------------
#
# The one port whose provider ships (``docs/adr/0124``), so the suite arranges a
# real world and asserts a real answer. The arrangement belongs to the **port**
# and not to any one implementation: one provider signs one contract, so the
# world an ``AccountStatusQuery`` answers about is ``users``' world whoever
# implements it, and a second implementation arriving tomorrow is held to the
# same two accounts without a line being written for it.


async def _register(session, *, nickname: str, is_active: bool):
    users = SqlAlchemyUserRepository(session)
    user_id = new_uuid()
    await users.project_registered(
        UserRegistered(
            user_id=user_id,
            email=f"{nickname}@example.com",
            nickname=nickname,
            password_hash="x" * 12,
            authority="USER",
            is_admin=False,
            is_active=is_active,
            occurred_at=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
            adult_attested=True,
        )
    )
    return user_id


@pytest.mark.parametrize("implementation", registered(AccountStatusQuery))
async def test_a_disabled_account_may_not_be_shown_and_an_active_one_may(
    implementation, session
):
    """A real provider, a real world, a real answer — and it discriminates.

    ``users`` ships ``is_active`` and ``auth`` already refuses a disabled account
    four ways; nothing in the matchmaking design had ever read it, so a disabled
    account kept its index row and stayed a candidate indefinitely. This is the
    test that says it no longer does.
    """

    port = implementation.build(session)
    playing = await _register(session, nickname="active", is_active=True)
    disabled = await _register(session, nickname="disabled", is_active=False)

    withheld = await port.may_not_be_shown([playing, disabled])

    assert withheld == frozenset({disabled})


@pytest.mark.parametrize("implementation", registered(AccountStatusQuery))
async def test_an_account_status_read_invents_nobody(implementation, session):
    """An id ``users`` has never heard of is not withheld and not asserted about.

    The gate asks *may this account be used*, and a stranger's id is not an
    answer to it. Withholding an unknown id would make a typo look like a
    disabled account; the search's own generation is what decides who is a
    candidate at all.
    """

    port = implementation.build(session)
    stranger = new_uuid()

    assert await port.may_not_be_shown([stranger]) == frozenset()


# ---------------------------------------------------------------------------
# PlayerScoreQuery — the six strands, separately, with their evidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_a_player_with_no_record_is_absent_and_never_a_zero(
    implementation, session
):
    """No record is not a bad record.

    A player without a score is not ``0.5`` and not ``0``: they are **absent**
    from the answer, the term returns ``NoEvidence`` and the surviving weights
    renormalise. Today that is every player, because nobody has failed to turn up
    — nobody has ever been *due* to.
    """

    port = implementation.build(session)
    unknown = (new_uuid(), new_uuid())

    readings = await port.readings_for(unknown)

    assert set(readings) == set()


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_a_score_read_answers_only_about_players_it_was_asked_about(
    implementation, session
):
    """One batched read per search, and it volunteers nobody."""

    port = implementation.build(session)
    asked = (new_uuid(), new_uuid())

    readings = await port.readings_for(asked)

    assert set(readings) <= set(asked)


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_every_strand_that_crosses_carries_its_own_evidence(
    implementation, session
):
    """The six are read separately, and each brings what it was measured from.

    Vacuous while ``player_score`` is unwritten and binding the day it is not:
    a strand arrives as its own published value with the numerator and
    denominator behind it and the moment it was last observed — or, for
    sportsmanship, as a mean and a rating count, because it is not a ratio.
    """

    port = implementation.build(session)

    readings = await port.readings_for([new_uuid()])

    for reading in readings.values():
        assert set(reading.strands) <= set(ReliabilityStrand)
        for strand, observation in reading.strands.items():
            expected = (
                SportsmanshipStrand
                if strand is ReliabilityStrand.SPORTSMANSHIP
                else RatioStrand
            )
            assert isinstance(observation, expected)


# ---------------------------------------------------------------------------
# MatchHistoryQuery — the pairwise read, the count, and the origin key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_the_pairwise_read_is_bounded_and_most_recent_first(
    implementation, session
):
    """500 counterparts, newest first, each one once.

    Load-bearing rather than tidy: it makes a counterpart truncated by the bound
    and one fully decayed by time **indistinguishable by construction**, which is
    what keeps familiarity's signed decay honest at the tail instead of reading a
    repetition-seeker's regular partner as a stranger.
    """

    port = implementation.build(session)

    counterparts = await port.pairwise_counterparts(new_uuid())

    assert len(counterparts) <= PAIRWISE_COUNTERPART_BOUND
    moments = [counterpart.last_at for counterpart in counterparts]
    assert moments == sorted(moments, reverse=True)
    seen = [counterpart.player_id for counterpart in counterparts]
    assert len(seen) == len(set(seen))


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_every_open_challenge_names_where_it_came_from(implementation, session):
    """The origin key is required, and there is no third answer.

    A search not joined to its outcome is evidence that no longer exists, there
    is no backfill, and the loss is permanent and silent — so the field is never
    optional and *somewhere else* is an explicit case rather than a missing
    value.
    """

    port = implementation.build(session)

    for challenge in await port.open_challenges(new_uuid()):
        assert isinstance(challenge.origin, ChallengeOrigin)


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_the_open_challenge_count_is_a_measured_zero_for_everybody_asked(
    implementation, session
):
    """Here a zero is real, and that is the difference from a Player Score.

    No challenge has ever been sent by anyone, so *nobody has an open challenge*
    is **true-over-empty** rather than absent: every player asked about gets a
    count, and today every count is a measured ``0``. A Player Score's ``0``
    would have been invented, so that port answers about nobody at all.
    """

    port = implementation.build(session)
    asked = (new_uuid(), new_uuid())

    counts = await port.open_challenge_counts(asked)

    assert dict(counts) == {player_id: 0 for player_id in asked}


# ---------------------------------------------------------------------------
# AtStakeQuery — what a counted result would do to the searcher's Level
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_against_an_unrated_pair_is_absent_and_never_zero(
    implementation, session
):
    """The card omits the block; it never prints a pair of zeros.

    Today that is every pair, because the rule that moves a Level on a result is
    not written. A zero would claim a counted game against this opponent moves
    the searcher's Level by nothing, which is false about every opponent — and
    that is the difference between an absence that was measured and one that was
    invented.
    """

    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.PADEL
    )

    assert at_stake is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_never_crosses_as_a_pair_that_changes_nothing(
    implementation, session
):
    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.TENNIS
    )

    assert at_stake is None or (at_stake.win_delta > 0 > at_stake.loss_delta)


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("port", MATCHER_DEMANDS, ids=lambda port: port.__name__)
def test_every_outward_demand_has_something_answering_it(port):
    """A port nothing implements is a demand nothing runs against.

    It arrives by omission rather than by anybody deciding it — which is exactly
    the shape of failure ``docs/adr/0098`` exists to prevent — so it is asked
    rather than watched for.

    **This is the test that stands under all the parameterised ones.** A port
    whose register row is deleted does not turn its own contract tests red: an
    empty ``parametrize`` collects as *skipped*, and a skipped test is a test
    nobody is watching. Driven against a register with a row removed, this one
    goes red while the two ``AtStakeQuery`` cases quietly skip — which is the
    demonstration, not a footnote.
    """

    assert implementations_of(port)


@pytest.mark.parametrize(
    "implementation",
    REGISTERED_IMPLEMENTATIONS,
    ids=[implementation.name for implementation in REGISTERED_IMPLEMENTATIONS],
)
async def test_a_registered_implementation_answers_the_port_it_registered_against(
    implementation, session
):
    """It implements the port it claims, and it is the class the row names.

    The row's name is what a failure above is reported under, so a row pointing
    at a builder that returns something else would blame the wrong class for a
    broken contract — and the register is exactly the kind of list that keeps its
    old label through a rename.
    """

    assert implementation.port in MATCHER_DEMANDS
    built = implementation.build(session)
    assert isinstance(built, implementation.port)
    assert type(built).__name__ == implementation.name


# ---------------------------------------------------------------------------
# The fail posture, per port
# ---------------------------------------------------------------------------


def test_every_port_says_how_it_fails():
    assert set(FAIL_POSTURE) == set(MATCHER_DEMANDS)


async def _unreadable():
    raise RuntimeError("the provider is down")


async def test_a_gate_that_cannot_be_evaluated_refuses_the_search():
    """A gate that cannot be evaluated excludes — so the whole search refuses.

    Blocks and holds, and the account-state gate beside them: there is no
    degraded answer to fall through to, because *nobody is held* and *we could
    not find out* are not the same sentence and must not become one.
    """

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountHoldQuery, _unreadable)

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountStatusQuery, _unreadable)


async def test_a_term_that_cannot_be_evaluated_stands_down_and_the_search_goes_on():
    """History and the pending-pair set fail soft, and the search proceeds.

    Losing a game because we could not remember who you played in March is a
    worse outcome than a slightly duller list, and §7.5's re-verify on the way
    out is the backstop under a duplicate proposal.
    """

    assert await read_demand(MatchHistoryQuery, _unreadable, stood_down=()) == ()
    assert await read_demand(PlayerScoreQuery, _unreadable, stood_down={}) == {}
    assert await read_demand(AtStakeQuery, _unreadable, stood_down=None) is None


async def test_a_gate_cannot_be_handed_a_degraded_answer_to_fall_through_to():
    """Offering a gate something to stand down to is refused at the call site.

    This is what makes the posture a property of the **port** rather than of
    whoever happened to write the call: a caller cannot quietly soften a gate by
    passing it a default, and a caller cannot forget to soften a term, because
    the same function reads both and refuses the mismatch either way.
    """

    with pytest.raises(InvariantViolated):
        await read_demand(AccountHoldQuery, _unreadable, stood_down=frozenset())

    with pytest.raises(InvariantViolated):
        await read_demand(MatchHistoryQuery, _unreadable)


def test_the_two_gates_fail_closed_and_the_three_terms_fail_soft():
    assert FAIL_POSTURE[AccountHoldQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[AccountStatusQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[MatchHistoryQuery] is FailPosture.SOFT
    assert FAIL_POSTURE[PlayerScoreQuery] is FailPosture.SOFT
    assert FAIL_POSTURE[AtStakeQuery] is FailPosture.SOFT


# ---------------------------------------------------------------------------
# The shapes, and what they make unwritable
# ---------------------------------------------------------------------------
#
# The tests above ask what an implementation *answers*. These ask what an
# implementation *can* answer, which is where the expensive mistakes are refused:
# a demand that is merely described is satisfiable by accident, and the whole
# return on ``docs/adr/0098`` is that the wrong thing cannot be built rather than
# that somebody notices it was.


def test_a_player_score_cannot_be_supplied_as_one_number():
    """The failure this contract is written against, refused at the type.

    The Player Score is one number in the UI, so the obvious thing for whoever
    builds ``player_score`` to ship is that number — at which point the
    strand-decomposition argument dies quietly and nobody finds out until
    somebody wires the term up. A reading has to carry strands; the published
    figure alone is not a reading, and there is nowhere to put a blend of the six
    in place of them.
    """

    with pytest.raises(InvariantViolated):
        PlayerScoreReading(strands={}, published_score=72)


def test_a_strand_cannot_cross_without_the_evidence_behind_it():
    """Value, numerator, denominator, last observation — none of them optional.

    A bare ``0–100`` cannot distinguish one no-show out of one game from
    thirty-five of thirty-eight, and it would make the absence rule a matter of
    trusting somebody else to send nothing rather than a zero.
    """

    with pytest.raises(TypeError):
        RatioStrand(value=80)  # no numerator, denominator or observation

    assert {field.name for field in fields(RatioStrand)} == {
        "value",
        "numerator",
        "denominator",
        "observed_at",
    }
    assert {field.name for field in fields(SportsmanshipStrand)} == {
        "mean",
        "rating_count",
        "observed_at",
    }


def test_a_hold_read_carries_nothing_that_could_be_scored():
    """Reading ``cases`` to score is impossible here rather than discouraged.

    One question, answered in player ids: no case, no opened-at, no severity, no
    count. *Settles up* is ``player_score``'s to publish from the historical
    record — the prototype computes it from the **live** open case, which
    conflates the strand with the gate. A held player is both excluded here and
    carrying a low *settles up*, and that double reach is intended.
    """

    members = {
        name
        for name, value in vars(AccountHoldQuery).items()
        if callable(value) and not name.startswith("_")
    }
    assert members == {"held_among"}
    assert get_type_hints(AccountHoldQuery.held_among)["return"] == frozenset[UUID]


def test_a_challenge_cannot_be_recorded_without_saying_where_it_came_from():
    """Never an optional field: there is no third answer and no missing one.

    The first caller who finds it inconvenient omits it, the loss is silent, and
    there is no backfill — a search not joined to its outcome is evidence that no
    longer exists.
    """

    with pytest.raises(TypeError):
        OpenChallenge(counterpart_id=new_uuid(), opened_at=None)

    assert ChallengeOrigin.__args__ == (SentFromSearch, SentOutsideASearch)


def test_a_counterpart_carries_both_halves_of_familiarity():
    """``strength`` reads *days since last* **and** *n games played together*.

    ``ranking-weights.md`` §8: ``0.5 ^ (days_since_last / HALF_LIFE) × (1 −
    DEPTH_PHI ⁿ)``. One outcome and one moment per person can supply the first
    and never the second, and a shape that cannot feed the modifier it exists for
    is a demand that was never really made. The counts also keep an accept
    visible under a later decline, which the previous-decline signal needs and a
    single latest-outcome would erase.
    """

    counterpart = PairwiseCounterpart(
        player_id=new_uuid(),
        outcomes={
            PairwiseOutcome.PLAYED: OutcomeTally(
                count=4, last_at=instant(datetime(2026, 6, 1, tzinfo=timezone.utc))
            ),
            PairwiseOutcome.DECLINED: OutcomeTally(
                count=1, last_at=instant(datetime(2026, 8, 1, tzinfo=timezone.utc))
            ),
        },
    )

    assert counterpart.games_played_together == 4
    assert counterpart.last_at == instant(
        datetime(2026, 8, 1, tzinfo=timezone.utc)
    )


def test_a_counterpart_with_nothing_between_you_is_not_a_counterpart():
    """Absence keeps one spelling: they are not in the list at all.

    *You have never played this person* is true of everyone, and a row saying so
    would make familiarity fire identically on every candidate — changing no
    ranking while printing a sentence on every card.
    """

    with pytest.raises(InvariantViolated):
        PairwiseCounterpart(player_id=new_uuid(), outcomes={})


def test_a_tally_counts_something_that_happened():
    with pytest.raises(InvariantViolated):
        OutcomeTally(
            count=0,
            last_at=instant(datetime(2026, 6, 1, tzinfo=timezone.utc)),
        )


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_late_is_one_published_threshold_and_never_a_per_case_judgement(
    implementation, session
):
    """*Keeps plans* has a denominator only if *late* means one thing.

    "One late change in six months" is prose in the prototype with no denominator
    behind it, and a per-case judgement is not a fact and cannot be contracted —
    so the contract demands ``matches`` publish **the single threshold**. The
    method takes no pair, no plan and no case, which is what makes a per-case
    judgement unexpressible rather than discouraged.

    ``None`` today: nothing schedules a plan, so there is no threshold to
    publish. It is absent rather than a number somebody would otherwise pick.
    """

    port = implementation.build(session)

    assert not signature(type(port).late_change_threshold).parameters.keys() - {"self"}
    assert await port.late_change_threshold() is None


def test_all_six_strands_cross_separately_and_keep_their_own_evidence():
    """Six readings in, six readings out, none of them averaged on the way.

    The subset check above says a reading may not invent a seventh strand; this
    says it can carry all six *at once* without them collapsing into each other —
    which is the half that would go wrong if somebody satisfied the shape by
    writing the same figure into every key. Each strand keeps the numerator and
    denominator it was measured from, and sportsmanship keeps a mean and a rating
    count because it is not a ratio.
    """

    observed = instant(datetime(2026, 8, 1, tzinfo=timezone.utc))
    ratios = {
        ReliabilityStrand.SHOWS_UP: (95, 38, 40),
        ReliabilityStrand.ANSWERS_CHALLENGES: (70, 14, 20),
        ReliabilityStrand.CONFIRMS_RESULTS: (100, 12, 12),
        ReliabilityStrand.KEEPS_PLANS: (83, 25, 30),
        ReliabilityStrand.SETTLES_UP: (50, 1, 2),
    }
    reading = PlayerScoreReading(
        strands={
            **{
                strand: RatioStrand(
                    value=value,
                    numerator=numerator,
                    denominator=denominator,
                    observed_at=observed,
                )
                for strand, (value, numerator, denominator) in ratios.items()
            },
            ReliabilityStrand.SPORTSMANSHIP: SportsmanshipStrand(
                mean=4.6,
                rating_count=9,
                observed_at=instant(datetime(2026, 7, 1, tzinfo=timezone.utc)),
            ),
        },
        published_score=84,
    )

    assert set(reading.strands) == set(ReliabilityStrand)
    for strand, (value, numerator, denominator) in ratios.items():
        observation = reading.strands[strand]
        assert (observation.value, observation.numerator, observation.denominator) == (
            value,
            numerator,
            denominator,
        )
    assert reading.strands[ReliabilityStrand.SPORTSMANSHIP].mean == 4.6
    assert reading.strands[ReliabilityStrand.SPORTSMANSHIP].rating_count == 9
    # The horizon reads one moment over the whole score, not six.
    assert reading.most_recent_observation == observed


def test_the_six_strands_are_the_platform_s_six():
    """The keys are the engine's closed vocabulary, not a second spelling of it.

    A reading keyed by a locally-declared enum would satisfy every other
    assertion here and still be a second copy of a closed vocabulary, free to
    drift — the failure ``tests/unit/test_social_tag_vocabulary.py`` refuses for
    the Social tags.
    """

    assert [strand.value for strand in ReliabilityStrand] == [
        "SHOWS_UP",
        "ANSWERS_CHALLENGES",
        "CONFIRMS_RESULTS",
        "KEEPS_PLANS",
        "SETTLES_UP",
        "SPORTSMANSHIP",
    ]


def test_a_strand_cannot_claim_more_good_outcomes_than_opportunities():
    with pytest.raises(InvariantViolated):
        RatioStrand(
            value=100,
            numerator=41,
            denominator=40,
            observed_at=instant(datetime(2026, 8, 1, tzinfo=timezone.utc)),
        )
