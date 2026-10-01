"""Posting a game, read and posted as the phone does (#546; the mechanics §9;
the screens A5).

Every member is made the way the platform makes one — signed up, a week of
hours, rated, an intent declared, a card saved — and a group is joined over
HTTP. Every claim is read back as a player reads it: the grid, a cell's sheet,
their deck, their live yeses, a game's details.

The claims, one family each:

- **the grid**: a cell's number is the best fits free together with the poster
  at the best hour in its range that has a free court — *never anyone
  overlapping* — and around it the court, a full game's worth, the poster's own
  hours, earlier today and a game already happening; *Who* and the Level range
  narrow who counts, and the range starts as the engine's own window;
- **the sheet**: the fits free then, the free courts home club first with their
  own counts, and rescues the poster fits before posts still filling;
- **posting**: the poster's yes, dealt as up to three versions to the best fits
  as a *Challenge*, refused by its guards with a code each, kept dealt to
  whoever becomes a fit, joined from the sheet, withdrawn, and gone at its
  book-by.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the tenth is a
Saturday, and the club sells padel at 120 zł — 30 zł a seat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.kernel import Sport
from app.modules.proposals.application.propose_games import Proposed
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.modules.proposals.presentation.dependencies import get_booked_games
from tests.api.proposals_world import (
    LIVE_YESES,
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    live_ids,
    makes,
    says_yes,
    sweeps,
    warsaw,
    withdraws,
)
from tests.unit.fake_clock import MovableClock

SATURDAY = date(2026, 10, 10)
SAT_17, SAT_18 = warsaw(10, 17), warsaw(10, 18)


def saturday(*hours: int) -> list[dict]:
    return [{"day": 6, "hour": hour} for hour in hours]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@dataclass
class BookedFor:
    """``BookedGames`` as a test says each player's games are."""

    games: dict[UUID, list[datetime]] = field(default_factory=dict)

    async def starts_of(self, player_id, *, start, end):
        return [at for at in self.games.get(player_id, []) if start <= at < end]


@pytest.fixture
def booked(app) -> BookedFor:
    stand_in = BookedFor()
    app.dependency_overrides[get_booked_games] = lambda: stand_in
    return stand_in


async def members(client, session_factory, payments, *named: str, **overrides):
    return [
        await a_member(client, session_factory, payments, name, **overrides)
        for name in named
    ]


def posting(**overrides) -> dict:
    return {"sport": "PADEL", "kind": "COMPETITIVE", "who": "ANYONE", **overrides}


async def grid_read(client, player: dict, group: UUID, **params):
    return await client.get(
        f"/api/v1/pools/{group}/posting-grid",
        params=posting(**params),
        headers=player["headers"],
    )


async def grid_of(client, player: dict, group: UUID, **params) -> dict:
    read = await grid_read(client, player, group, **params)
    assert read.status_code == 200, read.text
    return read.json()


def cell(grid: dict, day: date, range_: str) -> dict:
    [found] = [
        cell
        for row in grid["days"]
        if row["day"] == day.isoformat()
        for cell in row["cells"]
        if cell["range"] == range_
    ]
    return found


def at(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


async def sheet_of(
    client, player: dict, group: UUID, day: date, range_: str, **params
) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/posting-grid/slot",
        params={**posting(**params), "day": day.isoformat(), "range": range_},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def posts(client, player: dict, group: UUID, club: str, start, **body):
    return await client.post(
        f"/api/v1/pools/{group}/posts",
        json={**posting(**body), "club_id": club, "starts_at": start.isoformat()},
        headers=player["headers"],
    )


async def posted(client, player: dict, group: UUID, club: str, start, **body) -> dict:
    answer = await posts(client, player, group, club, start, **body)
    assert answer.status_code == 201, answer.text
    return answer.json()


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


async def details_of(client, player: dict, proposal_id: str) -> dict:
    read = await client.get(
        f"/api/v1/proposals/{proposal_id}", headers=player["headers"]
    )
    assert read.status_code == 200, read.text
    return read.json()


async def proposes(session_factory, clock, group: UUID) -> Proposed:
    async with session_factory() as session:
        return await build_propose_games(session, clock=clock).execute(group)


def code_of(response) -> str:
    return response.json()["code"]


# --------------------------------------------------------------------------- #
# The grid
# --------------------------------------------------------------------------- #


async def test_a_cell_counts_the_fits_free_at_its_best_hour_never_anyone_overlapping(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    (ola,) = await members(
        client, session_factory, payments, "ola", week=saturday(17, 18)
    )
    early = await members(
        client, session_factory, payments, "kuba", "ewa", week=saturday(17)
    )
    late = await members(
        client, session_factory, payments, "tomek", "ania", "marek", week=saturday(18)
    )
    group = await a_group(client, ola, club, *early, *late)

    grid = await grid_of(client, ola, group)

    evening = cell(grid, SATURDAY, "EVENING")
    # Five overlap her Saturday evening, at two hours: three can play together.
    assert evening["fits_free"] == 3
    assert at(evening["best_starts_at"]) == SAT_18
    assert evening["court_free"] and evening["full_game"]
    assert not evening["outside_your_hours"] and not evening["past"]
    assert not evening["happening"]
    assert grid["week"] == 1 and grid["open_seats"] == 3
    assert [row["day"] for row in grid["days"]][0] == "2026-10-05"
    assert grid["days"][0]["is_today"] and not grid["days"][1]["is_today"]


async def test_every_cell_says_what_is_around_its_number(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    (ola,) = await members(client, session_factory, payments, "ola", week=saturday(17))
    tuesday_mornings = await members(
        client, session_factory, payments, "kuba", "ewa", week=[{"day": 2, "hour": 9}]
    )
    group = await a_group(client, ola, club, *tuesday_mornings)
    clock.move(timedelta(hours=5, minutes=30))

    grid = await grid_of(client, ola, group)
    second = await grid_of(client, ola, group, week=2)

    # No court on a Tuesday morning, and not her hours: two fit, and it says so.
    tuesday = cell(grid, date(2026, 10, 6), "MORNING")
    assert (tuesday["fits_free"], tuesday["court_free"]) == (2, False)
    assert tuesday["outside_your_hours"] and not tuesday["full_game"]
    # Her Saturday has a court and nobody who fits free then: a dead cell.
    evening = cell(grid, SATURDAY, "EVENING")
    assert (evening["fits_free"], evening["court_free"]) == (0, True)
    # Earlier today.
    assert cell(grid, date(2026, 10, 5), "MORNING")["past"]
    assert not cell(grid, date(2026, 10, 5), "EVENING")["past"]
    # The week after starts seven days on.
    assert second["days"][0]["day"] == "2026-10-12"
    assert cell(second, date(2026, 10, 17), "EVENING")["court_free"]


async def test_the_level_range_starts_as_the_engine_s_window_and_may_only_be_narrowed(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    (ola, kuba) = await members(client, session_factory, payments, "ola", "kuba")
    (ewa,) = await members(client, session_factory, payments, "ewa", mu=2.9)
    (tomek,) = await members(client, session_factory, payments, "tomek", mu=2.2)
    group = await a_group(client, ola, club, kuba, ewa, tomek)

    whole = await grid_of(client, ola, group)
    narrowed = await grid_of(client, ola, group, level_low=2.4)
    wider = await grid_read(client, ola, group, level_high=3.2)
    inverted = await grid_read(client, ola, group, level_low=2.8, level_high=2.6)

    # Her Level is 2,5 and the competitive window 0,55 either side of it.
    assert whole["engine_level_range"] == {"low": 1.95, "high": 3.05}
    assert whole["level_range"] == whole["engine_level_range"]
    assert cell(whole, SATURDAY, "EVENING")["fits_free"] == 3
    assert narrowed["level_range"] == {"low": 2.4, "high": 3.05}
    assert cell(narrowed, SATURDAY, "EVENING")["fits_free"] == 2
    assert wider.status_code == 400
    assert code_of(wider) == "level_range_too_wide"
    assert wider.json()["details"] == {"low": 1.95, "high": 3.05}
    assert (inverted.status_code, code_of(inverted)) == (400, "level_range_inverted")


async def test_who_counts_only_the_members_the_post_is_for(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    (ola, ewa) = await members(client, session_factory, payments, "ola", "ewa")
    men = await members(
        client, session_factory, payments, "kuba", "tomek", gender="MAN"
    )
    (ania,) = await members(
        client, session_factory, payments, "ania", gender_preference="WOMEN_ONLY"
    )
    group = await a_group(client, ola, club, ewa, *men, ania)

    def evening_count(grid: dict) -> int:
        return cell(grid, SATURDAY, "EVENING")["fits_free"]

    assert evening_count(await grid_of(client, ola, group)) == 4
    assert evening_count(await grid_of(client, ola, group, who="WOMEN")) == 2
    # Both men and Ewa; Ania plays with women only.
    assert evening_count(await grid_of(client, ola, group, who="MIXED_PAIRS")) == 3


async def test_a_grid_is_refused_where_nothing_could_be_posted(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    (ola,) = await members(client, session_factory, payments, "ola")
    (tennis,) = await members(
        client, session_factory, payments, "kuba", sports=(Sport.TENNIS,)
    )
    (stranger,) = await members(client, session_factory, payments, "zosia")
    group = await a_group(client, ola, club, tennis)

    outsider = await grid_read(client, stranger, group)
    unrated = await grid_read(client, tennis, group)
    singles = await grid_read(client, ola, group, sport="TENNIS", who="MIXED_PAIRS")
    not_hers = await grid_read(client, ola, group, who="MEN")

    assert (outsider.status_code, code_of(outsider)) == (404, "pool_not_found")
    assert (unrated.status_code, code_of(unrated)) == (409, "not_rated_in_the_sport")
    assert (singles.status_code, code_of(singles)) == (
        400,
        "mixed_pairs_only_in_doubles",
    )
    assert (not_hers.status_code, code_of(not_hers)) == (409, "who_leaves_you_out")


# --------------------------------------------------------------------------- #
# The sheet
# --------------------------------------------------------------------------- #


async def test_a_sheet_lists_the_fits_free_then_and_the_free_courts_home_club_first(
    client, session_factory, payments, clock
):
    home = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    near = await a_club_selling(
        client,
        name="Kazimierz Padel",
        point=(50.065, 19.955),
        hours=[(6, 18)],
        padel_grosze=100_00,
    )
    (ola,) = await members(client, session_factory, payments, "ola")
    (kuba,) = await members(
        client, session_factory, payments, "kuba", week=saturday(17, 18)
    )
    (ewa,) = await members(
        client, session_factory, payments, "ewa", mu=2.9, week=saturday(17, 18)
    )
    (tomek,) = await members(
        client, session_factory, payments, "tomek", week=saturday(18)
    )
    group = await a_group(client, ola, home, kuba, ewa, tomek)

    sheet = await sheet_of(client, ola, group, SATURDAY, "EVENING")

    assert sheet["cell"]["fits_free"] == 3
    # Best fit first: Kuba and Tomek at her Level, then Ewa.
    assert [fit["name"] for fit in sheet["fits"]][-1] == "ewa"
    assert {fit["name"] for fit in sheet["fits"]} == {"kuba", "ewa", "tomek"}
    assert all(fit["forecast"] is not None for fit in sheet["fits"])
    assert [
        (court["club"]["id"], at(court["starts_at"]), court["fits_free"])
        for court in sheet["free_courts"]
    ] == [(home, SAT_17, 2), (home, SAT_18, 3), (near, SAT_18, 3)]
    assert [court["home_club"] for court in sheet["free_courts"]] == [True, True, False]
    assert [court["share_grosze"] for court in sheet["free_courts"]] == [
        30_00,
        30_00,
        25_00,
    ]
    assert at(sheet["free_courts"][0]["book_by"]) == SAT_17 - timedelta(hours=2)
    assert sheet["rescues"] == [] and sheet["posts"] == []


async def test_already_happening_here_lists_rescues_first_then_posts_still_filling(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        "ania",
        "marek",
        "zosia",
    )
    ola, kuba, ewa, tomek, ania, marek, zosia = crowd
    group = await a_group(client, ola, club, *crowd[1:])
    # Saturday at 17:00 is booked by four of them, and Tomek leaves it.
    four = (kuba, ewa, tomek, ania)
    game = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    for player in four:
        assert (await says_yes(client, player, game)).status_code == 200
    left = await client.post(
        f"/api/v1/bookings/{game}/departure", headers=tomek["headers"]
    )
    assert left.status_code == 200, left.text
    # Marek posts Saturday at 18:00.
    marek_s = await posted(client, marek, group, club, SAT_18)

    grid = await grid_of(client, zosia, group)
    sheet = await sheet_of(client, zosia, group, SATURDAY, "EVENING")

    assert cell(grid, SATURDAY, "EVENING")["happening"]
    assert [row["booking_id"] for row in sheet["rescues"]] == [str(game)]
    assert sheet["rescues"][0]["share_grosze"] == 30_00
    [post] = sheet["posts"]
    assert post["proposal_id"] == marek_s["proposal_id"]
    assert post["challenger"]["name"] == "marek"
    assert [tile["name"] for tile in post["people_in"]] == ["marek"]
    assert post["open_seats"] == 3


# --------------------------------------------------------------------------- #
# Posting
# --------------------------------------------------------------------------- #


async def test_posting_is_the_poster_s_yes_dealt_to_their_best_fits_as_a_challenge(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola,) = await members(client, session_factory, payments, "ola")
    fits = await members(
        client,
        session_factory,
        payments,
        "kuba",
        "ewa",
        "tomek",
        "ania",
        "marek",
        "zosia",
        "piotr",
        week=saturday(18),
    )
    group = await a_group(client, ola, club, *fits)

    post = await posted(client, ola, group, club, SAT_18)

    # Seven fits: two full sets, and one waits for a no.
    assert (post["versions"], post["dealt_to"], post["open_seats"]) == (2, 6, 3)
    dealt = [fit for fit in fits if await deck_of(client, fit, group)]
    assert len(dealt) == 6
    for fit in dealt:
        [card] = await deck_of(client, fit, group)
        assert card["proposal_id"] == post["proposal_id"]
        assert card["type"] == "CHALLENGE"
        assert card["challenger"]["name"] == "ola"
        assert card["in_count"] == 1
    assert await live_ids(client, ola) == [post["proposal_id"]]
    assert (await details_of(client, ola, post["proposal_id"]))["status"] == "FILLING"


async def test_a_post_is_dealt_only_to_whom_it_is_for_and_a_yes_held_to_it(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, ewa, ania) = await members(
        client, session_factory, payments, "ola", "ewa", "ania"
    )
    (kuba,) = await members(client, session_factory, payments, "kuba", gender="MAN")
    group = await a_group(client, ola, club, ewa, ania, kuba)

    post = await posted(client, ola, group, club, SAT_18, who="WOMEN")
    joining = await says_yes(client, kuba, UUID(post["proposal_id"]))

    assert (post["versions"], post["dealt_to"]) == (1, 2)
    assert await deck_of(client, kuba, group) == []
    assert (joining.status_code, code_of(joining)) == (409, "no_longer_fits")


async def test_a_post_keeps_being_dealt_to_whoever_becomes_a_fit(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, kuba) = await members(client, session_factory, payments, "ola", "kuba")
    group = await a_group(client, ola, club, kuba)
    post = await posted(client, ola, group, club, SAT_18)
    (ewa,) = await members(client, session_factory, payments, "ewa")
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=ewa["headers"]
    )
    assert joined.status_code in (200, 201), joined.text

    await proposes(session_factory, clock, group)

    [card] = await deck_of(client, ewa, group)
    assert card["proposal_id"] == post["proposal_id"]
    assert card["type"] == "CHALLENGE"


async def test_a_member_never_dealt_a_post_joins_it_from_the_sheet(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    crowd = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek", "ania"
    )
    ola, *others = crowd
    group = await a_group(client, ola, club, *others)
    post = await posted(client, ola, group, club, SAT_18)
    [waiting] = [fit for fit in others if not await deck_of(client, fit, group)]
    [shown] = (await sheet_of(client, waiting, group, SATURDAY, "EVENING"))["posts"]

    joined = await says_yes(client, waiting, UUID(shown["proposal_id"]))

    assert shown["proposal_id"] == post["proposal_id"]
    assert joined.status_code == 200, joined.text
    assert joined.json()["open_seats"] == 2
    assert await live_ids(client, waiting) == [post["proposal_id"]]


async def test_a_member_who_could_not_be_dealt_a_post_cannot_join_it(
    client, session_factory, payments, clock
):
    home = await a_club_selling(client, hours=[(6, 18)])
    near = await a_club_selling(
        client, name="Kazimierz Padel", point=(50.065, 19.955), hours=[(6, 18)]
    )
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        "ania",
        "piotr",
    )
    ola, kuba, ewa, tomek, ania, piotr = crowd
    (busy,) = await members(
        client, session_factory, payments, "zosia", week=[{"day": 1, "hour": 9}]
    )
    group = await a_group(client, ola, home, kuba, ewa, tomek, ania, piotr, busy)
    # Ania is booked at the other club at the same hour.
    game = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=near,
        start=SAT_18,
        versions=((kuba, ewa, tomek, ania),),
    )
    for player in (kuba, ewa, tomek, ania):
        assert (await says_yes(client, player, game)).status_code == 200
    post = await posted(client, ola, group, home, SAT_18)

    double = await says_yes(client, ania, UUID(post["proposal_id"]))
    not_free = await says_yes(client, busy, UUID(post["proposal_id"]))

    assert (double.status_code, code_of(double)) == (409, "post_not_open_to_you")
    assert (not_free.status_code, code_of(not_free)) == (409, "post_not_open_to_you")


async def test_only_a_post_is_joined_by_somebody_it_was_never_dealt_to(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    crowd = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek", "ania"
    )
    group = await a_group(client, crowd[0], club, *crowd[1:])
    pick = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_18,
        versions=(tuple(crowd[:4]),),
    )

    stranger = await says_yes(client, crowd[4], pick)

    assert (stranger.status_code, code_of(stranger)) == (404, "proposal_not_found")


async def test_a_mixed_pairs_post_is_dealt_two_men_and_two_women(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, ewa) = await members(client, session_factory, payments, "ola", "ewa")
    men = await members(
        client, session_factory, payments, "kuba", "tomek", "marek", gender="MAN"
    )
    group = await a_group(client, ola, club, ewa, *men)

    post = await posted(client, ola, group, club, SAT_18, who="MIXED_PAIRS")

    # A woman and two men beside her: one full set, and a man waits.
    assert (post["versions"], post["dealt_to"]) == (1, 3)
    assert await deck_of(client, ewa, group)
    assert len([man for man in men if await deck_of(client, man, group)]) == 2
    for man in men:
        for card in await deck_of(client, man, group):
            for side in (card["sides"]["yours"], card["sides"]["theirs"]):
                assert len({tile["name"] for tile in side} & {"ola", "ewa"}) == 1


async def test_a_mixed_pairs_game_takes_no_third_man_and_books_a_man_and_a_woman_a_side(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, ewa) = await members(client, session_factory, payments, "ola", "ewa")
    (kuba,) = await members(
        client, session_factory, payments, "kuba", mu=2.75, gender="MAN"
    )
    (tomek,) = await members(
        client, session_factory, payments, "tomek", mu=2.25, gender="MAN"
    )
    (marek,) = await members(client, session_factory, payments, "marek", gender="MAN")
    group = await a_group(client, ola, club, ewa, kuba, tomek, marek)
    post = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_18,
        poster=ola,
        versions=((kuba, tomek, ewa),),
        posted_for=PostedFor(
            who=Who.MIXED_PAIRS, levels=LevelRange(low=1.95, high=3.05)
        ),
    )
    for man in (kuba, tomek):
        assert (await says_yes(client, man, post)).status_code == 200

    third = await says_yes(client, marek, post)
    booked = await says_yes(client, ewa, post)

    assert (third.status_code, code_of(third)) == (409, "no_longer_fits")
    assert booked.status_code == 200, booked.text
    booking = await client.get(
        f"/api/v1/bookings/{booked.json()['booked']['booking_id']}",
        headers=ola["headers"],
    )
    assert booking.status_code == 200, booking.text
    # The two women against the two men would be the evener game: a mixed
    # pairs game stands one of each a side all the same.
    for side in booking.json()["sides"].values():
        assert len({tile["name"] for tile in side} & {"ola", "ewa"}) == 1


async def test_a_paused_yes_does_not_come_back_as_a_third_man_on_a_mixed_pairs_game(
    client, session_factory, payments, clock, mailbox
):
    club = await a_club_selling(client, hours=[(6, 17), (7, 10)])
    (ewa, ania, ola, zosia) = await members(
        client, session_factory, payments, "ewa", "ania", "ola", "zosia"
    )
    (kuba, tomek, marek, piotr) = await members(
        client,
        session_factory,
        payments,
        "kuba",
        "tomek",
        "marek",
        "piotr",
        gender="MAN",
    )
    group = await a_group(
        client, ewa, club, ania, ola, zosia, kuba, tomek, marek, piotr
    )
    one_a_week = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=kuba["headers"],
    )
    assert one_a_week.status_code == 200, one_a_week.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 10),
        poster=ewa,
        versions=((kuba, tomek, ania),),
        posted_for=PostedFor(
            who=Who.MIXED_PAIRS, levels=LevelRange(low=1.95, high=3.05)
        ),
    )
    assert (await says_yes(client, kuba, sunday)).status_code == 200
    # Saturday's game books Kuba's one game a week, and pauses his Sunday yes.
    saturday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_17,
        versions=((kuba, piotr, ola, zosia),),
    )
    for player in (piotr, ola, zosia, kuba):
        assert (await says_yes(client, player, saturday)).status_code == 200
    assert str(sunday) not in await live_ids(client, kuba)
    # Two other men are In on Sunday's while his yes waits.
    assert (await says_yes(client, tomek, sunday)).status_code == 200
    assert (await says_yes(client, marek, sunday)).status_code == 200

    left = await client.post(
        f"/api/v1/bookings/{saturday}/departure", headers=kuba["headers"]
    )
    assert left.status_code == 200, left.text
    await mailbox.drain()

    assert str(sunday) not in await live_ids(client, kuba)
    details = await details_of(client, ewa, str(sunday))
    assert details["status"] == "FILLING"


# --------------------------------------------------------------------------- #
# The guards
# --------------------------------------------------------------------------- #


async def test_a_post_needs_a_saved_method_and_at_most_two_live(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18), (7, 17)])
    (ola, kuba) = await members(client, session_factory, payments, "ola", "kuba")
    (no_card,) = await members(client, session_factory, payments, "ewa", card=False)
    group = await a_group(client, ola, club, kuba, no_card)

    unchargeable = await posts(client, no_card, group, club, SAT_17)
    await posted(client, ola, group, club, SAT_17)
    await posted(client, ola, group, club, SAT_18)
    third = await posts(client, ola, group, club, warsaw(11, 17))

    assert (unchargeable.status_code, code_of(unchargeable)) == (
        409,
        "payment_method_required",
    )
    assert (third.status_code, code_of(third)) == (409, "live_posts_exhausted")
    assert third.json()["details"] == {"cap": 2}


async def test_a_post_in_a_week_whose_games_are_booked_is_refused(
    client, session_factory, payments, clock, booked
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, kuba) = await members(client, session_factory, payments, "ola", "kuba")
    group = await a_group(client, ola, club, kuba)
    booked.games[ola["id"]] = [warsaw(7, 19), warsaw(8, 19)]

    refused = await posts(client, ola, group, club, SAT_18)

    assert (refused.status_code, code_of(refused)) == (409, "games_per_week_booked")
    assert refused.json()["details"] == {"games_per_week": 2, "week": "2026-10-05"}


async def test_a_post_at_an_hour_the_poster_plays_or_nobody_fits_is_refused(
    client, session_factory, payments, clock, booked
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18), (7, 9)])
    (ola,) = await members(client, session_factory, payments, "ola")
    (kuba,) = await members(
        client, session_factory, payments, "kuba", week=saturday(17, 18)
    )
    group = await a_group(client, ola, club, kuba)
    booked.games[ola["id"]] = [SAT_18]

    playing = await posts(client, ola, group, club, SAT_18)
    nobody = await posts(client, ola, group, club, warsaw(11, 9))
    unsold = await posts(client, ola, group, club, warsaw(10, 19))

    assert (playing.status_code, code_of(playing)) == (409, "you_play_then")
    assert (nobody.status_code, code_of(nobody)) == (409, "nobody_fits_then")
    assert (unsold.status_code, code_of(unsold)) == (409, "court_hour_not_for_sale")


# --------------------------------------------------------------------------- #
# Withdrawing, and the book-by
# --------------------------------------------------------------------------- #


async def test_the_poster_withdrawing_leaves_the_game_to_those_in_or_takes_it_away(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    crowd = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek"
    )
    ola, kuba, ewa, tomek = crowd
    group = await a_group(client, ola, club, kuba, ewa, tomek)
    carried = await posted(client, ola, group, club, SAT_17)
    alone = await posted(client, ola, group, club, SAT_18)
    assert (
        await says_yes(client, kuba, UUID(carried["proposal_id"]))
    ).status_code == 200

    assert (
        await withdraws(client, ola, UUID(carried["proposal_id"]))
    ).status_code == 204
    assert (await withdraws(client, ola, UUID(alone["proposal_id"]))).status_code == 204

    # The group challenged you: the game carries on without her name.
    cards = {card["proposal_id"]: card for card in await deck_of(client, ewa, group)}
    assert cards[carried["proposal_id"]]["challenger"] is None
    assert cards[carried["proposal_id"]]["type"] == "CHALLENGE"
    assert alone["proposal_id"] not in cards
    assert (await details_of(client, kuba, carried["proposal_id"]))[
        "status"
    ] == "FILLING"
    assert (await details_of(client, ola, alone["proposal_id"]))[
        "status"
    ] == "WITHDRAWN"


async def test_a_post_not_full_by_its_book_by_disappears(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 18)])
    (ola, kuba) = await members(client, session_factory, payments, "ola", "kuba")
    group = await a_group(client, ola, club, kuba)
    post = await posted(client, ola, group, club, SAT_18)
    assert await deck_of(client, kuba, group)

    # Its book-by: the club's two hours' notice before the hour.
    clock.move(SAT_18 - timedelta(hours=2) - MONDAY_MORNING)
    swept = await sweeps(session_factory, clock)

    assert swept.proposals == 1
    assert await deck_of(client, kuba, group) == []
    read = await client.get(LIVE_YESES, headers=ola["headers"])
    assert read.json()["yeses"] == []
    assert (await details_of(client, ola, post["proposal_id"]))["status"] == "EXPIRED"
