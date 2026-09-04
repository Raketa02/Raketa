"""What ``player_score`` publishes, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/player_score_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red.

**This context stores nothing, so every arrangement here is made through
somebody else's aggregate** — a ``Challenge`` that was answered or left to lapse,
a ``Game`` that was played or ghosted — and never an ``INSERT``
(``docs/adr/0029``). That is not ceremony: the two folds under this port live in
``games`` and ``challenges``, and the only honest way to exercise a fold is to
make the history it folds.

**The rule the whole suite is written around is the absence rule.** A player with
no record is *absent from the answer*, never ``0`` and never ``0.5``. It is the
one thing that cannot be checked by reading the code, because the failure looks
like a perfectly ordinary dictionary comprehension — and it is the rule whose
breach would turn *no record* into *a bad record* everywhere downstream at once.

**Two strands and never three.** *Keeps plans*, *settles up* and *sportsmanship*
have no provider on this platform, and the assertions below say so by name rather
than by asserting a length: the day one of them lands, a named assertion says
which, and a length assertion would only say that something changed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.bootstrap.player_score_demands import (
    PLAYER_SCORE_DEMANDS,
    PLAYER_SCORE_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant, Sport, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.seats import SeatPlan, court_sides
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_profile.domain.availability import Window
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
# The world these demands are run against
# ---------------------------------------------------------------------------


def _now() -> Instant:
    return instant(datetime.now(timezone.utc))


def _ago(**offset) -> Instant:
    """A moment that far behind the clock these demands read ``now`` from."""

    return instant(datetime.now(timezone.utc) - timedelta(**offset))


#: Old enough that a plan made then has closed its entry window on silence.
#: Read off the two windows rather than typed, so a change to either moves this
#: with it instead of leaving a test that passes for the wrong reason.
_LONG_ENOUGH_TO_GHOST = PLAN_HORIZON + ENTRY_GRACE + timedelta(days=1)


def _challenges(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _games(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _court(
    sport: Sport,
    organiser: UUID,
    *invitees: UUID,
    already_in: tuple[UUID, ...] = (),
) -> list[SeatPlan]:
    """The sport's whole fixed court: the organiser, whoever is asked, and gaps.

    An empty seat is a seat, so the rest of the court is spelled rather than
    omitted — and a **newly** invited seat carries the origin the send read off a
    search, because a seat that cannot say where it came from cannot be
    constructed. ``already_in`` is who is being kept rather than asked: only the
    newly seated are invited, and offering a seat to somebody already in the game
    is refused at the aggregate.
    """

    sides = court_sides(sport)
    occupants: list[UUID | None] = [organiser, *already_in, *invitees]
    occupants += [None] * (len(sides) - len(occupants))
    asked = set(invitees)
    return [
        SeatPlan(
            side=side,
            player_id=occupant,
            origin=(
                SentFromSearch(search_id=new_uuid(), position=seat)
                if occupant in asked
                else None
            ),
        )
        for seat, (side, occupant) in enumerate(zip(sides, occupants, strict=True), 1)
    ]


async def _invited(
    session,
    *,
    organiser: UUID,
    invitee: UUID,
    at: Instant,
    beside: UUID | None = None,
) -> Challenge:
    """One send, through the aggregate: an organiser and whoever is asked.

    Tennis unless a second invitee is named, in which case it is padel — because
    a singles challenge whose only invitee says no is **over**, and a court with
    somebody still in it is what a re-offer needs.
    """

    others = (invitee,) if beside is None else (invitee, beside)
    sport = Sport.TENNIS if beside is None else Sport.PADEL
    challenge = Challenge.sent(
        challenge_id=new_uuid(),
        sport=sport,
        mode=None,
        window=Window.THIS_WEEK,
        organiser_id=organiser,
        arrangement=_court(sport, organiser, *others),
        occurred_at=at,
    )
    await _challenges(session).save(challenge)
    await session.commit()
    return challenge


async def _answers(
    session, challenge: Challenge, player_id: UUID, *, yes: bool, at: Instant
) -> None:
    repository = _challenges(session)
    loaded = await repository.load(challenge.id)
    assert loaded is not None
    if yes:
        loaded.accept(player_id, occurred_at=at)
    else:
        loaded.decline(player_id, occurred_at=at)
    await repository.save(loaded)
    await session.commit()


async def _refills(
    session,
    challenge: Challenge,
    *,
    organiser: UUID,
    still_in: tuple[UUID, ...],
    replacement: UUID,
    at: Instant,
) -> None:
    """Offer the seat somebody just left on to somebody new.

    The path that makes today's arrangement forget a former occupant, which is
    the whole reason the invitations are walked off the events rather than read
    off the seats.
    """

    repository = _challenges(session)
    loaded = await repository.load(challenge.id)
    assert loaded is not None
    loaded.invite(
        _court(loaded.sport, organiser, replacement, already_in=still_in),
        occurred_at=at,
    )
    await repository.save(loaded)
    await session.commit()


async def _played(session, *, one: UUID, other: UUID, at: Instant) -> Game:
    """A plan that produced a game: somebody said *we played*, with a score."""

    game = _plan(one=one, other=other, at=at)
    game.state_result(
        by=one,
        score=Score.of((SetScore(a=6, b=4),)),
        occurred_at=instant(at + timedelta(hours=2)),
    )
    await _games(session).save(game)
    await session.commit()
    return game


async def _ghosted(session, *, one: UUID, other: UUID) -> Game:
    """A plan nobody ever claimed, old enough that its entry window has shut."""

    game = _plan(one=one, other=other, at=instant(_now() - _LONG_ENOUGH_TO_GHOST))
    await _games(session).save(game)
    await session.commit()
    return game


def _plan(*, one: UUID, other: UUID, at: Instant) -> Game:
    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        kind=GameKind.COUNTED,
        window=Window.TODAY,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=one),
                Seating(side=GameSide.B, player_id=other),
            )
        ),
        occurred_at=at,
    )


# ---------------------------------------------------------------------------
# The absence rule, which is the whole of what this context promises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_player_with_no_record_is_absent_and_never_a_zero(
    implementation, session
):
    """No record is not a bad record, and the spelling of that is *not answering*.

    Two strangers, and a provider with two event logs behind it that can now
    answer about somebody: the answer is empty rather than two scores of nought.
    """

    port = implementation.build(session)

    assert await port.scores_for([new_uuid(), new_uuid()], now=_now()) == {}


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_score_read_answers_only_about_players_it_was_asked_about(
    implementation, session
):
    """One batched read per search, and it volunteers nobody.

    The organiser of the challenge below has a record of their own and is
    deliberately not in the question: a read that answered about them would be
    answering about somebody the caller never asked after.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=invitee, at=_ago(days=2)
    )
    await _answers(session, challenge, invitee, yes=True, at=_ago(days=2))

    scores = await port.scores_for([invitee], now=_now())

    assert set(scores) == {invitee}


# ---------------------------------------------------------------------------
# The two strands that have a provider
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_answering_inside_the_window_and_letting_one_lapse_are_one_strand(
    implementation, session
):
    """Two invitations, one answered and one left to run out.

    Both are opportunities and one is a good outcome, so the strand is a half —
    and the lapse is counted **without any sweep having run**, because a seat
    past its day is lapsed whether or not anything noticed.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    answered = await _invited(
        session, organiser=organiser, invitee=invitee, at=_ago(days=4)
    )
    await _answers(session, answered, invitee, yes=True, at=_ago(days=4))
    await _invited(session, organiser=organiser, invitee=invitee, at=_ago(days=3))

    score = (await port.scores_for([invitee], now=_now()))[invitee]
    strand = score.strands[ReliabilityStrand.ANSWERS_CHALLENGES]

    assert (strand.good, strand.opportunities) == (1, 2)
    assert strand.value == 50


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_turning_somebody_down_inside_your_day_is_answering_them(
    implementation, session
):
    """**The one strand on this platform where a no is a good outcome.**

    *Answers challenges* prices silence, not judgement — which is why a lapse and
    a decline are different facts on the seat, and why a strand that filed them
    alike would be unmeasurable.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=invitee, at=_ago(days=2)
    )
    await _answers(session, challenge, invitee, yes=False, at=_ago(days=2))

    score = (await port.scores_for([invitee], now=_now()))[invitee]

    assert score.strands[ReliabilityStrand.ANSWERS_CHALLENGES].value == 100


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_organisers_own_seat_is_not_an_invitation_they_answered(
    implementation, session
):
    """A seat nobody was asked to take is not an opportunity.

    The organiser accepts from birth because they are the one proposing, and a
    strand that counted it would publish a hundred per cent for anybody who only
    ever organises. They are absent here — their invitee's challenge tells us
    nothing about *them*.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=invitee, at=_ago(days=2)
    )
    await _answers(session, challenge, invitee, yes=True, at=_ago(days=2))

    scores = await port.scores_for([organiser, invitee], now=_now())

    assert set(scores) == {invitee}


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_an_invitation_still_inside_its_day_is_not_yet_an_opportunity(
    implementation, session
):
    """The answer is still wanted, so nothing has been observed about anybody.

    Filing it either way would price somebody for an answer they still have time
    to give — and the player is absent rather than sitting at ``0/0``.
    """

    port = implementation.build(session)
    organiser, invitee = new_uuid(), new_uuid()
    await _invited(session, organiser=organiser, invitee=invitee, at=_ago(hours=1))

    assert await port.scores_for([invitee], now=_now()) == {}


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_game_that_happened_and_a_plan_that_ghosted_are_one_strand(
    implementation, session
):
    """*Shows up*, both halves, on the same person.

    The ghost is charged to **everybody who was on that court**, which is the
    decision ``docs/adr/0140`` had to take rather than inherit: a dissolved
    arrangement is a fact about the court and there is nobody in it to blame.
    """

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _played(session, one=one, other=other, at=_ago(days=3))
    await _ghosted(session, one=one, other=other)

    scores = await port.scores_for([one, other], now=_now())
    strand = scores[one].strands[ReliabilityStrand.SHOWS_UP]

    assert (strand.good, strand.opportunities) == (1, 2)
    assert scores[other].strands[ReliabilityStrand.SHOWS_UP] == strand


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_an_answer_survives_the_seat_being_offered_to_somebody_else(
    implementation, session
):
    """A refusal stays on the record of the person who made it.

    A declined seat can be re-offered, and the arrangement that results has
    forgotten whoever left it — so a read that asked today's seats would erase a
    real answer the day the organiser refilled the seat, and would hand the
    replacement a deadline that was never theirs.
    """

    port = implementation.build(session)
    organiser, decliner = new_uuid(), new_uuid()
    staying, replacement = new_uuid(), new_uuid()
    challenge = await _invited(
        session,
        organiser=organiser,
        invitee=decliner,
        beside=staying,
        at=_ago(days=3),
    )
    await _answers(session, challenge, staying, yes=True, at=_ago(days=3))
    await _answers(session, challenge, decliner, yes=False, at=_ago(days=3))
    await _refills(
        session,
        challenge,
        organiser=organiser,
        still_in=(staying,),
        replacement=replacement,
        at=_ago(hours=2),
    )

    scores = await port.scores_for([decliner, replacement], now=_now())

    assert scores[decliner].strands[ReliabilityStrand.ANSWERS_CHALLENGES].value == 100
    # The replacement's own day is still running, so nothing is owed about them.
    assert replacement not in scores


# ---------------------------------------------------------------------------
# The three that stand down, and the blend over what is left
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_three_strands_with_no_provider_are_absent_and_never_nought(
    implementation, session
):
    """Named one by one, so the day one lands the assertion says which.

    Nobody has failed to keep a plan, because no plan on this platform has a
    moment to be late for; nobody owes a court share, because there is no court
    money; and nobody has been rated, because there is no surface on which to
    rate anybody.
    """

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _played(session, one=one, other=other, at=_ago(days=3))

    score = (await port.scores_for([one], now=_now()))[one]

    assert ReliabilityStrand.KEEPS_PLANS not in score.strands
    assert ReliabilityStrand.SETTLES_UP not in score.strands
    assert ReliabilityStrand.SPORTSMANSHIP not in score.strands


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_one_strand_is_a_score_and_the_two_records_are_independent(
    implementation, session
):
    """A reading needs *a* strand, not all of them.

    Somebody who has answered invitations and never had a game arranged has a
    Player Score of one strand — and requiring both would make the score answer
    about nobody until the platform held both records about the same person.
    """

    port = implementation.build(session)
    organiser, answerer = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=answerer, at=_ago(days=2)
    )
    await _answers(session, challenge, answerer, yes=True, at=_ago(days=2))
    player, opponent = new_uuid(), new_uuid()
    await _played(session, one=player, other=opponent, at=_ago(days=3))

    scores = await port.scores_for([answerer, player], now=_now())

    assert set(scores[answerer].strands) == {ReliabilityStrand.ANSWERS_CHALLENGES}
    assert set(scores[player].strands) == {ReliabilityStrand.SHOWS_UP}


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_published_number_is_the_blend_over_the_strands_that_are_there(
    implementation, session
):
    """35 and 20 over a basis of 55, and never over a hundred.

    A player with both strands at a hundred is published at a hundred — which is
    the assertion that the three standing-down names cost the number nothing,
    because a blend over a basis of a hundred would have capped them at 55.
    """

    port = implementation.build(session)
    organiser, player = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=player, at=_ago(days=2)
    )
    await _answers(session, challenge, player, yes=True, at=_ago(days=2))
    await _played(session, one=player, other=new_uuid(), at=_ago(days=3))

    score = (await port.scores_for([player], now=_now()))[player]

    assert score.published == 100


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_freshest_observation_is_one_moment_over_the_whole_score(
    implementation, session
):
    """The horizon reads one age, because the strands share one cause.

    *This player stopped playing* is one fact, and two ages would be two places
    for it to disagree with itself. The moment is the most recent opportunity to
    have **closed**, whichever strand it belonged to.
    """

    port = implementation.build(session)
    organiser, player = new_uuid(), new_uuid()
    challenge = await _invited(
        session, organiser=organiser, invitee=player, at=_ago(days=9)
    )
    answered_at = _ago(days=9)
    await _answers(session, challenge, player, yes=True, at=answered_at)
    game = await _played(session, one=player, other=new_uuid(), at=_ago(days=3))

    score = (await port.scores_for([player], now=_now()))[player]

    assert score.last_at == game.played_at
    assert score.last_at > answered_at


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_published_port_has_at_least_one_implementation():
    """A port with nothing registered is a red build."""

    unregistered = [
        port.__name__ for port in PLAYER_SCORE_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_is_of_a_published_port():
    """And the other direction, so the two lists check each other."""

    stray = [
        one.name
        for one in PLAYER_SCORE_IMPLEMENTATIONS
        if one.port not in PLAYER_SCORE_DEMANDS
    ]

    assert stray == []
