"""Shelves 4 and 5, as values: two windows, two caps, two comparators, one key.

Everything asserted here is the half of ADR-0051 and ADR-0068 that can be written
down without a clock or a repository. The ordering rules are the substance —
*closeness and never descending* is the difference between a discovery shelf and
a leaderboard, and *newest first and never nearest* is the difference between a
shelf that says **this is new** and one that answers **this is near**.
"""

from uuid import uuid4

from app.kernel import MINUTES_PER_DAY, Sport

from app.modules.now.domain.arrivals import (
    ARRIVAL_SET_TTL,
    CITY_UNKNOWN,
    NEW_CLUB_WINDOW,
    NEW_CLUBS_CAP,
    NEW_PLAYER_WINDOW,
    NEW_PLAYERS_CAP,
    ArrivalKey,
    ArrivalKind,
    Candidate,
    by_arrival,
    by_closeness,
)
from app.modules.now.domain.screen import Level
from tests.unit.arrival_doubles import a_club, a_player, days_ago


def _candidate(level: float, distance: float | None, **player) -> Candidate:
    return Candidate(
        player=a_player(**player),
        level=Level(value=level, provisional=False),
        distance=distance,
    )


# -- the two windows and the two caps ---------------------------------------


def test_new_on_raketa_is_thirty_days_and_new_clubs_is_sixty() -> None:
    assert NEW_PLAYER_WINDOW == 30 * MINUTES_PER_DAY
    assert NEW_CLUB_WINDOW == 60 * MINUTES_PER_DAY


def test_the_caps_are_eight_players_and_six_clubs() -> None:
    # ADR-0068 cut these from 20 and 10: at 320pt a shelf card is nearly full
    # width, so card 10 is nine swipes away, and every shelf ends in a tail card
    # into Find — the overflow has somewhere to go.
    assert NEW_PLAYERS_CAP == 8
    assert NEW_CLUBS_CAP == 6


def test_a_shared_set_is_good_for_fifteen_minutes() -> None:
    assert ARRIVAL_SET_TTL == 15


# -- the key ----------------------------------------------------------------


def test_a_set_is_filed_under_city_then_sport_then_kind() -> None:
    key = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.PLAYERS)
    assert key.key == "Kraków:PADEL:players"


def test_the_two_kinds_of_set_never_share_a_key() -> None:
    players = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.PLAYERS)
    clubs = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.CLUBS)
    assert players.key != clubs.key


def test_two_sports_in_one_city_never_share_a_key() -> None:
    padel = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.CLUBS)
    squash = ArrivalKey(city="Kraków", sport=Sport.SQUASH, kind=ArrivalKind.CLUBS)
    assert padel.key != squash.key


def test_two_cities_never_share_a_key() -> None:
    # One city must never be served another city's new arrivals, and that is true
    # whether or not the field saying which city she is in exists yet (#102).
    here = ArrivalKey(city="Kraków", sport=Sport.PADEL, kind=ArrivalKind.CLUBS)
    there = ArrivalKey(city="Gdańsk", sport=Sport.PADEL, kind=ArrivalKind.CLUBS)
    assert here.key != there.key


def test_a_viewer_with_no_city_still_files_under_a_city_component() -> None:
    # The component stays in the key rather than being dropped until it has a
    # source: a key that *gains* a component later is a key whose old entries
    # answer the wrong city for fifteen minutes on the day it lands.
    unknown = ArrivalKey(city=None, sport=Sport.PADEL, kind=ArrivalKind.PLAYERS)
    assert unknown.key == f"{CITY_UNKNOWN}:PADEL:players"
    assert unknown.key.count(":") == 2


def test_an_empty_city_string_is_the_unknown_city_and_not_a_city_of_its_own() -> None:
    assert (
        ArrivalKey(city="", sport=Sport.PADEL, kind=ArrivalKind.PLAYERS).key
        == ArrivalKey(city=None, sport=Sport.PADEL, kind=ArrivalKind.PLAYERS).key
    )


# -- new players: closeness, never descending -------------------------------


def test_new_players_are_ordered_by_closeness_to_the_viewers_level() -> None:
    far = _candidate(4.8, 2.0, nickname="far")
    near = _candidate(3.0, 0.2, nickname="near")
    middling = _candidate(3.9, 0.9, nickname="middling")

    assert [c.player.nickname for c in by_closeness([far, near, middling])] == [
        "near",
        "middling",
        "far",
    ]


def test_the_shelf_is_never_a_leaderboard() -> None:
    # Descending by Level tells every new player where they rank on the home
    # screen of every stranger in the city, and puts the players the viewer can
    # least enjoy a game with at the front (ADR-0051).
    strongest = _candidate(5.0, 2.0, nickname="strongest")
    weakest = _candidate(1.0, 0.1, nickname="weakest")

    assert [c.player.nickname for c in by_closeness([strongest, weakest])] == [
        "weakest",
        "strongest",
    ]


def test_a_player_the_viewer_cannot_be_compared_against_falls_to_the_back() -> None:
    # There is no floor on this shelf, so *cannot compare* is a position and
    # never an exclusion.
    comparable = _candidate(3.0, 1.9, nickname="comparable")
    incomparable = _candidate(3.0, None, nickname="incomparable")

    assert [c.player.nickname for c in by_closeness([incomparable, comparable])] == [
        "comparable",
        "incomparable",
    ]


def test_a_viewer_with_no_rating_at_all_still_gets_a_shelf_newest_first() -> None:
    # The door case (#78): she taps squash, holds no squash rating, and the shelf
    # composes beneath the door so she can see there are squash players here.
    old = _candidate(3.0, None, nickname="old", joined=days_ago(20))
    new = _candidate(3.0, None, nickname="new", joined=days_ago(1))

    assert [c.player.nickname for c in by_closeness([old, new])] == ["new", "old"]


def test_players_equally_close_are_ordered_newest_first() -> None:
    old = _candidate(3.5, 0.5, nickname="old", joined=days_ago(25))
    new = _candidate(2.5, 0.5, nickname="new", joined=days_ago(2))

    assert [c.player.nickname for c in by_closeness([old, new])] == ["new", "old"]


def test_players_equally_close_and_equally_new_are_ordered_by_nickname() -> None:
    # A creation stamp is a server default that every account written in one
    # transaction shares, so the last key cannot be one — an order that changes
    # between runs is an order nothing can test.
    same = days_ago(3)
    zoe = _candidate(3.5, 0.5, nickname="zoe", joined=same)
    ada = _candidate(3.5, 0.5, nickname="ada", joined=same)

    assert [c.player.nickname for c in by_closeness([zoe, ada])] == ["ada", "zoe"]


def test_ordering_drops_nobody() -> None:
    candidates = [_candidate(3.0, 0.1), _candidate(3.0, None), _candidate(1.0, 2.0)]
    assert len(by_closeness(candidates)) == 3


def test_the_closer_pairing_wins_when_one_player_arrives_at_two_sports() -> None:
    who = uuid4()
    close = _candidate(3.0, 0.1, who=who)
    far = _candidate(4.9, 1.9, who=who)

    assert close.closer_than(far)
    assert not far.closer_than(close)


def test_a_pairing_the_viewer_can_be_compared_against_beats_one_she_cannot() -> None:
    who = uuid4()
    comparable = _candidate(3.0, 1.9, who=who)
    incomparable = _candidate(3.0, None, who=who)

    assert comparable.closer_than(incomparable)
    assert not incomparable.closer_than(comparable)


def test_two_incomparable_pairings_do_not_displace_each_other() -> None:
    who = uuid4()
    one = _candidate(3.0, None, who=who)
    other = _candidate(4.0, None, who=who)

    assert not one.closer_than(other)
    assert not other.closer_than(one)


# -- new clubs: newest first, and never nearest -----------------------------


def test_new_clubs_are_ordered_newest_first() -> None:
    old = a_club(name="old", joined=days_ago(50))
    new = a_club(name="new", joined=days_ago(2))

    assert [club.name for club in by_arrival([old, new])] == ["new", "old"]


def test_a_shelf_that_says_this_is_new_does_not_answer_this_is_near() -> None:
    # ADR-0068: the shelf's title is its claim. Ordering by distance would make a
    # shelf saying *this is new* answer *this is near* instead.
    near_but_older = a_club(name="near", joined=days_ago(50), distance_km=1)
    far_but_newer = a_club(name="far", joined=days_ago(2), distance_km=40)

    assert [club.name for club in by_arrival([near_but_older, far_but_newer])] == [
        "far",
        "near",
    ]


def test_distance_breaks_a_tie_between_two_clubs_that_arrived_together() -> None:
    same = days_ago(9)
    far = a_club(name="far", joined=same, distance_km=30)
    near = a_club(name="near", joined=same, distance_km=3)

    assert [club.name for club in by_arrival([far, near])] == ["near", "far"]


def test_a_club_with_no_distance_sorts_after_one_with_a_distance_in_a_tie() -> None:
    # Absent is not nearest. A distance the platform does not have must not read
    # as zero kilometres.
    same = days_ago(9)
    unknown = a_club(name="unknown", joined=same)
    far = a_club(name="far", joined=same, distance_km=40)

    assert [club.name for club in by_arrival([unknown, far])] == ["far", "unknown"]


def test_clubs_tied_on_everything_are_ordered_by_name() -> None:
    same = days_ago(9)
    zenith = a_club(name="Zenith", joined=same)
    apex = a_club(name="Apex", joined=same)

    assert [club.name for club in by_arrival([zenith, apex])] == ["Apex", "Zenith"]


def test_club_ordering_drops_nobody() -> None:
    assert len(by_arrival([a_club(), a_club(), a_club()])) == 3
