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
from datetime import datetime, timedelta, timezone
from typing import get_type_hints
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
    build_skill_rating_repository,
)
from app.bootstrap.matcher_demands import (
    REGISTERED_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.assessment import AssessmentResult, BandView
from app.engines.matchfit.core import ReliabilityStrand
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
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.matchmaking.domain.errors import GateDataUnavailable
from app.modules.matchmaking.domain.ports import (
    FAIL_POSTURE,
    MATCHER_DEMANDS,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    ChallengeOrigin,
    FailPosture,
    HalfBuiltCourtQuery,
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
    SharedCourt,
    SharedCourtQuery,
    SportsmanshipStrand,
)
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import entry_closes_at
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.player_profile.domain.weekly_hours import Window
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
# PlayerScoreQuery — the six strands, separately, with their evidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PlayerScoreQuery))
async def test_a_player_with_no_record_is_absent_and_never_a_zero(
    implementation, session
):
    """No record is not a bad record.

    A player without a score is not ``0.5`` and not ``0``: they are **absent**
    from the answer, the term returns ``NoEvidence`` and the surviving weights
    renormalise. It used to be every player and no longer is (``docs/adr/0140``),
    which is what makes this the assertion it was written to be: two ids nothing
    has ever arranged anything for, put to a provider that can now answer about
    somebody.
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

    **No longer vacuous**: ``player_score`` ships and answers three of the six
    for anybody with a record (``docs/adr/0140``, ``docs/adr/0160``). It stays
    written over whatever arrives rather than over the three, because the shape
    is the demand — a strand
    is its own published value with the numerator and denominator behind it and
    the moment it was last observed, or, for sportsmanship, a mean and a rating
    count, because it is not a ratio.

    Asked about a stranger, so what it proves here is that a provider with a real
    database behind it still answers about nobody rather than inventing a row.
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
#
# **One provider since #578.** ``games`` answers the pairwise read; the challenge
# half — ``ACCEPTED`` and ``DECLINED``, the open-challenge set and the load count
# — went with the challenges, and what is left of it is a **measured absence**:
# nothing sends a challenge, so none is open and nobody's inbox holds one. The
# arrangement is real games through the ``Game`` aggregate and never an
# ``INSERT`` (``docs/adr/0029``); the helpers are the shared-court block's below.


def _ago(**offset) -> Instant:
    return instant(datetime.now(timezone.utc) - timedelta(**offset))


def _counterparts(rows) -> set[UUID]:
    return {row.counterpart_id for row in rows}


def _by_player(counterparts) -> dict[UUID, dict]:
    return {row.player_id: row.outcomes for row in counterparts}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_no_challenge_is_open_and_every_inbox_is_a_measured_zero(
    implementation, session
):
    """Nothing sends a challenge since #578, so nobody is arranging anything
    with anybody — and **every player asked about gets a count**, a zero that
    was measured rather than invented."""

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    game = _a_game(line_up=_singles(one, other), planned_at=_ago(days=3))
    game.state_result(by=one, score=_a_score(), occurred_at=_ago(days=2))
    await _saved(session, game)

    assert await port.open_challenges(one) == ()
    assert await port.open_challenges(other) == ()
    assert await port.open_challenge_counts([one, other]) == {one: 0, other: 0}


@pytest.mark.parametrize("implementation", registered(MatchHistoryQuery))
async def test_a_played_game_is_tallied_for_both_and_newest_first(
    implementation, session
):
    """``PLAYED`` is ``games``' fact, read for each side of the net, and the
    rows come newest first — the order is the bound's meaning."""

    port = implementation.build(session)
    me, older, newer = new_uuid(), new_uuid(), new_uuid()
    for them, days in ((older, 9), (newer, 3)):
        game = _a_game(line_up=_singles(me, them), planned_at=_ago(days=days + 1))
        game.state_result(by=me, score=_a_score(), occurred_at=_ago(days=days))
        await _saved(session, game)

    rows = await port.pairwise_counterparts(me)

    assert [row.player_id for row in rows] == [newer, older]
    tallied = _by_player(rows)
    assert tallied[newer][PairwiseOutcome.PLAYED].count == 1
    assert PairwiseOutcome.ACCEPTED not in tallied[newer]
    assert _by_player(await port.pairwise_counterparts(newer)).keys() == {me}


# ---------------------------------------------------------------------------
# AtStakeQuery — what a counted result would do to the searcher's Level
# ---------------------------------------------------------------------------


# **The provider ships and the rule exists** (``docs/adr/0139``), so these
# arrange a real world and assert a real answer — through ``rating``'s own
# aggregate, never through the adapter's insides. What is being held to the
# contract is the *pair*: signed, never zero, and the same pair the game will
# deliver if it is played.


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


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_against_an_unrated_pair_is_absent_and_never_zero(
    implementation, session
):
    """The card omits the block; it never prints a pair of zeros.

    A pair with no Level between them is *we have nothing to price this
    against*, and that is the difference between an absence that was measured
    and one that was invented.
    """

    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.PADEL
    )

    assert at_stake is None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_one_side_rated_is_still_no_answer(implementation, session):
    """Half a pairing prices nothing, and the absence has one spelling."""

    port = implementation.build(session)
    rated = await _rated(session, mu=3.00, sigma=0.30)

    assert (
        await port.counted_game_deltas(
            searcher_id=rated, opponent_id=new_uuid(), sport=Sport.PADEL
        )
        is None
    )
    assert (
        await port.counted_game_deltas(
            searcher_id=new_uuid(), opponent_id=rated, sport=Sport.PADEL
        )
        is None
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_two_rated_players_are_priced_and_the_pair_is_signed(
    implementation, session
):
    """The demand this port was written for: a real answer, both ways signed."""

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30)
    opponent = await _rated(session, mu=3.00, sigma=0.30)

    at_stake = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=opponent, sport=Sport.PADEL
    )

    assert at_stake is not None
    assert at_stake.win_delta > 0 > at_stake.loss_delta


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_beating_somebody_above_you_is_worth_more_than_beating_an_equal(
    implementation, session
):
    """A shape demand and not a value one.

    The numbers are the rule's and are held to ``tests/unit/`` against hand-worked
    pairings; what the *contract* owes is that the block a player reads is about
    the person beside it. A port answering one figure for everybody would satisfy
    every other demand here.
    """

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30)
    equal = await _rated(session, mu=3.00, sigma=0.30)
    stronger = await _rated(session, mu=4.00, sigma=0.30)

    against_equal = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=equal, sport=Sport.PADEL
    )
    against_stronger = await port.counted_game_deltas(
        searcher_id=searcher, opponent_id=stronger, sport=Sport.PADEL
    )

    assert against_stronger.win_delta > against_equal.win_delta
    assert against_stronger.loss_delta > against_equal.loss_delta


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_is_asked_about_a_sport_and_answers_about_that_one(
    implementation, session
):
    """A Level is per ``(player, sport)``, and a padel pair prices no tennis."""

    port = implementation.build(session)
    searcher = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.PADEL)
    opponent = await _rated(session, mu=3.20, sigma=0.30, sport=Sport.PADEL)

    assert (
        await port.counted_game_deltas(
            searcher_id=searcher, opponent_id=opponent, sport=Sport.PADEL
        )
        is not None
    )
    assert (
        await port.counted_game_deltas(
            searcher_id=searcher, opponent_id=opponent, sport=Sport.TENNIS
        )
        is None
    )


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_at_stake_never_crosses_as_a_pair_that_changes_nothing(
    implementation, session
):
    port = implementation.build(session)

    at_stake = await port.counted_game_deltas(
        searcher_id=new_uuid(), opponent_id=new_uuid(), sport=Sport.TENNIS
    )

    assert at_stake is None or (at_stake.win_delta > 0 > at_stake.loss_delta)


# **A court, priced the way the result will be priced** (``docs/adr/0161``). A
# card prices *you against this person* because the other seats are unknown when
# it is drawn; a game's line-up is frozen, so its figure is the rule's own — side
# against side — and these demands hold the court read to that rather than to the
# pair read beside it.


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_a_court_of_two_is_priced_exactly_as_the_pair_is(
    implementation, session
):
    """In singles a side is one person, so the two readings are one number — and
    a court read that disagreed with the card here would be two rules."""

    port = implementation.build(session)
    me = await _rated(session, mu=3.00, sigma=0.30, sport=Sport.TENNIS)
    them = await _rated(session, mu=3.40, sigma=0.25, sport=Sport.TENNIS)

    on_court = await port.counted_game_deltas_on_court(
        player_id=me, own_side=[me], opposing_side=[them], sport=Sport.TENNIS
    )
    as_a_pair = await port.counted_game_deltas(
        searcher_id=me, opponent_id=them, sport=Sport.TENNIS
    )

    assert on_court == as_a_pair
    assert on_court is not None


@pytest.mark.parametrize("implementation", registered(AtStakeQuery))
async def test_a_four_is_priced_side_against_side_and_partners_share_the_pair(
    implementation, session
):
    """**Both partners move by the same amount**, because a result is a statement
    about one pair against another (``rule.py``'s ``one_side``) — and the pair
    is **the one ``rating_after`` will move by**, which is the whole of what *at
    stake* promises: not a preview of the rule but the rule, read forward.

    It is held against the engine's own entry point rather than against the pair
    read beside it, because in a four the two are different numbers: the step is
    priced from the **side's** uncertainty and the side's Level, and a card
    printing the head-to-head figure would be contradicted by the update.
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
    head_to_head = await port.counted_game_deltas(
        searcher_id=me, opponent_id=left, sport=Sport.PADEL
    )
    moved = rating_after(
        player=SkillEstimate(mu=3.00, sigma=0.30),
        opposition=one_side([SkillEstimate(3.00, 0.30), SkillEstimate(3.00, 0.30)]),
        won=True,
        results_so_far=0,
        share=information_share(Sport.PADEL),
        own_side=one_side([SkillEstimate(3.00, 0.30), SkillEstimate(2.00, 0.30)]),
    )

    assert mine is not None and head_to_head is not None
    assert mine == theirs
    assert (mine.win_delta, mine.loss_delta) == (moved.stakes.win, moved.stakes.loss)
    assert mine != head_to_head


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
# HalfBuiltCourtQuery — the court a fill names, and since #578 there is none
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(HalfBuiltCourtQuery))
async def test_a_fill_names_a_court_that_does_not_exist(implementation, session):
    """Nothing builds a court any more (#578), so every id a fill names answers
    the port's own word for *no such court*."""

    port = implementation.build(session)

    assert (
        await port.half_built_court(challenge_id=new_uuid(), member_id=new_uuid())
        is None
    )


# ---------------------------------------------------------------------------
# SharedCourtQuery — the deck's cool-off, read off ``games``' own record
# ---------------------------------------------------------------------------

# **The provider ships and the arrangement belongs to the port.** Every fact
# here is a game fact — a court is ahead until somebody says *we played*, calls
# it off, or lets the entry window close on it — so these arrange real games
# through the ``Game`` aggregate and never an ``INSERT`` (``docs/adr/0029``),
# and read the three ends back through whatever signed the contract.


def _games(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _singles(one: UUID, other: UUID) -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=one),
            Seating(side=GameSide.B, player_id=other),
        )
    )


def _four(a: UUID, b: UUID, c: UUID, d: UUID) -> LineUp:
    return LineUp.of(
        (
            Seating(side=GameSide.A, player_id=a),
            Seating(side=GameSide.A, player_id=b),
            Seating(side=GameSide.B, player_id=c),
            Seating(side=GameSide.B, player_id=d),
        )
    )


def _a_game(*, line_up: LineUp, planned_at: Instant) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=line_up,
        occurred_at=planned_at,
    )


async def _saved(session, game: Game) -> Game:
    """Every act on the aggregate first, then one save: the store's version
    check is what makes a second save of the same in-memory game a conflict."""

    await _games(session).save(game)
    await session.commit()
    return game


def _a_score() -> Score:
    return Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3)))


def _by_counterpart(courts) -> dict[UUID, SharedCourt]:
    return {court.counterpart_id: court for court in courts}


@pytest.mark.parametrize("implementation", registered(SharedCourtQuery))
async def test_a_court_still_ahead_is_ahead_and_names_everybody_on_it(
    implementation, session
):
    """A game planned and not yet played is a court the searcher is *with* each
    of the other three on — partner and opponents alike, because a pair is
    anybody you were on a court with."""

    me, partner, one, other = new_uuid(), new_uuid(), new_uuid(), new_uuid()
    await _saved(
        session,
        _a_game(line_up=_four(me, partner, one, other), planned_at=_ago(hours=2)),
    )

    courts = _by_counterpart(await implementation.build(session).shared_courts(me))

    assert set(courts) == {partner, one, other}
    assert all(court.ahead for court in courts.values())
    assert all(court.behind_since is None for court in courts.values())


@pytest.mark.parametrize("implementation", registered(SharedCourtQuery))
async def test_the_three_ends_each_date_the_court_behind_them(
    implementation, session
):
    """Played dates from the entry that said *we played*; called off from the
    call-off; never played from the entry window closing on silence — the
    three ends ``GAME_IS_HISTORY`` is dated from, and none of them the plan's
    own instant. A plan whose agreed moment has passed and whose window is
    still open is *ahead* here, which is ``docs/adr/0169`` §6's *awaiting a
    result*: the pair is held for as long as the court stands, and the window
    runs from the moment it stopped standing."""

    me, played, called_off, ghosted = new_uuid(), new_uuid(), new_uuid(), new_uuid()
    entered_at = _ago(days=2)
    game = _a_game(line_up=_singles(me, played), planned_at=_ago(days=3))
    game.state_result(by=me, score=_a_score(), occurred_at=entered_at)
    await _saved(session, game)

    # A four somebody left and the searcher then called off, with ``called_off``
    # still seated: the call-off is what put the court behind the two of them.
    ended_at = _ago(days=1)
    leaver = new_uuid()
    game = _a_game(
        line_up=_four(me, called_off, leaver, new_uuid()), planned_at=_ago(days=4)
    )
    game.vacate(leaver, occurred_at=_ago(days=1, hours=1))
    game.call_off(by=me, occurred_at=ended_at)
    await _saved(session, game)

    planned_at = _ago(days=20)
    await _saved(session, _a_game(line_up=_singles(me, ghosted), planned_at=planned_at))

    courts = _by_counterpart(await implementation.build(session).shared_courts(me))

    assert courts[played].behind_since == entered_at
    assert courts[called_off].behind_since == ended_at
    assert courts[ghosted].behind_since == entry_closes_at(planned_at)
    assert not any(court.ahead for court in courts.values())
    assert leaver not in courts, "a seat somebody left is no court of theirs"


@pytest.mark.parametrize("implementation", registered(SharedCourtQuery))
async def test_one_row_per_person_and_a_court_ahead_wins_over_one_behind(
    implementation, session
):
    """A pair with a game behind them and another ahead are *with* each other:
    the row is the ahead court. Two behind them is the later of the two."""

    me, again, twice = new_uuid(), new_uuid(), new_uuid()
    game = _a_game(line_up=_singles(me, again), planned_at=_ago(days=10))
    game.state_result(by=me, score=_a_score(), occurred_at=_ago(days=9))
    await _saved(session, game)
    await _saved(
        session, _a_game(line_up=_singles(me, again), planned_at=_ago(hours=1))
    )

    later = _ago(days=1)
    for entered_at in (_ago(days=5), later):
        game = _a_game(line_up=_singles(me, twice), planned_at=_ago(days=6))
        game.state_result(by=me, score=_a_score(), occurred_at=entered_at)
        await _saved(session, game)

    courts = await implementation.build(session).shared_courts(me)

    assert [court.counterpart_id for court in courts].count(again) == 1
    assert _by_counterpart(courts)[again].ahead
    assert _by_counterpart(courts)[twice].behind_since == later


@pytest.mark.parametrize("implementation", registered(SharedCourtQuery))
async def test_a_seat_the_searcher_left_is_no_court_of_theirs(
    implementation, session
):
    """Somebody who left a game is not *with* the people still on it, and a
    stranger to every court answers empty rather than erroring."""

    me, stayed, third, fourth = new_uuid(), new_uuid(), new_uuid(), new_uuid()
    game = _a_game(line_up=_four(me, stayed, third, fourth), planned_at=_ago(days=1))
    game.vacate(me, occurred_at=_ago(hours=3))
    await _saved(session, game)

    port = implementation.build(session)
    assert await port.shared_courts(me) == ()
    assert await port.shared_courts(new_uuid()) == ()
    assert {court.counterpart_id for court in await port.shared_courts(stayed)} == {
        third,
        fourth,
    }


@pytest.mark.parametrize("implementation", registered(SharedCourtQuery))
async def test_the_rows_come_newest_first_and_an_ahead_court_first_of_all(
    implementation, session
):
    """The order is the bound's meaning, as the pairwise history's is."""

    me, old, recent, ahead = new_uuid(), new_uuid(), new_uuid(), new_uuid()
    for other, planned_at, entered_at in (
        (old, _ago(days=21), _ago(days=20)),
        (recent, _ago(days=3), _ago(days=2)),
    ):
        game = _a_game(line_up=_singles(me, other), planned_at=planned_at)
        game.state_result(by=me, score=_a_score(), occurred_at=entered_at)
        await _saved(session, game)
    await _saved(
        session, _a_game(line_up=_singles(me, ahead), planned_at=_ago(hours=1))
    )

    courts = await implementation.build(session).shared_courts(me)

    assert [court.counterpart_id for court in courts] == [ahead, recent, old]


def test_a_shared_court_carries_the_other_person_and_a_moment_or_none():
    """Two fields and nothing about the game: no id to fetch it with, no side,
    no score. The deck needs *who* and *since when*, and a row carrying more
    would be a row a later caller acts on."""

    assert {field.name for field in fields(SharedCourt)} == {
        "counterpart_id",
        "behind_since",
    }
    ahead = SharedCourt(counterpart_id=new_uuid(), behind_since=None)
    assert ahead.ahead
    behind = SharedCourt(counterpart_id=new_uuid(), behind_since=_ago(days=1))
    assert not behind.ahead


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


async def test_the_deck_s_cool_off_fails_soft_and_is_neither_a_gate_nor_a_term():
    """A courtesy about the viewer's own deck, so it stands down like the
    suppression ledger does: an outage repeats the card of somebody they
    already know, and never empties a deal in a city that has people in it."""

    assert FAIL_POSTURE[SharedCourtQuery] is FailPosture.SOFT
    assert SharedCourtQuery in MATCHER_DEMANDS
    assert await read_demand(SharedCourtQuery, _unreadable, stood_down=()) == ()


def test_the_court_a_fill_names_fails_closed_and_is_not_a_gate():
    """**The row that shows what this table classifies.**

    It is not one of the four fail-closed gates and it is not a term: it is the
    subject of the search. Standing down would run an ordinary ⚡ over a pool that
    still excludes every person on the court, and hand the player a four of
    strangers where their own line-up should have been — so there is nothing to
    fall through to, and ``read_demand`` refuses a caller that offers one.
    """

    assert FAIL_POSTURE[HalfBuiltCourtQuery] is FailPosture.CLOSED
    assert HalfBuiltCourtQuery in MATCHER_DEMANDS


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
    figure alone is not a reading, and there is nowhere to put a blend of the
    five in place of them.
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
    says it can carry all six *at once* without them collapsing into each other
    — which is the half that would go wrong if somebody satisfied the shape by
    writing the same figure into every key. Each strand keeps the numerator and
    denominator it was measured from, and sportsmanship keeps a mean and a rating
    count because it is not a ratio.

    **Only three of the six have a provider**, and this reading is hand-built to
    carry all of them: the shape has to keep working the day the other three
    land, and a contract exercised only over what happens to be wired is a
    contract that goes stale quietly (``docs/adr/0140``, ``docs/adr/0160``).
    """

    observed = instant(datetime(2026, 8, 1, tzinfo=timezone.utc))
    ratios = {
        ReliabilityStrand.SHOWS_UP: (95, 38, 40),
        ReliabilityStrand.ANSWERS_CHALLENGES: (70, 14, 20),
        ReliabilityStrand.ANSWERS_RESULTS: (88, 22, 25),
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
    # The horizon reads one moment over the whole score, not one per strand.
    assert reading.most_recent_observation == observed


def test_the_six_strands_are_the_platform_s_six():
    """The keys are the engine's closed vocabulary, not a second spelling of it.

    A reading keyed by a locally-declared enum would satisfy every other
    assertion here and still be a second copy of a closed vocabulary, free to
    drift — the failure ``tests/unit/test_social_tag_vocabulary.py`` refuses for
    the Social tags. It binds twice over now: ``player_score`` publishes these
    names too, and it imports the same enum rather than declaring its own
    (``docs/adr/0140``).

    **The sixth name is not the one that was struck**, and the order is asserted
    rather than the membership, because the evidence rows are drawn in the enum's
    own declaration order. *Confirms results* was struck rather than deferred
    (``docs/adr/0137``): an unconfirmed result is a fact about a pair and a strand
    is a verdict about a person, and every denominator tried on it docked
    somebody ADR-0049 protects. It is listed nowhere because a withdrawn demand
    is withdrawn, not carried. *Answers about results* counts **answers** to a
    score put in front of somebody — a counter scores exactly as an acceptance
    does — which is a different measurement over the same events
    (``docs/adr/0160``).
    """

    assert [strand.value for strand in ReliabilityStrand] == [
        "SHOWS_UP",
        "ANSWERS_CHALLENGES",
        "ANSWERS_RESULTS",
        "KEEPS_PLANS",
        "SETTLES_UP",
        "SPORTSMANSHIP",
    ]
    assert "CONFIRMS_RESULTS" not in {strand.value for strand in ReliabilityStrand}


def test_a_strand_cannot_claim_more_good_outcomes_than_opportunities():
    with pytest.raises(InvariantViolated):
        RatioStrand(
            value=100,
            numerator=41,
            denominator=40,
            observed_at=instant(datetime(2026, 8, 1, tzinfo=timezone.utc)),
        )
