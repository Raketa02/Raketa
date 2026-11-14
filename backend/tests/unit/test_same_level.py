"""*Same competitive level players*' rules, at the pure seam (#794;
``docs/adr/0204`` §4, §7; the home-rows mechanics §6, §9).

The % is handed in as a function, so these tests use a plain one — 100 less a
hundred per point of gap, less fifty per point of the two σ — and the API tests
hold the real one against the matcher's own forecast.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport
from app.modules.discovery.domain.levels import Band, CurrentLevel, Estimate
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.same_level import (
    GOOD_MATCH,
    ON_THE_ROW,
    Comparison,
    SameLevelPlayer,
    SameLevelKey,
    Reach,
    RowOfTen,
    compared,
    is_fresh,
    same_level_player,
)

TOMEK = UUID(int=1)
ESTABLISHED = Band(name="Established", lower=2.7, upper=3.8)


def plain_even(sport: Sport, yours: Estimate, theirs: Estimate) -> int:
    return round(
        100 - 100 * abs(yours.mu - theirs.mu) - 50 * (yours.sigma + theirs.sigma)
    )


def level(
    player: UUID, sport: Sport, mu: float, sigma: float = 0.1, results: int = 0
) -> CurrentLevel:
    return CurrentLevel(
        player_id=player,
        sport=sport,
        mu=mu,
        sigma=sigma,
        band=ESTABLISHED,
        results=results,
    )


def mine(*levels: CurrentLevel) -> dict[Sport, CurrentLevel]:
    return {one.sport: one for one in levels}


def a_player(player: int, pct: int, level_gap: float = 0.0) -> SameLevelPlayer:
    comparison = Comparison(
        sport=Sport.PADEL,
        your_level=2.71,
        their_level=round(2.71 + level_gap, 2),
        your_band=ESTABLISHED,
        percent_even=pct,
    )
    return SameLevelPlayer(
        player_id=UUID(int=player), shown=comparison, comparisons=(comparison,)
    )


# --------------------------------------------------------------------------- #
# Each shared sport compared, the evenest shown
# --------------------------------------------------------------------------- #


def test_every_shared_sport_is_compared_most_even_first():
    kuba = UUID(int=2)
    reader = mine(level(TOMEK, Sport.PADEL, 2.71), level(TOMEK, Sport.TENNIS, 3.10))

    comparisons = compared(
        reader,
        [
            level(kuba, Sport.TENNIS, 3.35),
            level(kuba, Sport.PADEL, 2.80),
            level(kuba, Sport.SQUASH, 2.00),
        ],
        plain_even,
    )

    assert [(one.sport, one.percent_even) for one in comparisons] == [
        (Sport.PADEL, 81),
        (Sport.TENNIS, 65),
    ]
    padel = comparisons[0]
    assert padel.your_level == 2.71 and padel.their_level == 2.80
    assert round(padel.level_gap, 2) == 0.09
    assert padel.your_band == ESTABLISHED


def test_two_sports_alike_go_to_the_smaller_gap_then_the_sport_order():
    ola = UUID(int=3)
    reader = mine(
        level(TOMEK, Sport.PADEL, 2.0, sigma=0.0),
        level(TOMEK, Sport.TENNIS, 2.0, sigma=0.2),
        level(TOMEK, Sport.SQUASH, 2.0, sigma=0.0),
    )

    comparisons = compared(
        reader,
        [
            # Both read 90: the tennis gap is the smaller.
            level(ola, Sport.PADEL, 2.10, sigma=0.0),
            level(ola, Sport.TENNIS, 2.0, sigma=0.0),
            # 90 too, at padel's gap: padel comes first in the app's order.
            level(ola, Sport.SQUASH, 1.90, sigma=0.0),
        ],
        plain_even,
    )

    assert [one.sport for one in comparisons] == [
        Sport.TENNIS,
        Sport.PADEL,
        Sport.SQUASH,
    ]


def test_the_card_shows_the_evenest_sport_or_the_sport_asked():
    kuba = UUID(int=2)
    comparisons = compared(
        mine(level(TOMEK, Sport.PADEL, 2.71), level(TOMEK, Sport.TENNIS, 3.10)),
        [level(kuba, Sport.PADEL, 2.80), level(kuba, Sport.TENNIS, 3.35)],
        plain_even,
    )

    evenest = same_level_player(kuba, comparisons, in_sport=None)
    in_tennis = same_level_player(kuba, comparisons, in_sport=Sport.TENNIS)

    assert evenest is not None and evenest.shown.sport is Sport.PADEL
    assert in_tennis is not None and in_tennis.shown.sport is Sport.TENNIS
    # The sheet keeps every shared sport, most even first, either way.
    assert in_tennis.comparisons == evenest.comparisons == comparisons
    assert same_level_player(kuba, comparisons, in_sport=Sport.SQUASH) is None
    assert same_level_player(kuba, (), in_sport=None) is None


# --------------------------------------------------------------------------- #
# The order: best % first, then the smaller gap, then the player id
# --------------------------------------------------------------------------- #


def test_best_first_is_the_percent_then_the_smaller_gap_then_the_id():
    ordered = sorted(
        [
            a_player(5, 80, level_gap=0.10),
            a_player(4, 80, level_gap=-0.05),
            a_player(3, 80, level_gap=0.05),
            a_player(2, 91, level_gap=0.30),
        ],
        key=lambda one: one.key.order,
    )

    assert [one.player_id.int for one in ordered] == [2, 3, 4, 5]


def test_a_key_tells_who_is_behind_it():
    cursor = a_player(3, 80, level_gap=0.05).key

    assert a_player(4, 80, level_gap=0.05).key.is_behind(cursor)
    assert a_player(1, 80, level_gap=0.06).key.is_behind(cursor)
    assert a_player(9, 79, level_gap=0.0).key.is_behind(cursor)
    assert not a_player(3, 80, level_gap=0.05).key.is_behind(cursor)
    assert not a_player(1, 80, level_gap=0.05).key.is_behind(cursor)
    assert not a_player(9, 81, level_gap=0.40).key.is_behind(cursor)


# --------------------------------------------------------------------------- #
# What a window settles
# --------------------------------------------------------------------------- #


def test_a_window_settles_whoever_nobody_beyond_it_could_come_before():
    """Beyond a window of 0,08 nobody reads more than its ceiling, and anybody
    who reads it exactly is further away than 0,08."""

    reach = Reach(ceiling=85, width=0.08)

    assert reach.settles(a_player(1, 86, level_gap=0.30))
    assert reach.settles(a_player(1, 85, level_gap=0.07))
    assert not reach.settles(a_player(1, 85, level_gap=0.08))
    assert not reach.settles(a_player(1, 84, level_gap=0.0))


def test_a_key_is_a_card_s_shown_sport():
    player = a_player(7, 77, level_gap=-0.12)

    assert player.key == SameLevelKey(
        percent_even=77, distance=0.12, player_id=UUID(int=7)
    )


# --------------------------------------------------------------------------- #
# The row of 10: fresh good matches first, then gaps
# --------------------------------------------------------------------------- #


def test_fresh_is_a_good_match_not_connected_and_not_rested():
    good = a_player(1, GOOD_MATCH)
    weaker = a_player(1, GOOD_MATCH - 1)

    assert is_fresh(good, Relation.NONE, rested=False)
    assert is_fresh(good, Relation.ASKED_YOU, rested=False)
    assert not is_fresh(good, Relation.SENT, rested=False)
    assert not is_fresh(good, Relation.FRIEND, rested=False)
    assert not is_fresh(good, Relation.NONE, rested=True)
    assert not is_fresh(weaker, Relation.NONE, rested=False)


def fill(matches, relations=None, rested=frozenset()) -> RowOfTen:
    row = RowOfTen()
    for player in matches:
        if row.full:
            break
        row.take(
            player,
            relation=(relations or {}).get(player.player_id.int, Relation.NONE),
            rested=player.player_id.int in rested,
        )
    return row


def test_tomeks_row_seven_fresh_then_zofia_ania_and_piotr():
    """The mechanics §6.8: 7 fresh good matches, then Zofia (a friend, 91%),
    Ania (request sent, 90%) and Piotr (a stranger, 60%)."""

    zofia, ania, piotr = a_player(100, 91), a_player(101, 90), a_player(102, 60)
    fresh = [a_player(n, 89 - n) for n in range(7)]
    stream = [zofia, ania, *fresh, piotr, a_player(103, 55), a_player(104, 50)]

    row = fill(stream, relations={100: Relation.FRIEND, 101: Relation.SENT})

    assert row.row() == (*fresh, zofia, ania, piotr)


def test_a_new_fresh_match_takes_the_weakest_gap():
    """Marta starts playing at 85%: she joins the fresh ones and Piotr leaves.
    One more fresh match and Ania leaves; another, and Zofia does."""

    zofia, ania, piotr = a_player(100, 91), a_player(101, 90), a_player(102, 60)
    fresh = [a_player(n, 89 - n) for n in range(7)]
    marta = a_player(50, 85, level_gap=0.01)
    connected = {100: Relation.FRIEND, 101: Relation.SENT}

    def row_with(*extra: SameLevelPlayer) -> tuple[SameLevelPlayer, ...]:
        stream = sorted([zofia, ania, piotr, *fresh, *extra], key=lambda m: m.key.order)
        return fill(stream, connected).row()

    with_marta = row_with(marta)
    assert marta in with_marta and piotr not in with_marta
    assert with_marta[-2:] == (zofia, ania)

    one_more = row_with(marta, a_player(51, 75))
    assert ania not in one_more and one_more[-1] == zofia

    two_more = row_with(marta, a_player(51, 75), a_player(52, 74))
    assert zofia not in two_more and len(two_more) == ON_THE_ROW


def test_a_rested_player_comes_back_in_a_gap():
    rested = a_player(1, 95)
    row = fill([rested, a_player(2, 80), a_player(3, 40)], rested=frozenset({1})).row()

    assert row == (a_player(2, 80), rested, a_player(3, 40))


def test_the_row_stops_once_ten_fresh_are_taken():
    stream = [a_player(n, 95 - n) for n in range(ON_THE_ROW)]
    row = RowOfTen()
    for player in stream:
        row.take(player, relation=Relation.NONE, rested=False)

    assert row.full
    assert row.row() == tuple(stream)


def test_the_row_waits_while_a_fresh_match_could_still_come():
    """Ten taken, two of them gaps — but every one is 70% or more, so a
    later fresh match would still take a gap's place."""

    row = RowOfTen()
    for n in range(ON_THE_ROW):
        row.take(
            a_player(n, 90 - n),
            relation=Relation.FRIEND if n < 2 else Relation.NONE,
            rested=False,
        )
    assert not row.full

    row.take(a_player(20, 72), relation=Relation.NONE, rested=False)
    assert not row.full
    row.take(a_player(21, 50), relation=Relation.NONE, rested=False)
    assert row.full
    assert [one.player_id.int for one in row.row()] == [2, 3, 4, 5, 6, 7, 8, 9, 20, 0]


def test_fewer_than_ten_are_all_shown():
    zofia, stranger = a_player(1, 91), a_player(2, 40)

    assert fill([zofia, stranger], relations={1: Relation.FRIEND}).row() == (
        zofia,
        stranger,
    )
    assert fill([zofia, stranger]).row() == (zofia, stranger)
