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

from datetime import datetime, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_skill_rating_repository,
)
from app.bootstrap.matcher_demands import (
    REGISTERED_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.racketskill.core import (
    STATUS_INITIAL_ESTIMATE,
    SkillEstimate,
    band_for,
    confidence_percent,
    likely_range,
)
from app.engines.racketskill.update_v1 import (
    information_share,
    one_side,
    rating_after,
)
from app.kernel import InvariantViolated, Sport
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.errors import GateDataUnavailable
from app.modules.matchmaking.domain.ports import (
    FAIL_POSTURE,
    MATCHER_DEMANDS,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    FailPosture,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
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


async def _register(session, *, handle: str, is_active: bool):
    users = SqlAlchemyUserRepository(session)
    user_id = new_uuid()
    await users.project_registered(
        UserRegistered(
            user_id=user_id,
            email=f"{handle}@example.com",
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
    playing = await _register(session, handle="active", is_active=True)
    disabled = await _register(session, handle="disabled", is_active=False)

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
# AtStakeQuery — what a counted result on a court would do to a player's Level
# ---------------------------------------------------------------------------


# **The provider ships and the rule exists** (``docs/adr/0139``), so these
# arrange a real world and assert a real answer — through ``rating``'s own
# aggregate, never through the adapter's insides. What is held to the contract
# is the *pair* a booked game's screen prints: signed, never zero, and the same
# pair the game will deliver if it is played. The head-to-head read a search
# card drew went with the searches (#579); a court is read side against side.


async def _rated(session, *, mu: float, sigma: float, sport: Sport = Sport.PADEL):
    """One player carrying a Level, written through the aggregate that owns it.

    Built from the initialised rating and then moved by nothing, because what
    these demands need is *a Level exists* rather than a plausible history — and
    a hand-built stream would be the adapter's own storage detail asserted back
    at it.
    """

    player_id = new_uuid()
    ratings = build_skill_rating_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await ratings.save(
        SkillRating.initialise(
            rating_id=skill_rating_id(player_id, sport),
            player_id=player_id,
            sport=sport,
            result=_an_assessment_result(mu=mu, sigma=sigma),
            source_assessment_id=new_uuid(),
            occurred_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    return player_id


def _an_assessment_result(*, mu: float, sigma: float) -> AssessmentResult:
    band = band_for(mu)
    low, high = likely_range(mu, sigma)
    return AssessmentResult(
        mu=mu,
        sigma=sigma,
        confidence=confidence_percent(sigma),
        range_low=round(low, 2),
        range_high=round(high, 2),
        band=BandView(name=band.label, lower=band.lower, upper=band.upper),
        status=STATUS_INITIAL_ESTIMATE,
        questions_asked=7,
        engine_version="racketskill-fusion-v3",
        confidence_ceiling=confidence_percent(sigma),
    )


async def _singles(port, me, them, *, sport: Sport = Sport.PADEL):
    return await port.counted_game_deltas_on_court(
        player_id=me, own_side=[me], opposing_side=[them], sport=sport
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_on_an_unrated_court_is_absent_and_never_zero(
    implementation, session
):
    """The screen omits the block; it never prints a pair of zeros.

    A court with no Level on it is *we have nothing to price this against*, and
    that is the difference between an absence that was measured and one that
    was invented.
    """

    port = implementation.build(session)

    assert await _singles(port, new_uuid(), new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_one_side_rated_is_still_no_answer(implementation, session):
    """Half a pairing prices nothing, and the absence has one spelling."""

    port = implementation.build(session)
    rated = await _rated(session, mu=3.00, sigma=0.30)

    assert await _singles(port, rated, new_uuid()) is None
    assert await _singles(port, new_uuid(), rated) is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_a_court_of_two_is_priced_as_the_update_will_move_it(
    implementation, session
):
    """The demand this port was written for: a real answer, both ways signed,
    and **the pair ``rating_after`` will move by** — in singles a side is one
    person, so the court read is the rule's own head-to-head."""

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.TENNIS)
    them = await _rated(session, mu=3.40, sigma=0.25, sport=Sport.TENNIS)

    on_court = await _singles(port, me, them, sport=Sport.TENNIS)
    moved = rating_after(
        player=SkillEstimate(mu=3.00, sigma=0.30),
        opposition=one_side([SkillEstimate(3.40, 0.25)]),
        won=True,
        results_so_far=0,
        share=information_share(Sport.TENNIS),
        own_side=one_side([SkillEstimate(3.00, 0.30)]),
    )

    assert on_court is not None
    assert on_court.win_delta > 0 > on_court.loss_delta
    assert (on_court.win_delta, on_court.loss_delta) == (
        moved.stakes.win,
        moved.stakes.loss,
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_beating_somebody_above_you_is_worth_more_than_beating_an_equal(
    implementation, session
):
    """A shape demand and not a value one.

    The numbers are the rule's and are held to ``tests/unit/`` against hand-worked
    pairings; what the *contract* owes is that the block a player reads is about
    the court beside it. A port answering one figure for everybody would satisfy
    every other demand here.
    """

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30)
    equal = await _rated(session, mu=3.00, sigma=0.30)
    stronger = await _rated(session, mu=4.00, sigma=0.30)

    against_equal = await _singles(port, me, equal)
    against_stronger = await _singles(port, me, stronger)

    assert against_stronger.win_delta > against_equal.win_delta
    assert against_stronger.loss_delta > against_equal.loss_delta


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_is_asked_about_a_sport_and_answers_about_that_one(
    implementation, session
):
    """A Level is per ``(player, sport)``, and a padel court prices no tennis."""

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    them = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)

    assert await _singles(port, me, them, sport=Sport.PADEL) is not None
    assert await _singles(port, me, them, sport=Sport.TENNIS) is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_a_four_is_priced_side_against_side_and_partners_share_the_pair(
    implementation, session
):
    """**Both partners move by the same amount**, because a result is a statement
    about one pair against another (``rule.py``'s ``one_side``) — and the pair
    is **the one ``rating_after`` will move by**, which is the whole of what *at
    stake* promises: not a preview of the rule but the rule, read forward.

    It is held against the engine's own entry point, because the step is priced
    from the **side's** uncertainty and the side's Level, and a screen printing a
    head-to-head figure would be contradicted by the update.
    """

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    partner = await _rated(session, mu=2.00, sigma=0.30, sport=Sport.PADEL)
    left = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    right = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)

    mine = await port.counted_game_deltas_on_court(
        player_id=me, own_side=[me, partner], opposing_side=[left, right],
        sport=Sport.PADEL,
    )
    theirs = await port.counted_game_deltas_on_court(
        player_id=partner, own_side=[partner, me], opposing_side=[right, left],
        sport=Sport.PADEL,
    )
    moved = rating_after(
        player=SkillEstimate(mu=3.00, sigma=0.30),
        opposition=one_side([SkillEstimate(3.00, 0.30), SkillEstimate(3.00, 0.30)]),
        won=True,
        results_so_far=0,
        share=information_share(Sport.PADEL),
        own_side=one_side([SkillEstimate(3.00, 0.30), SkillEstimate(2.00, 0.30)]),
    )

    assert mine is not None
    assert mine == theirs
    assert (mine.win_delta, mine.loss_delta) == (moved.stakes.win, moved.stakes.loss)


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_a_side_nobody_on_is_rated_prices_nothing_and_so_does_an_unrated_reader(
    implementation, session
):
    """The two absences, and they are the update's own: *there is nothing to
    price the other side against* when a whole side holds no Level, and nothing
    to move when the reader holds none."""

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    partner = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    stranger = new_uuid()

    assert (
        await port.counted_game_deltas_on_court(
            player_id=me,
            own_side=[me, partner],
            opposing_side=[new_uuid(), new_uuid()],
            sport=Sport.PADEL,
        )
        is None
    )
    assert (
        await port.counted_game_deltas_on_court(
            player_id=stranger,
            own_side=[stranger, partner],
            opposing_side=[me, new_uuid()],
            sport=Sport.PADEL,
        )
        is None
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_an_unrated_seat_beside_a_rated_one_is_priced_as_the_update_prices_it(
    implementation, session
):
    """**Not an absence, because the rule prices it.** ``settle_results`` folds
    a side over the people on it who hold a rating and moves the rated ones, so
    a court with one unrated opponent is priced against the rated opponent
    alone — and a figure that omitted this case would be a preview and not the
    rule."""

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    partner = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    left = await _rated(session, mu=3.40, sigma=0.25, sport=Sport.PADEL)

    on_court = await port.counted_game_deltas_on_court(
        player_id=me,
        own_side=[me, partner],
        opposing_side=[left, new_uuid()],
        sport=Sport.PADEL,
    )
    moved = rating_after(
        player=SkillEstimate(mu=3.00, sigma=0.30),
        opposition=one_side([SkillEstimate(3.40, 0.25)]),
        won=True,
        results_so_far=0,
        share=information_share(Sport.PADEL),
        own_side=one_side([SkillEstimate(3.00, 0.30), SkillEstimate(3.00, 0.30)]),
    )

    assert on_court is not None
    assert (on_court.win_delta, on_court.loss_delta) == (
        moved.stakes.win,
        moved.stakes.loss,
    )


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


async def test_a_gate_that_cannot_be_evaluated_refuses_the_read():
    """A gate that cannot be evaluated excludes — so the whole read refuses.

    Holds, and the account-state gate beside them: there is no degraded answer
    to fall through to, because *nobody is held* and *we could not find out* are
    not the same sentence and must not become one.
    """

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountHoldQuery, _unreadable)

    with pytest.raises(GateDataUnavailable):
        await read_demand(AccountStatusQuery, _unreadable)


async def test_an_at_stake_read_that_cannot_be_evaluated_stands_down():
    """The block is simply not drawn, and the game screen is still served."""

    assert await read_demand(AtStakeQuery, _unreadable, stood_down=None) is None


async def test_a_gate_cannot_be_handed_a_degraded_answer_to_fall_through_to():
    """Offering a gate something to stand down to is refused at the call site.

    This is what makes the posture a property of the **port** rather than of
    whoever happened to write the call: a caller cannot quietly soften a gate by
    passing it a default, and a caller cannot forget to soften a soft read,
    because the same function reads both and refuses the mismatch either way.
    """

    with pytest.raises(InvariantViolated):
        await read_demand(AccountHoldQuery, _unreadable, stood_down=frozenset())

    with pytest.raises(InvariantViolated):
        await read_demand(AtStakeQuery, _unreadable)


def test_the_two_gates_fail_closed_and_the_at_stake_read_fails_soft():
    assert FAIL_POSTURE[AccountHoldQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[AccountStatusQuery] is FailPosture.CLOSED
    assert FAIL_POSTURE[AtStakeQuery] is FailPosture.SOFT


# ---------------------------------------------------------------------------
# The shapes, and what they make unwritable
# ---------------------------------------------------------------------------


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
