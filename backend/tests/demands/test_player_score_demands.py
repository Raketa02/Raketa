"""What ``player_score`` publishes, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/player_score_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or turns
the build red.

**This context stores nothing, so every arrangement here is made through
somebody else's aggregate** — a ``Booking`` that was kept or left, a ``Game``
that was played, come to late or not come to — and never an ``INSERT``
(``docs/adr/0029``). That is not ceremony: the folds under this port live in
``games`` and ``bookings``, and the only honest way to exercise a fold is to make
the history it folds.

**What the suite is written around is Player reliability in points** (#659;
``docs/adr/0195`` §1): everyone starts at a hundred, each thing on the record is
read off the context that owns it and priced once, and nobody asked about is
left out of the answer. The arithmetic's own edges — the clamp, a band's floor,
the order — are ``tests/unit/test_player_score_points.py``'s; here each line is
proved to be *read*, from real streams.
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
from app.engines.matchfit.core import ReliabilityBand, SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_score.domain.points import ReliabilityCounts
from app.shared.ids import new_uuid

AT_THE_CLUB = ClubVerdict(at_the_club=True, club_name="Ogrody 33")


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


def _game(
    one: UUID, other: UUID, *, starts: Instant, sport: Sport = Sport.TENNIS
) -> Game:
    """A booked singles game with an hour, ``one`` on side A."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=sport,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=one),
                Seating(side=GameSide.B, player_id=other),
            )
        ),
        occurred_at=instant(starts - timedelta(days=2)),
        starts_at=starts,
    )


async def _save(session, game: Game) -> Game:
    await _games(session).save(game)
    await session.commit()
    return game


async def _played(
    session,
    *,
    one: UUID,
    other: UUID,
    starts: Instant,
    sport: Sport = Sport.TENNIS,
) -> Game:
    """A booked game played through: ``one`` puts the score up after the hour."""

    game = _game(one, other, starts=starts, sport=sport)
    game.state_result(
        by=one,
        score=Score.of((SetScore(a=6, b=4),)),
        occurred_at=instant(starts + timedelta(hours=1, minutes=5)),
    )
    return await _save(session, game)


async def _not_come_to(session, *, absent: UUID, tapper: UUID, starts: Instant) -> Game:
    """``tapper`` came and tapped ``absent`` *isn't here yet* at the club ten
    minutes in; nobody arrived, so ``absent`` **Didn't come** — for good once
    the late claim's day is over (#657)."""

    game = _game(absent, tapper, starts=starts)
    game.note_absent(
        by=tapper,
        absent=absent,
        where=AT_THE_CLUB,
        occurred_at=instant(starts + timedelta(minutes=10)),
    )
    return await _save(session, game)


async def _came_late(session, *, late: UUID, tapper: UUID, starts: Instant) -> Game:
    """``late`` was tapped ten minutes in and said *I'm here* at 17:22 — **Came
    late** — and the game carried on to a score."""

    game = _game(late, tapper, starts=starts)
    game.note_absent(
        by=tapper,
        absent=late,
        where=AT_THE_CLUB,
        occurred_at=instant(starts + timedelta(minutes=10)),
    )
    game.note_arrival(
        by=late,
        arrived=late,
        where=AT_THE_CLUB,
        occurred_at=instant(starts + timedelta(minutes=22)),
    )
    game.state_result(
        by=tapper,
        score=Score.of((SetScore(a=6, b=4),)),
        occurred_at=instant(starts + timedelta(hours=1, minutes=5)),
    )
    return await _save(session, game)


def _counts(**said: int) -> ReliabilityCounts:
    zero = dict(
        turned_up=0, turned_up_of=0, late=0, kept=0, kept_of=0, left_in_dispute=0
    )
    return ReliabilityCounts(**{**zero, **said})


# ---------------------------------------------------------------------------
# Everybody asked is answered, and nobody else
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_player_with_no_record_reads_a_hundred_and_new(implementation, session):
    """Everyone starts at a hundred, so nobody is left out of the answer — and
    a hundred with every count at nought is not a verdict about anybody."""

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()

    scores = await port.scores_for([one, other], now=_now())

    assert set(scores) == {one, other}
    assert scores[one].points == 100
    assert scores[one].band is ReliabilityBand.VERY_HIGH
    assert scores[one].is_new
    assert scores[one].counts == _counts()


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_score_read_answers_only_about_players_it_was_asked_about(
    implementation, session
):
    """One batched read, and it volunteers nobody: the other player on the
    game below has a record of their own and is deliberately not asked about."""

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    await _played(session, one=one, other=other, starts=_ago(days=3))

    assert set(await port.scores_for([other], now=_now())) == {other}
    assert await port.scores_for([], now=_now()) == {}


# ---------------------------------------------------------------------------
# Shows up, read off the games
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_three_games_played_through_and_she_is_no_longer_new(
    implementation, session
):
    port = implementation.build(session)
    her, them = new_uuid(), new_uuid()
    for days in (9, 7):
        await _played(session, one=them, other=her, starts=_ago(days=days))

    before = (await port.scores_for([her], now=_now()))[her]
    await _played(session, one=them, other=her, starts=_ago(days=5))
    after = (await port.scores_for([her], now=_now()))[her]

    assert (before.points, before.is_new) == (100, True)
    assert (after.points, after.is_new) == (100, False)
    assert after.counts == _counts(turned_up=3, turned_up_of=3)


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_didnt_come_costs_twenty_five_and_the_one_who_came_earns_nothing(
    implementation, session
):
    """The miss is charged to **the player tapped** and to nobody else on that
    court; whoever came turned up, to a game that took no score."""

    port = implementation.build(session)
    oscar, ivan = new_uuid(), new_uuid()
    await _played(session, one=ivan, other=oscar, starts=_ago(days=10))
    await _not_come_to(session, absent=oscar, tapper=ivan, starts=_ago(days=6))

    scores = await port.scores_for([oscar, ivan], now=_now())

    # Five earned at a hundred is nothing, and then the miss: 75.
    assert scores[oscar].points == 75
    assert scores[oscar].band is ReliabilityBand.HIGH
    assert scores[oscar].counts == _counts(turned_up=1, turned_up_of=2)
    assert scores[ivan].points == 100
    assert scores[ivan].counts == _counts(turned_up=2, turned_up_of=2)
    # The game Ivan turned up to never counted: one game played through.
    assert scores[ivan].is_new


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_didnt_come_still_inside_its_late_claim_is_on_nobodys_record(
    implementation, session
):
    port = implementation.build(session)
    oscar, ivan = new_uuid(), new_uuid()
    await _not_come_to(session, absent=oscar, tapper=ivan, starts=_ago(hours=3))

    scores = await port.scores_for([oscar, ivan], now=_now())

    assert scores[oscar].points == 100
    assert scores[oscar].counts == _counts()
    assert scores[ivan].counts == _counts()


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_came_late_costs_ten_counts_as_turned_up_and_earns_nothing_back(
    implementation, session
):
    port = implementation.build(session)
    oscar, ivan = new_uuid(), new_uuid()
    await _came_late(session, late=oscar, tapper=ivan, starts=_ago(days=2))

    scores = await port.scores_for([oscar, ivan], now=_now())

    assert scores[oscar].points == 90
    assert scores[oscar].counts == _counts(turned_up=1, turned_up_of=1, late=1)
    assert scores[ivan].points == 100
    assert scores[ivan].counts == _counts(turned_up=1, turned_up_of=1)


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_silence_on_a_score_costs_nothing(implementation, session):
    """*Answers about results* left the figure (``docs/adr/0195`` §1): a score
    put to somebody and never answered is a game played through, and nothing
    else."""

    port = implementation.build(session)
    opener, silent = new_uuid(), new_uuid()
    await _played(session, one=opener, other=silent, starts=_ago(days=4))

    score = (await port.scores_for([silent], now=_now()))[silent]

    assert score.points == 100
    assert score.counts == _counts(turned_up=1, turned_up_of=1)


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_result_left_in_dispute_is_counted_for_both_and_costs_nothing(
    implementation, session
):
    """Two scores naming different winners, and neither side gave way: a line
    on each poster's record, and no points (``docs/adr/0195`` §5)."""

    port = implementation.build(session)
    one, other = new_uuid(), new_uuid()
    starts = _ago(days=5)
    game = _game(one, other, starts=starts)
    game.state_result(
        by=one,
        score=Score.of((SetScore(a=6, b=4),)),
        occurred_at=instant(starts + timedelta(hours=1, minutes=5)),
    )
    game.state_result(
        by=other,
        score=Score.of((SetScore(a=4, b=6),)),
        occurred_at=instant(starts + timedelta(hours=2)),
    )
    await _save(session, game)

    scores = await port.scores_for([one, other], now=_now())

    for player in (one, other):
        assert scores[player].points == 100
        assert scores[player].counts == _counts(
            turned_up=1, turned_up_of=1, left_in_dispute=1
        )


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_one_figure_across_sports(implementation, session):
    port = implementation.build(session)
    her, them = new_uuid(), new_uuid()
    await _not_come_to(session, absent=her, tapper=them, starts=_ago(days=8))
    await _played(session, one=them, other=her, starts=_ago(days=4), sport=Sport.PADEL)
    await _played(session, one=them, other=her, starts=_ago(days=3), sport=Sport.SQUASH)

    score = (await port.scores_for([her], now=_now()))[her]

    assert score.points == 85
    assert score.counts == _counts(turned_up=2, turned_up_of=3)


# ---------------------------------------------------------------------------
# Keeps plans, read off the bookings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_leaving_after_the_cut_off_with_the_seat_left_empty_costs_fifteen(
    implementation, session
):
    """Kept one, left another after the cut-off with nobody taking the seat —
    and those who stayed in the one that went ahead short are untouched."""

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

    scores = await port.scores_for([player, others[0]], now=_now())

    assert scores[player].points == 85
    assert scores[player].counts == _counts(kept=1, kept_of=2)
    assert scores[others[0]].points == 100
    assert scores[others[0]].counts == _counts(kept=1, kept_of=1)


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_leaving_while_it_was_free_costs_ten_once_the_game_is_called_off(
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

    assert scores[leaver].points == 90
    assert scores[leaver].counts == _counts(kept=0, kept_of=1)
    assert scores[stayers[0]].counts == _counts()


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_booked_game_still_ahead_is_on_nobodys_record(implementation, session):
    port = implementation.build(session)
    player = new_uuid()
    await _booked(
        session, (player, new_uuid(), new_uuid(), new_uuid()), starts=_ago(days=-3)
    )

    score = (await port.scores_for([player], now=_now()))[player]

    assert (score.points, score.counts) == (100, _counts())


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_didnt_come_is_priced_once_and_the_booked_game_is_kept(
    implementation, session
):
    """``docs/adr/0195`` §1: *Didn't come* is −25 on *Shows up*, and it no
    longer also breaks *Keeps plans* — the booking they held reads kept."""

    port = implementation.build(session)
    oscar, ivan, others = new_uuid(), new_uuid(), (new_uuid(), new_uuid())
    starts = _ago(days=6)
    await _booked(session, (oscar, ivan, *others), starts=starts)
    await _not_come_to(session, absent=oscar, tapper=ivan, starts=starts)

    score = (await port.scores_for([oscar], now=_now()))[oscar]

    assert score.points == 75
    assert score.counts == _counts(turned_up=0, turned_up_of=1, kept=1, kept_of=1)


# ---------------------------------------------------------------------------
# Six months
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(PublishedScoreQuery))
async def test_a_failure_older_than_six_months_drops_out_of_the_figure_and_counts(
    implementation, session
):
    port = implementation.build(session)
    player, others = new_uuid(), (new_uuid(), new_uuid(), new_uuid())
    long_ago = _ago(days=200)
    await _booked(
        session,
        (player, *others),
        starts=long_ago,
        leaving=((player, long_ago - timedelta(hours=3)),),
    )

    score = (await port.scores_for([player], now=_now()))[player]

    assert score.points == 100
    assert score.counts == _counts()


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
