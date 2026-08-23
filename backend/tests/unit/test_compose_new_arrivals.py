"""Composing shelves 4 and 5: a shared set, a per-viewer order, and no floor.

The behaviours under test are the four steps ADR-0068's split makes literal —
ask the cache, ask the port on a miss, load the rows live, order for **this**
viewer — plus the two rules a shelf carries that a region does not: a cap, and
being **absent** rather than empty.
"""

from uuid import UUID, uuid4

import pytest

from app.kernel import Sport, shifted, minutes

from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.domain.arrivals import (
    NEW_CLUB_WINDOW,
    NEW_PLAYER_WINDOW,
    ArrivalKind,
)
from app.modules.now.domain.screen import ClubCard, Level, PersonCard
from app.modules.now.domain.vocabulary import CardType, ShelfCode
from tests.unit.arrival_doubles import (
    AT,
    FakeArrivalRows,
    FakeLevels,
    FakeNewArrivals,
    RecordingArrivalSets,
    a_club,
    a_player,
    days_ago,
)

STAMP = 1_771_200_000_000
VIEWER = uuid4()


def _level(value: float, *, provisional: bool = False) -> Level:
    return Level(value=value, provisional=provisional)


def _compose(
    *,
    arrivals: FakeNewArrivals | None = None,
    rows: FakeArrivalRows | None = None,
    levels: FakeLevels | None = None,
    sets: RecordingArrivalSets | None = None,
) -> tuple[ComposeNewArrivals, RecordingArrivalSets, FakeNewArrivals]:
    held_sets = sets or RecordingArrivalSets()
    held_arrivals = arrivals or FakeNewArrivals()
    return (
        ComposeNewArrivals(
            arrivals=held_arrivals,
            rows=rows or FakeArrivalRows(),
            levels=levels or FakeLevels(),
            sets=held_sets,
        ),
        held_sets,
        held_arrivals,
    )


async def _shelves(compose: ComposeNewArrivals, *sports: Sport, viewer: UUID = VIEWER):
    return await compose.compose(
        viewer=viewer,
        sports=frozenset(sports),
        now=AT,
        stamp=STAMP,
    )


def _by_code(shelves, code: ShelfCode):
    for shelf in shelves:
        if shelf.code is code:
            return shelf
    return None


# -- absent rather than empty -----------------------------------------------


async def test_a_shelf_with_nothing_in_it_is_absent() -> None:
    # A shelf makes a claim, and a row that appears every week saying *nothing
    # worth waiting for* is a row players learn to scroll past.
    compose, _, _ = _compose()
    assert await _shelves(compose, Sport.PADEL) == ()


async def test_a_viewer_with_no_sports_composes_nothing_and_asks_nothing() -> None:
    compose, sets, arrivals = _compose()
    assert await _shelves(compose) == ()
    assert arrivals.player_asks == []
    assert arrivals.club_asks == []
    assert sets.gets == []


async def test_new_clubs_composes_on_its_own_when_no_player_arrived() -> None:
    club = a_club(name="Podgórze Padel")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(clubs={Sport.PADEL: (club.club_id,)}),
        rows=FakeArrivalRows(clubs=[club]),
    )
    shelves = await _shelves(compose, Sport.PADEL)

    assert [shelf.code for shelf in shelves] == [ShelfCode.NEW_CLUBS]


async def test_new_players_composes_on_its_own_when_no_club_arrived() -> None:
    player = a_player(nickname="nadia")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (player.player_id,)}),
        rows=FakeArrivalRows(players=[player]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    shelves = await _shelves(compose, Sport.PADEL)

    assert [shelf.code for shelf in shelves] == [ShelfCode.NEW_PLAYERS]


async def test_new_players_is_composed_before_new_clubs() -> None:
    player = a_player()
    club = a_club()
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(
            players={Sport.PADEL: (player.player_id,)},
            clubs={Sport.PADEL: (club.club_id,)},
        ),
        rows=FakeArrivalRows(players=[player], clubs=[club]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    shelves = await _shelves(compose, Sport.PADEL)

    assert [shelf.code for shelf in shelves] == [
        ShelfCode.NEW_PLAYERS,
        ShelfCode.NEW_CLUBS,
    ]


# -- the windows -------------------------------------------------------------


async def test_the_player_window_is_thirty_days_back_from_the_compose() -> None:
    compose, _, arrivals = _compose(arrivals=FakeNewArrivals(players={Sport.PADEL: ()}))
    await _shelves(compose, Sport.PADEL)

    assert arrivals.player_asks == [
        (Sport.PADEL, shifted(AT, minutes(-NEW_PLAYER_WINDOW)))
    ]


async def test_the_club_window_is_sixty_days_back_from_the_compose() -> None:
    compose, _, arrivals = _compose(arrivals=FakeNewArrivals(clubs={Sport.PADEL: ()}))
    await _shelves(compose, Sport.PADEL)

    assert arrivals.club_asks == [(Sport.PADEL, shifted(AT, minutes(-NEW_CLUB_WINDOW)))]


# -- the caps ----------------------------------------------------------------


async def test_new_players_is_capped_at_eight_and_keeps_the_closest() -> None:
    players = [a_player(nickname=f"p{n}") for n in range(12)]
    # Ranked deliberately against the order they arrive in, so a cap that kept
    # the first eight *found* rather than the first eight *ordered* would show.
    levels = {
        player.player_id: _level(1.0 + 0.3 * (11 - index))
        for index, player in enumerate(players)
    }
    levels[VIEWER] = _level(1.0)
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(
            players={Sport.PADEL: tuple(p.player_id for p in players)}
        ),
        rows=FakeArrivalRows(players=players),
        levels=FakeLevels({Sport.PADEL: levels}),
    )
    shelf = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_PLAYERS)

    assert shelf is not None
    assert len(shelf.cards) == 8
    assert [card.nickname for card in shelf.cards] == [
        f"p{n}" for n in range(11, 3, -1)
    ]


async def test_new_clubs_is_capped_at_six_and_keeps_the_newest() -> None:
    # The set arrives **oldest first**, deliberately: a cap applied to the
    # retrieval order rather than to the composed order would keep the six oldest
    # clubs in the city and call the shelf *new*, and a fixture whose retrieval
    # order already agreed with its arrival order could not tell the two apart.
    clubs = [a_club(name=f"c{n}", joined=days_ago(9 - n)) for n in range(9)]
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(clubs={Sport.PADEL: tuple(c.club_id for c in clubs)}),
        rows=FakeArrivalRows(clubs=clubs),
    )
    shelf = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_CLUBS)

    assert shelf is not None
    assert [card.name for card in shelf.cards] == [f"c{n}" for n in range(8, 2, -1)]


# -- no floor ----------------------------------------------------------------


async def test_neither_shelf_has_a_floor() -> None:
    # There is no such thing as a player who is insufficiently new. A viewer at
    # 1,0 and an arrival at 5,0 is the widest gap the scale allows, and the card
    # is still on the shelf.
    far = a_player(nickname="far")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (far.player_id,)}),
        rows=FakeArrivalRows(players=[far]),
        levels=FakeLevels(
            {Sport.PADEL: {VIEWER: _level(1.0), far.player_id: _level(5.0)}}
        ),
    )
    shelf = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_PLAYERS)

    assert shelf is not None
    assert [card.nickname for card in shelf.cards] == ["far"]


# -- the cards ---------------------------------------------------------------


async def test_a_person_card_carries_the_level_and_its_quiet_marker() -> None:
    player = a_player(nickname="nadia")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (player.player_id,)}),
        rows=FakeArrivalRows(players=[player]),
        levels=FakeLevels(
            {Sport.PADEL: {player.player_id: _level(2.7, provisional=True)}}
        ),
    )
    shelf = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_PLAYERS)

    assert shelf is not None
    card = shelf.cards[0]
    assert isinstance(card, PersonCard)
    assert card.card_type is CardType.PERSON
    assert card.stamp == STAMP
    assert card.level == Level(value=2.7, provisional=True)


async def test_a_club_card_carries_its_name_and_no_distance_it_does_not_have() -> None:
    club = a_club(name="Podgórze Padel")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(clubs={Sport.PADEL: (club.club_id,)}),
        rows=FakeArrivalRows(clubs=[club]),
    )
    shelf = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_CLUBS)

    assert shelf is not None
    card = shelf.cards[0]
    assert isinstance(card, ClubCard)
    assert card.card_type is CardType.CLUB
    assert card.name == "Podgórze Padel"
    assert card.distance_km is None
    assert card.stamp == STAMP


async def test_no_shelf_carries_a_caption() -> None:
    player = a_player()
    club = a_club()
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(
            players={Sport.PADEL: (player.player_id,)},
            clubs={Sport.PADEL: (club.club_id,)},
        ),
        rows=FakeArrivalRows(players=[player], clubs=[club]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    shelves = await _shelves(compose, Sport.PADEL)

    assert [shelf.caption for shelf in shelves] == [None, None]


# -- who is on the shelf -----------------------------------------------------


async def test_the_viewer_is_never_on_her_own_new_players_shelf() -> None:
    me = a_player(nickname="me", who=VIEWER)
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (VIEWER,)}),
        rows=FakeArrivalRows(players=[me]),
        levels=FakeLevels({Sport.PADEL: {VIEWER: _level(3.0)}}),
    )

    assert await _shelves(compose, Sport.PADEL) == ()


async def test_a_player_whose_rating_has_gone_since_the_set_was_cached_is_dropped() -> (
    None
):
    # The set is up to fifteen minutes old and the rating read is live, so a
    # player can be in one and not the other. She is dropped rather than printed
    # at an imputed Level.
    ghost = a_player(nickname="ghost")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (ghost.player_id,)}),
        rows=FakeArrivalRows(players=[ghost]),
        levels=FakeLevels({Sport.PADEL: {}}),
    )

    assert await _shelves(compose, Sport.PADEL) == ()


async def test_a_player_the_row_read_no_longer_finds_is_dropped_silently() -> None:
    gone = uuid4()
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (gone,)}),
        rows=FakeArrivalRows(players=[]),
        levels=FakeLevels({Sport.PADEL: {gone: _level(3.0)}}),
    )

    assert await _shelves(compose, Sport.PADEL) == ()


async def test_one_player_new_at_two_sports_is_one_card_at_her_closest_level() -> None:
    her = a_player(nickname="nadia")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(
            players={
                Sport.PADEL: (her.player_id,),
                Sport.TENNIS: (her.player_id,),
            }
        ),
        rows=FakeArrivalRows(players=[her]),
        levels=FakeLevels(
            {
                Sport.PADEL: {VIEWER: _level(3.0), her.player_id: _level(4.5)},
                Sport.TENNIS: {VIEWER: _level(3.0), her.player_id: _level(3.1)},
            }
        ),
    )
    shelf = _by_code(
        await _shelves(compose, Sport.PADEL, Sport.TENNIS), ShelfCode.NEW_PLAYERS
    )

    assert shelf is not None
    assert len(shelf.cards) == 1
    card = shelf.cards[0]
    assert isinstance(card, PersonCard)
    assert card.level.value == pytest.approx(3.1)


async def test_one_club_selling_two_of_her_sports_is_one_card() -> None:
    club = a_club(name="Both")
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(
            clubs={Sport.PADEL: (club.club_id,), Sport.TENNIS: (club.club_id,)}
        ),
        rows=FakeArrivalRows(clubs=[club]),
    )
    shelf = _by_code(
        await _shelves(compose, Sport.PADEL, Sport.TENNIS), ShelfCode.NEW_CLUBS
    )

    assert shelf is not None
    assert [card.name for card in shelf.cards] == ["Both"]


async def test_the_sports_of_a_filter_are_asked_in_the_registrys_order() -> None:
    # `all` is a set and a set has no order, so composing over it directly would
    # make the shelf's contents depend on hash iteration — reproducible within one
    # process and not between two.
    compose, _, arrivals = _compose()
    await _shelves(compose, Sport.BADMINTON, Sport.PADEL, Sport.SQUASH, Sport.TENNIS)

    assert [sport for sport, _ in arrivals.club_asks] == [
        Sport.PADEL,
        Sport.TENNIS,
        Sport.SQUASH,
        Sport.BADMINTON,
    ]


# -- the cache ---------------------------------------------------------------


async def test_a_set_is_stored_under_city_sport_and_kind() -> None:
    player = a_player()
    club = a_club()
    compose, sets, _ = _compose(
        arrivals=FakeNewArrivals(
            players={Sport.PADEL: (player.player_id,)},
            clubs={Sport.PADEL: (club.club_id,)},
        ),
        rows=FakeArrivalRows(players=[player], clubs=[club]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    await _shelves(compose, Sport.PADEL)

    assert [key for key, _ in sets.puts] == ["?:PADEL:players", "?:PADEL:clubs"]


async def test_a_second_compose_reads_the_set_from_the_cache() -> None:
    player = a_player()
    compose, sets, arrivals = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (player.player_id,)}),
        rows=FakeArrivalRows(players=[player]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    await _shelves(compose, Sport.PADEL)
    await _shelves(compose, Sport.PADEL)

    assert len(arrivals.player_asks) == 1
    assert len(sets.gets) == 4


async def test_the_row_is_read_live_on_every_compose() -> None:
    # A nickname or a club's name changing has to reach the next screen: fifteen
    # minutes of a renamed club is fifteen minutes of a player being told about a
    # venue that no longer goes by that name.
    player = a_player()
    rows = FakeArrivalRows(players=[player])
    compose, _, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (player.player_id,)}),
        rows=rows,
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    await _shelves(compose, Sport.PADEL)
    await _shelves(compose, Sport.PADEL)

    assert len(rows.player_asks) == 2


async def test_an_empty_answer_is_cached_like_any_other() -> None:
    # A city with no new clubs is a fact worth fifteen minutes as much as a city
    # with six; skipping the write would make the empty case the one that pays
    # the full query on every single request.
    compose, sets, arrivals = _compose(
        arrivals=FakeNewArrivals(clubs={Sport.PADEL: ()})
    )
    await _shelves(compose, Sport.PADEL)
    await _shelves(compose, Sport.PADEL)

    assert sets.held["?:PADEL:clubs"] == ()
    assert len(arrivals.club_asks) == 1


async def test_the_cache_holds_identifiers_and_never_a_row() -> None:
    player = a_player(nickname="nadia")
    compose, sets, _ = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (player.player_id,)}),
        rows=FakeArrivalRows(players=[player]),
        levels=FakeLevels({Sport.PADEL: {player.player_id: _level(3.0)}}),
    )
    await _shelves(compose, Sport.PADEL)

    assert sets.held["?:PADEL:players"] == (player.player_id,)
    assert all(isinstance(one, UUID) for one in sets.held["?:PADEL:players"])


async def test_two_viewers_share_a_set_and_not_a_row() -> None:
    her = a_player(nickname="nadia")
    other = uuid4()
    compose, _, arrivals = _compose(
        arrivals=FakeNewArrivals(players={Sport.PADEL: (her.player_id,)}),
        rows=FakeArrivalRows(players=[her]),
        levels=FakeLevels(
            {
                Sport.PADEL: {
                    VIEWER: _level(3.0),
                    other: _level(4.4),
                    her.player_id: _level(4.5),
                }
            }
        ),
    )
    mine = _by_code(await _shelves(compose, Sport.PADEL), ShelfCode.NEW_PLAYERS)
    theirs = _by_code(
        await _shelves(compose, Sport.PADEL, viewer=other), ShelfCode.NEW_PLAYERS
    )

    assert len(arrivals.player_asks) == 1
    assert mine is not None and theirs is not None
    assert mine.cards[0].level == theirs.cards[0].level


def test_the_two_kinds_are_the_only_kinds() -> None:
    assert {kind.value for kind in ArrivalKind} == {"players", "clubs"}
