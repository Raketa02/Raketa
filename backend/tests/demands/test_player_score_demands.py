"""What ``player_score`` publishes, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/player_score_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red.

**This context stores nothing, so every arrangement here is made through
somebody else's aggregate** — a ``Booking`` that was kept or left, a ``Game``
that was played or ghosted — and never an ``INSERT`` (``docs/adr/0029``). That
is not ceremony: the folds under this port live in ``games`` and ``bookings``,
and the only honest way to exercise a fold is to make the history it folds.

**The rule the whole suite is written around is the absence rule.** A player with
no record is *absent from the answer*, never ``0`` and never ``0.5``. It is the
one thing that cannot be checked by reading the code, because the failure looks
like a perfectly ordinary dictionary comprehension — and it is the rule whose
breach would turn *no record* into *a bad record* everywhere downstream at once.

**Three strands and never four.** *Answers challenges* stood down with #544 —
challenges no longer wait for answers, and *keeps plans* came up in its place —
*settles up* has no provider on this platform, and *sportsmanship* is published
in its own right rather than as a strand (``docs/adr/0158``), and the assertions
below say so by name rather than by asserting a length: the day one of them
lands, a named assertion says which, and a length assertion would only say that
something changed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.bootstrap.player_score_demands import (
    PLAYER_SCORE_DEMANDS,
    PLAYER_SCORE_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.games.domain.windows import ENTRY_GRACE, PLAN_HORIZON
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_profile.domain.weekly_hours import Window
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


def _games(session):
    return build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


def _bookings(session):
    return build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def _booked(
    session,
    players: tuple[UUID, UUID, UUID, UUID],
    *,
    starts: Instant,
    leaving: tuple[tuple[UUID, Instant], ...] = (),
) -> Booking:
    """A padel game booked five days before its hour, through the aggregate,
    with a 24-hour cut-off — and whoever left it, when they left."""

    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=starts,
        share_grosze=30_00,
        first_side=players[:2],
        second_side=players[2:],
        cut_off=instant(starts - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(starts - timedelta(days=5)),
    )
    for player, at in leaving:
        booking.leave(player, at=at)
    await _bookings(session).save(booking)
    await session.commit()
    return booking


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


async def _answered_a_score(
    session, *, opener: UUID, answerer: UUID, at: Instant, counter: bool = False
) -> Game:
    """A game whose score was put in front of ``answerer``, and answered.

    ``counter`` is the whole point of the strand: a player who believes the score
    is wrong says so, and saying so is an answer. Both paths leave the same fact
    on the record — *they replied inside the window* — and the ending they leave
    the **game** in is deliberately different, which is what proves the strand is
    not counting agreements.
    """

    game = _plan(one=opener, other=answerer, at=at)
    proposed_at = instant(at + timedelta(hours=2))
    game.state_result(
        by=opener, score=Score.of((SetScore(a=6, b=4),)), occurred_at=proposed_at
    )
    if counter:
        game.state_result(
            by=answerer,
            score=Score.of((SetScore(a=4, b=6),)),
            occurred_at=instant(proposed_at + timedelta(hours=1)),
        )
    else:
        game.accept_result(
            by=answerer, occurred_at=instant(proposed_at + timedelta(hours=1))
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

    The other player on the game below has a record of their own and is
    deliberately not in the question: a read that answered about them would be
    answering about somebody the caller never asked after.
    """

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _played(session, one=one, other=other, at=_ago(days=3))

    scores = await port.scores_for([other], now=_now())

    assert set(scores) == {other}


# ---------------------------------------------------------------------------
# The three strands that have a provider
# ---------------------------------------------------------------------------


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
async def test_a_score_answered_and_a_score_ignored_are_one_strand(
    implementation, session
):
    """*Answers about results*, both halves, on the same person.

    Two scores were put in front of them; they replied to one and let the other
    run out. Both are opportunities and one is a good outcome, and the miss is
    counted **without anything having swept it** — a window that has closed has
    closed whether or not a job noticed.
    """

    port = implementation.build(session)
    player, opener = new_uuid(), new_uuid()
    await _answered_a_score(session, opener=opener, answerer=player, at=_ago(days=4))
    await _played(session, one=opener, other=player, at=_ago(days=3))

    score = (await port.scores_for([player], now=_now()))[player]
    strand = score.strands[ReliabilityStrand.ANSWERS_RESULTS]

    assert (strand.good, strand.opportunities) == (1, 2)
    assert strand.value == 50


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_countering_a_score_is_answering_it_and_disagreeing_costs_nothing(
    implementation, session
):
    """**The reason this strand could be built and the struck one could not.**

    The game ends unscored — two scores stood and neither side gave way — and the
    person who disagreed is published at a hundred. A strand counting agreements
    would have docked them, and would have docked the other side too, for the one
    act ``docs/adr/0049`` most wants a player to feel free to make.
    """

    port = implementation.build(session)
    opener, counterer = new_uuid(), new_uuid()
    await _answered_a_score(
        session, opener=opener, answerer=counterer, at=_ago(days=4), counter=True
    )

    scores = await port.scores_for([opener, counterer], now=_now())

    assert scores[counterer].strands[ReliabilityStrand.ANSWERS_RESULTS].value == 100
    # The opener was asked nothing: their score was the question.
    assert ReliabilityStrand.ANSWERS_RESULTS not in scores[opener].strands


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_only_this_strand_forgets_and_the_other_two_count_a_career(
    implementation, session
):
    """**One window, and it belongs to one strand** (``docs/adr/0160``).

    The same game, more than twelve months old, is still an opportunity for
    *shows up* and is no longer one for *answers about results*. That asymmetry is
    the decision rather than a coincidence: turning up is a commitment somebody
    made, and answering a score is a habit of opening an app — a mark for
    something that cheap to fail by accident has to be one a player can work off.
    """

    port = implementation.build(session)
    player, opener = new_uuid(), new_uuid()
    await _played(session, one=opener, other=player, at=_ago(days=400))

    score = (await port.scores_for([player], now=_now()))[player]

    assert ReliabilityStrand.SHOWS_UP in score.strands
    assert ReliabilityStrand.ANSWERS_RESULTS not in score.strands


# ---------------------------------------------------------------------------
# The three that stand down, and the blend over what is left
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_booked_game_kept_and_one_broken_after_its_cut_off_are_one_strand(
    implementation, session
):
    """*Keeps plans*, both halves, on the same person (#544; the mechanics §15.4).

    A booked game is a plan with a moment. They stayed in one until its hour,
    which is keeping it; they left another after the club's cut-off and nobody
    took the seat, which is breaking it — counted **without anything having
    swept it**, since an hour that has come has come.
    """

    port = implementation.build(session)
    player, others = new_uuid(), (new_uuid(), new_uuid(), new_uuid())
    await _booked(session, (player, *others), starts=_ago(days=5))
    broken = _ago(days=2)
    await _booked(
        session,
        (player, *others),
        starts=broken,
        leaving=((player, broken - timedelta(hours=3)),),
    )

    score = (await port.scores_for([player, others[0]], now=_now()))
    strand = score[player].strands[ReliabilityStrand.KEEPS_PLANS]

    assert (strand.good, strand.opportunities) == (1, 2)
    assert strand.last_at == broken
    # Those who stayed kept the first; the second, which went ahead short, is
    # nothing on their record (the mechanics §14.1).
    stayed = score[others[0]].strands[ReliabilityStrand.KEEPS_PLANS]
    assert (stayed.good, stayed.opportunities) == (1, 1)


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_leaving_while_it_was_free_is_a_mark_once_the_game_is_called_off(
    implementation, session
):
    """Leaving before the cut-off is on the record **only if the game is then
    called off because of that seat** — and nothing is on the record of those
    who stayed."""

    port = implementation.build(session)
    leaver, stayers = new_uuid(), (new_uuid(), new_uuid(), new_uuid())
    starts = _ago(hours=12)
    await _booked(
        session,
        (leaver, *stayers),
        starts=starts,
        leaving=((leaver, starts - timedelta(days=2)),),
    )

    scores = await port.scores_for([leaver, stayers[0]], now=_now())

    assert scores[leaver].strands[ReliabilityStrand.KEEPS_PLANS].value == 0
    assert stayers[0] not in scores


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_booked_game_still_ahead_is_not_yet_an_opportunity(
    implementation, session
):
    """Nobody has kept or broken a game whose hour has not come — and the
    player is absent rather than sitting at ``0/0``."""

    port = implementation.build(session)
    player = new_uuid()
    await _booked(
        session, (player, new_uuid(), new_uuid(), new_uuid()), starts=_ago(days=-3)
    )

    assert await port.scores_for([player], now=_now()) == {}


# ---------------------------------------------------------------------------
# The three that stand down, and the blend over what is left
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_three_strands_with_no_provider_are_absent_and_never_nought(
    implementation, session
):
    """Named one by one, so the day one lands the assertion says which.

    Nobody has failed to answer a challenge since challenges stopped waiting for
    answers (#544), and nothing sends one since they went (#578); nobody owes a
    court share, because a share is taken before the game exists; and nobody
    has been rated, because there is no surface on which to rate anybody.
    """

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _played(session, one=one, other=other, at=_ago(days=3))

    score = (await port.scores_for([one], now=_now()))[one]

    assert ReliabilityStrand.ANSWERS_CHALLENGES not in score.strands
    assert ReliabilityStrand.SETTLES_UP not in score.strands
    assert ReliabilityStrand.SPORTSMANSHIP not in score.strands


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_one_strand_is_a_score_and_the_two_records_are_independent(
    implementation, session
):
    """A reading needs *a* strand, not all of them.

    Somebody who has kept a booked game and never had a game ghost or a score
    put to them has a Player Score of one strand — and requiring every record
    would make the score answer about nobody until the platform held all of
    them about the same person.
    """

    port = implementation.build(session)
    keeper = new_uuid()
    await _booked(
        session, (keeper, new_uuid(), new_uuid(), new_uuid()), starts=_ago(days=2)
    )
    player, opponent = new_uuid(), new_uuid()
    await _played(session, one=player, other=opponent, at=_ago(days=3))

    scores = await port.scores_for([keeper, player], now=_now())

    assert set(scores[keeper].strands) == {ReliabilityStrand.KEEPS_PLANS}
    assert set(scores[player].strands) == {ReliabilityStrand.SHOWS_UP}


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_the_published_number_is_the_blend_over_the_strands_that_are_there(
    implementation, session
):
    """35, 12 and 15 over a basis of 62, and never over a hundred.

    A player with all three live strands at a hundred is published at a hundred —
    which is the assertion that the three standing-down names cost the number
    nothing, because a blend over a basis of a hundred would have capped them at
    62.
    """

    port = implementation.build(session)
    player = new_uuid()
    await _booked(
        session, (player, new_uuid(), new_uuid(), new_uuid()), starts=_ago(days=2)
    )
    await _played(session, one=player, other=new_uuid(), at=_ago(days=3))
    await _answered_a_score(
        session, opener=new_uuid(), answerer=player, at=_ago(days=3)
    )

    score = (await port.scores_for([player], now=_now()))[player]

    assert set(score.strands) == {
        ReliabilityStrand.SHOWS_UP,
        ReliabilityStrand.KEEPS_PLANS,
        ReliabilityStrand.ANSWERS_RESULTS,
    }
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
    player = new_uuid()
    kept_at = _ago(days=9)
    await _booked(session, (player, new_uuid(), new_uuid(), new_uuid()), starts=kept_at)
    game = await _played(session, one=player, other=new_uuid(), at=_ago(days=3))

    score = (await port.scores_for([player], now=_now()))[player]

    assert score.last_at == game.played_at
    assert score.last_at > kept_at


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


