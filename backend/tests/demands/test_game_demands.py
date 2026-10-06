"""What ``games`` demands of the matcher, run against every implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/game_demands.py`` is enrolled
here automatically, so a second one either satisfies the demand or turns the
build red. There is no skipped test to go stale.

**The world is built the way the platform builds one**: a reader goes through
sign-up, the profile commit and a real assessment run, and the rest of the
court is filed on the log where the rating context files a Level. Nothing is
searched and nothing is indexed — the pairing is read side against side from
the people's Levels (#575).

**The demands this port exists for are the ones easiest to satisfy wrongly**
(``docs/adr/0161``). The forecast and the split are read *in the reader's
direction*, so the case that matters most is one court read by two people on
opposite sides. The stakes are *the rule read forward*, side against side, so
both partners get one pair. And a seat nobody rated empties the forecast and
never the Levels, and a reader with nothing to compute is still told who is
rated.
"""

from __future__ import annotations

import pytest

from app.bootstrap.game_demands import (
    GAME_DEMANDS,
    GAME_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import InvariantViolated, Sport
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.ports import ClubCheckIns, CourtPairing
from tests.api import players_world as players


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _port(implementation, session):
    return implementation.build(session)


async def _a_court(client, session_factory, *names, mu: float):
    """Some people rated at ``mu``, their Levels filed on the log."""

    return [
        (await players.a_player_on_the_log(client, session_factory, name, mu=mu))[0]
        for name in names
    ]


def _line_up(side_a, side_b) -> LineUp:
    return LineUp.of(
        (
            *(Seating(side=GameSide.A, player_id=one) for one in side_a),
            *(Seating(side=GameSide.B, player_id=one) for one in side_b),
        )
    )


async def _read(
    implementation,
    session_factory,
    *,
    reader_id,
    line_up: LineUp,
    kind: GameKind = GameKind.COUNTED,
    sport: Sport = players.SPORT,
):
    async with session_factory() as session:
        return await _port(implementation, session).pairing_for(
            sport=sport, kind=kind, line_up=line_up, reader_id=reader_id
        )


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_published_port_has_an_implementation():
    """A port nothing implements is a demand nothing runs against.

    **This is the test that stands under the parameterised ones.** A port whose
    register row is deleted does not turn its own contract tests red: an empty
    ``parametrize`` collects as *skipped*, and a skipped test is a test nobody
    is watching.
    """

    for port in GAME_DEMANDS:
        assert implementations_of(port), f"nothing signs {port.__name__}"


def test_every_registered_implementation_is_of_a_published_port():
    """The other direction: a row for a port this register does not declare is
    a claim of a different kind, filed on the wrong list."""

    for implementation in GAME_IMPLEMENTATIONS:
        assert implementation.port in GAME_DEMANDS


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_every_implementation_satisfies_the_protocol(
    implementation, session_factory
):
    """Structural, so a method renamed on one side is red here rather than a
    runtime ``AttributeError`` on somebody's game screen."""

    async with session_factory() as session:
        built = _port(implementation, session)

    assert isinstance(built, CourtPairing)


# ---------------------------------------------------------------------------
# The seats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_the_seats_name_whoever_holds_a_rating_in_the_courts_own_order(
    implementation, client, session_factory
):
    """**A Level per rated seat, in the line-up's order, and nothing else about
    them.** The unrated seat is simply not there — absence has one spelling —
    and the figures are ``rating``'s published ones, never derived."""

    reader = await players.a_rated_player(client, "reader")
    ada, bea = await _a_court(client, session_factory, "ada", "bea", mu=reader["mu"])
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)

    answer = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=_line_up((reader["id"], ada), (bea, unrated_id)),
    )

    assert answer is not None
    assert [seat.player_id for seat in answer.seats] == [reader["id"], ada, bea]
    theirs = next(seat for seat in answer.seats if seat.player_id == ada)
    assert theirs.level == pytest.approx(reader["mu"])
    assert theirs.band == "Improver"
    assert (theirs.range_low, theirs.range_high) == (
        pytest.approx(reader["mu"] - 0.3),
        pytest.approx(reader["mu"] + 0.3),
    )
    assert theirs.confidence == 62


# ---------------------------------------------------------------------------
# The forecast and the split
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_the_forecast_and_the_split_are_read_in_the_readers_direction(
    implementation, client, session_factory
):
    """**The demand this port exists for.** One court, two readers on opposite
    sides: the same percentage — a forecast is a fact about the game — and
    mirror-image strengths, because *your side* is theirs wherever they sit.
    Never provisional, because a line-up is frozen at the plan."""

    reader = await players.a_rated_player(client, "reader")
    other = await players.a_rated_player(client, "other")
    ada, bea = await _a_court(client, session_factory, "ada", "bea", mu=reader["mu"])
    line_up = _line_up((reader["id"], ada), (other["id"], bea))

    mine = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=line_up,
    )
    theirs = await _read(
        implementation,
        session_factory,
        reader_id=other["id"],
        line_up=line_up,
    )

    assert mine is not None and theirs is not None
    assert mine.forecast is not None and mine.split is not None
    assert theirs.forecast is not None and theirs.split is not None
    assert mine.forecast.pct == theirs.forecast.pct
    assert mine.forecast.provisional is False
    assert mine.split.your_side == theirs.split.their_side
    assert mine.split.their_side == theirs.split.your_side
    assert mine.split.gap == -theirs.split.gap


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_a_singles_court_is_one_strength_a_side(
    implementation, client, session_factory
):
    """`seats_per_side` is the sport's: a tennis court is two people, and the
    split is two player strengths and their difference."""

    me = await players.a_rated_player(client, "me", sport=Sport.TENNIS)
    you = await players.a_rated_player(client, "you", sport=Sport.TENNIS)

    answer = await _read(
        implementation,
        session_factory,
        reader_id=me["id"],
        line_up=_line_up((me["id"],), (you["id"],)),
        sport=Sport.TENNIS,
    )

    assert answer is not None and answer.split is not None
    assert len(answer.seats) == 2
    assert answer.split.your_side == pytest.approx(me["mu"])
    assert answer.split.their_side == pytest.approx(you["mu"])


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_a_reader_with_nothing_to_compute_still_gets_the_seats(
    implementation, client, session_factory
):
    """**Two providers, and each fails on its own.** A reader with no rating in
    the sport has nothing for the matcher to compute against, and is still told
    who on the court is rated — the Levels are ``rating``'s and not the
    pairing's. The stakes are absent too: nothing to move."""

    ada, bea, cy = await _a_court(client, session_factory, "ada", "bea", "cy", mu=2.80)
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)

    answer = await _read(
        implementation,
        session_factory,
        reader_id=unrated_id,
        line_up=_line_up((unrated_id, ada), (bea, cy)),
    )

    assert answer is not None
    assert [seat.player_id for seat in answer.seats] == [ada, bea, cy]
    assert answer.forecast is None and answer.split is None
    assert answer.at_stake is None


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_an_unrated_seat_empties_the_forecast_and_not_the_levels(
    implementation, client, session_factory
):
    """**Absent, never provisional.** A seat with no Level in the sport would
    read as a side short and price a provisional figure on a court whose
    line-up is booked. The forecast is omitted instead; the rated seats' Levels
    are still named, and the stakes still priced against the rated opponent."""

    reader = await players.a_rated_player(client, "reader")
    ada, bea = await _a_court(client, session_factory, "ada", "bea", mu=reader["mu"])
    unrated_id, unrated = await players.register(client, "unrated")
    await players.commit_profile(client, unrated)

    answer = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=_line_up((reader["id"], ada), (bea, unrated_id)),
    )

    assert answer is not None
    assert [seat.player_id for seat in answer.seats] == [reader["id"], ada, bea]
    assert answer.forecast is None and answer.split is None
    assert answer.at_stake is not None


# ---------------------------------------------------------------------------
# What is at stake
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_a_friendly_is_never_priced_and_a_counted_game_is(
    implementation, client, session_factory
):
    """*Meaningless rather than unavailable*: the forecast is drawn either way,
    and the stakes only where a result would count."""

    reader = await players.a_rated_player(client, "reader")
    ada, bea, cy = await _a_court(
        client, session_factory, "ada", "bea", "cy", mu=reader["mu"]
    )
    line_up = _line_up((reader["id"], ada), (bea, cy))

    friendly = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=line_up,
        kind=GameKind.FRIENDLY,
    )
    counted = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=line_up,
        kind=GameKind.COUNTED,
    )

    assert friendly is not None and counted is not None
    assert friendly.forecast is not None and friendly.at_stake is None
    assert counted.at_stake is not None
    assert counted.at_stake.win_delta > 0 > counted.at_stake.loss_delta
    assert counted.forecast == friendly.forecast


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_the_stakes_are_the_sides_and_both_partners_get_one_pair(
    implementation, client, session_factory
):
    """**Side against side.** A result is a statement about one pair against
    another, so the two people on a side are moved by the same amount — and the
    pair each is shown is the same pair."""

    reader = await players.a_rated_player(client, "reader")
    partner = await players.a_rated_player(client, "partner")
    bea, cy = await _a_court(client, session_factory, "bea", "cy", mu=reader["mu"])
    line_up = _line_up((reader["id"], partner["id"]), (bea, cy))

    mine = await _read(
        implementation,
        session_factory,
        reader_id=reader["id"],
        line_up=line_up,
    )
    theirs = await _read(
        implementation,
        session_factory,
        reader_id=partner["id"],
        line_up=line_up,
    )

    assert mine is not None and theirs is not None
    assert mine.at_stake is not None
    assert mine.at_stake == theirs.at_stake


# ---------------------------------------------------------------------------
# Who may ask
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(CourtPairing))
async def test_a_reader_who_is_not_on_the_court_is_a_broken_precondition(
    implementation, client, session_factory
):
    """The caller decides who may read — *the court is the whole of the
    permission* — so a reader off the court reaching this port is a wrong
    branch, and it is loud rather than answered."""

    ada, bea = await _a_court(client, session_factory, "ada", "bea", mu=2.80)
    stranger_id, _ = await players.register(client, "stranger")

    with pytest.raises(InvariantViolated):
        await _read(
            implementation,
            session_factory,
            reader_id=stranger_id,
            line_up=_line_up((ada,), (bea,)),
        )


# ---------------------------------------------------------------------------
# ClubCheckIns — who the club's desk saw arrive. The booking's answer (#547).
# ---------------------------------------------------------------------------


def _check_ins(implementation, session) -> ClubCheckIns:
    return implementation.build(session)


@pytest.mark.parametrize("implementation", registered(ClubCheckIns))
async def test_the_desk_s_check_ins_are_the_booking_s_and_nobody_else_s(
    implementation, session_factory
):
    """Keyed by the arrangement the game was opened from — a booked game's is
    its booking's id — and empty where no booking is behind it."""

    from datetime import datetime, timedelta, timezone

    from app.bootstrap.composition import (
        build_booking_repository,
        build_domain_event_store,
        build_event_publisher,
    )
    from app.engines.matchfit.core import SearchMode
    from app.kernel import Sport, instant
    from app.modules.bookings.domain.booking import BookedCourt, Booking
    from app.shared.ids import new_uuid

    ola, kuba, ewa, tomek = (new_uuid() for _ in range(4))
    start = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=start,
        share_grosze=30_00,
        first_side=(ola, kuba),
        second_side=(ewa, tomek),
        cut_off=instant(start - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(start - timedelta(days=5)),
    )
    booking.check_in(ewa, at=instant(start - timedelta(minutes=5)))
    async with session_factory() as session:
        await build_booking_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(booking)
        await session.commit()

    async with session_factory() as session:
        port = _check_ins(implementation, session)
        assert isinstance(port, ClubCheckIns)
        assert await port.checked_in(booking.booking_id) == frozenset({ewa})
        assert await port.checked_in(new_uuid()) == frozenset()
