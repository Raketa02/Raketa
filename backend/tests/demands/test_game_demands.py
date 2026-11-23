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

**And where a booked game's club is** (``GameClubs``, #657): the booking's club,
its name and its point, and how far a position is from it — the platform's one
great-circle distance, in metres — so an attendance tap can be measured against
the place the game is played. The world for it is a booked game, filled the way
a group fills one.

**And the Social tags of the people on a court** (``TagsOnTheCourt``, #835):
what a For-fun game's pairing works its Social vibe out from, every tag held,
committed over HTTP and heard by the player directory through the outbox.

**The demands this port exists for are the ones easiest to satisfy wrongly**
(``docs/adr/0161``). The forecast and the split are read *in the reader's
direction*, so the case that matters most is one court read by two people on
opposite sides. The stakes are *the rule read forward*, side against side, so
both partners get one pair. And a seat nobody rated empties the forecast and
never the Levels, and a reader with nothing to compute is still told who is
rated.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.game_demands import (
    GAME_DEMANDS,
    GAME_IMPLEMENTATIONS,
    implementations_of,
)
from app.kernel import InvariantViolated, Sport
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.ports import (
    CourtPairing,
    GameClub,
    GameClubs,
    TagsOnTheCourt,
)
from app.modules.player_profile.domain.social_tags import SocialTag
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_player,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def every_row():
    """Every row in the register, whichever port it signs."""

    return [
        pytest.param(one, id=f"{one.port.__name__}:{one.name}")
        for one in GAME_IMPLEMENTATIONS
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


@pytest.mark.parametrize("implementation", every_row())
async def test_every_implementation_satisfies_the_protocol(
    implementation, session_factory
):
    """Structural, so a method renamed on one side is red here rather than a
    runtime ``AttributeError`` on somebody's game screen."""

    async with session_factory() as session:
        built = _port(implementation, session)

    assert isinstance(built, implementation.port)


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
# Where a booked game's club is (#657)
# ---------------------------------------------------------------------------

#: Ogrody 33's point, as its desk dropped it.
OGRODY = (50.0600, 19.9400)


@pytest.fixture
def monday(app, payments) -> MovableClock:
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    payments.clock = fixed
    return fixed


async def _a_booking_at_ogrody(client, session_factory, payments, clock) -> str:
    """Ivan and Oscar's singles at Ogrody 33, booked by their two yeses."""

    ivan, oscar = [
        await a_player(client, payments, name, sports=(Sport.TENNIS,))
        for name in ("ivan", "oscar")
    ]
    club = await a_club_selling(client, name="Ogrody 33", point=OGRODY)
    group = await a_group(client, ivan, club, oscar)
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        sport=Sport.TENNIS,
        versions=((ivan, oscar),),
    )
    await says_yes(client, ivan, proposal)
    said = await says_yes(client, oscar, proposal)
    assert said.json()["booked"] is not None, said.text
    return said.json()["booked"]["booking_id"]


@pytest.mark.parametrize("implementation", registered(GameClubs))
async def test_a_booking_names_its_club_and_the_point_its_desk_dropped(
    implementation, client, session_factory, payments, monday
):
    booking = await _a_booking_at_ogrody(client, session_factory, payments, monday)

    async with session_factory() as session:
        club = await _port(implementation, session).of(UUID(booking))

    assert club == GameClub(name="Ogrody 33", latitude=OGRODY[0], longitude=OGRODY[1])


@pytest.mark.parametrize("implementation", registered(GameClubs))
async def test_a_position_is_measured_from_the_club_in_great_circle_metres(
    implementation, client, session_factory, payments, monday
):
    """A kilometre north is a kilometre — the haversine every distance on the
    platform is read with — and the club's own point is nought."""

    booking = await _a_booking_at_ogrody(client, session_factory, payments, monday)

    async with session_factory() as session:
        port = _port(implementation, session)
        there = await port.metres_from(
            UUID(booking), latitude=OGRODY[0], longitude=OGRODY[1]
        )
        north = await port.metres_from(
            UUID(booking), latitude=OGRODY[0] + 0.008993, longitude=OGRODY[1]
        )

    assert there is not None and north is not None
    assert (there.club_name, there.metres) == ("Ogrody 33", 0.0)
    assert north.metres == pytest.approx(1_000.0, abs=1.0)


@pytest.mark.parametrize("implementation", registered(GameClubs))
async def test_a_booking_that_does_not_exist_has_no_club(
    implementation, session_factory
):
    async with session_factory() as session:
        port = _port(implementation, session)
        nowhere = new_uuid()

        assert await port.of(nowhere) is None
        assert await port.metres_from(nowhere, latitude=0.0, longitude=0.0) is None


# ---------------------------------------------------------------------------
# The Social tags of the people on a court (#835)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(TagsOnTheCourt))
async def test_the_tags_on_the_court_are_everybody_s_as_they_hold_them_now(
    implementation, client, session_factory, mailbox
):
    """**What a For-fun game's Social vibe is worked out from** (#835): every
    tag each person holds — 💘 too, since leaving it out is the vibe's rule
    and not the port's — and everybody asked answered, with none for somebody
    holding none or unknown to the provider. Committed over HTTP and heard
    through the outbox, as the player directory hears them."""

    async def tagged(name: str, *held: str) -> tuple[UUID, str]:
        player_id, token = await players.register(client, name)
        if held:
            await players.commit_profile(client, token, social_tag_ids=list(held))
        return player_id, token

    tomek, _ = await tagged(
        "tomek", "STAYS_FOR_A_DRINK", "OPEN_TO_MEET_SOMEONE", "PLAYS_TO_WIN"
    )
    ola, ola_token = await tagged("ola", "STAYS_FOR_A_DRINK", "NEW_IN_TOWN")
    halfway, _ = await tagged("halfway")
    stranger = new_uuid()
    await mailbox.drain()

    async with session_factory() as session:
        tags = _port(implementation, session)
        assert await tags.held_by([tomek, ola, halfway, stranger]) == {
            tomek: {
                SocialTag.STAYS_FOR_A_DRINK,
                SocialTag.OPEN_TO_MEET_SOMEONE,
                SocialTag.PLAYS_TO_WIN,
            },
            ola: {SocialTag.STAYS_FOR_A_DRINK, SocialTag.NEW_IN_TOWN},
            halfway: frozenset(),
            stranger: frozenset(),
        }
        assert await tags.held_by([]) == {}

    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": ["QUIET_AND_FOCUSED", "SHARES_A_LIFT"]},
        headers=players.auth(ola_token),
    )
    assert changed.status_code == 200, changed.text
    await mailbox.drain()

    # The tags as they stand now, never as they stood on a read before.
    async with session_factory() as session:
        assert await _port(implementation, session).held_by([ola]) == {
            ola: {SocialTag.QUIET_AND_FOCUSED, SocialTag.SHARES_A_LIFT}
        }
