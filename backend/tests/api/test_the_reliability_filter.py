"""**Marta's evenings stay safe** — the reliability filter (``docs/adr/0195`` §6;
#661, PRD #649).

Marta switches on *Play only with players of at least High reliability*. From
that moment the pair rule has one more clause, asked like a block's: **a pair is
unfit when either player's minimum is above the other's band**, and **New passes
every minimum**. So:

- **Sergio** — 65, Medium, with three games played through behind him — is never
  dealt with her, never offered a seat on her game, never fits her post, and his
  yes never lands beside hers; and the same holds the other way round.
- **Yeses given before** she switched it on, or before he dropped below it,
  **stand**, and **booked games never change**.
- **Nerea**, New after two evenings she never came to, passes.
- Marta's own record reads how many players in her groups her filter hides; the
  record of a player somebody filters out tells them, naming nobody, the figure
  that brings them back.

Every act is taken over HTTP as the phone takes it, and every claim is read where
a player would read it — the deck, the details, Fill in, the posting sheet, Home,
the record. A figure is made the honest way, out of games on the record, each
dated before the clock.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the games are on
**Saturday 10 October**.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.modules.proposals.application.propose_games import DueForProposing
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    live_ids,
    makes,
    says_yes,
    warsaw,
)
from tests.api.reliability_world import (
    AT_75,
    LOW_AT_15,
    MISSED,
    NEW_AT_50,
    SERGIO_AT_65,
    a_history,
)
from tests.api.test_rescues import confirms, refused_rescuer
from tests.unit.fake_clock import MovableClock

FILTER = "/api/v1/players/me/reliability-filter"
SATURDAY = date(2026, 10, 10)
SAT_18, SAT_19 = warsaw(10, 18), warsaw(10, 19)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def switches_on(client, player: dict, minimum: str | None = "HIGH") -> None:
    answered = await client.put(
        FILTER, json={"minimum": minimum}, headers=player["headers"]
    )
    assert answered.status_code == 204, answered.text


async def own_record(client, player: dict) -> dict:
    read = await client.get("/api/v1/players/me/record", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


def names_on(card: dict) -> set[str]:
    return {
        tile["name"] for tile in (*card["sides"]["yours"], *card["sides"]["theirs"])
    }


def ids_of(cards: list[dict]) -> list[str]:
    return [card["proposal_id"] for card in cards]


async def proposes(session_factory, clock, group: UUID) -> None:
    async with session_factory() as session:
        await build_propose_games(session, clock=clock).execute(group)


async def fill_in(client, player: dict, group: UUID) -> list[str]:
    read = await client.get(
        f"/api/v1/pools/{group}/fill-in",
        params={"sport": "PADEL"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return [row["booking_id"] for row in read.json()["seats_to_fill"]]


async def home_of(client, player: dict) -> list[dict]:
    read = await client.get("/api/v1/home", headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["games"]


async def books(client, session_factory, clock, *, group, club, four, start):
    """The four's game at ``start``, booked by the last of their yeses."""

    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=start,
        versions=(tuple(four),),
    )
    for player in four:
        said = await says_yes(client, player, proposal)
        assert said.status_code == 200, said.text
    return said.json()["booked"]["booking_id"]


def code_of(response) -> str:
    return response.json()["code"]


# --------------------------------------------------------------------------- #
# The world
# --------------------------------------------------------------------------- #


@pytest.fixture
async def club(client) -> str:
    """Bonarka Arena, selling padel at every hour of the week."""

    return await a_club_selling(client)


@pytest.fixture
async def crowd(client, session_factory, payments) -> dict[str, dict]:
    """Marta, Sergio (65 · Medium), Nerea (50 · New), and Ola and Kuba, who
    nothing has happened to — every one at padel 2,5, free every hour,
    competitive, with a card that pays."""

    people = {
        name: await a_member(client, session_factory, payments, name)
        for name in ("marta", "sergio", "nerea", "ola", "kuba")
    }
    await a_history(session_factory, people["sergio"]["id"], SERGIO_AT_65)
    await a_history(session_factory, people["nerea"]["id"], NEW_AT_50)
    return people


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    marta, *others = crowd.values()
    return await a_group(client, marta, club, *others)


# --------------------------------------------------------------------------- #
# The deal — Picked for you
# --------------------------------------------------------------------------- #


async def test_the_deal_never_puts_sergio_on_her_court_and_new_nerea_passes(
    client, session_factory, payments, clock
):
    """Saturday evenings at 17:00: of the five, the four the proposer may deal
    with Marta never hold Sergio, and Nerea — New — is on her card."""

    club = await a_club_selling(client, hours=[(6, 17)])
    crowd = {
        name: await a_member(client, session_factory, payments, name)
        for name in ("marta", "sergio", "nerea", "ola", "kuba")
    }
    await a_history(session_factory, crowd["sergio"]["id"], SERGIO_AT_65)
    await a_history(session_factory, crowd["nerea"]["id"], NEW_AT_50)
    marta, *others = crowd.values()
    group = await a_group(client, marta, club, *others)
    await switches_on(client, marta)

    await proposes(session_factory, clock, group)

    cards = {
        card["proposal_id"]: names_on(card)
        for player in crowd.values()
        for card in await deck_of(client, player, group)
    }
    assert cards, "the proposer dealt nothing"
    assert not [names for names in cards.values() if {"marta", "sergio"} <= names]
    assert [names for names in cards.values() if {"marta", "nerea"} <= names]
    assert [names for names in cards.values() if "sergio" in names]


# --------------------------------------------------------------------------- #
# The deck and the details
# --------------------------------------------------------------------------- #


async def test_a_card_with_sergio_in_is_withheld_from_her_and_hers_from_him(
    client, session_factory, clock, club, crowd, group
):
    """Both dealt both cards before she switched it on: his yes on one keeps it
    out of her deck, hers on the other keeps it out of his — and on a card
    with only Ola In, each of them is left off the other's version."""

    marta, sergio, ola, kuba = (
        crowd[name] for name in ("marta", "sergio", "ola", "kuba")
    )
    four = (marta, sergio, ola, kuba)
    his = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    hers = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_18,
        versions=(four,),
    )
    olas = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_19,
        versions=(four,),
    )
    assert (await says_yes(client, sergio, his)).status_code == 200
    assert (await says_yes(client, marta, hers)).status_code == 200
    assert (await says_yes(client, ola, olas)).status_code == 200

    await switches_on(client, marta)

    martas = await deck_of(client, marta, group)
    sergios = await deck_of(client, sergio, group)
    assert ids_of(martas) == [str(olas)]
    assert ids_of(sergios) == [str(olas)]
    assert names_on(martas[0]) == {"marta", "ola", "kuba"}
    assert names_on(sergios[0]) == {"sergio", "ola", "kuba"}


async def test_the_details_of_a_card_with_the_other_in_are_not_theirs_to_read(
    client, session_factory, clock, club, crowd, group
):
    """His card with him In is not hers to open once her filter is on, and
    hers with her In is not his — the deck's withholding, as a screen."""

    marta, sergio = crowd["marta"], crowd["sergio"]
    four = (marta, sergio, crowd["ola"], crowd["kuba"])
    his = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    hers = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_18,
        versions=(four,),
    )
    assert (await says_yes(client, sergio, his)).status_code == 200
    assert (await says_yes(client, marta, hers)).status_code == 200
    before = await client.get(f"/api/v1/proposals/{his}", headers=marta["headers"])

    await switches_on(client, marta)
    hers_of_his = await client.get(f"/api/v1/proposals/{his}", headers=marta["headers"])
    his_of_hers = await client.get(
        f"/api/v1/proposals/{hers}", headers=sergio["headers"]
    )

    assert before.status_code == 200, before.text
    for read in (hers_of_his, his_of_hers):
        assert (read.status_code, code_of(read)) == (404, "proposal_not_found")


# --------------------------------------------------------------------------- #
# No later yes puts them together
# --------------------------------------------------------------------------- #


async def test_a_yes_that_would_put_them_together_is_refused_whoever_says_it(
    client, session_factory, clock, club, crowd, group
):
    marta, sergio = crowd["marta"], crowd["sergio"]
    four = (marta, sergio, crowd["ola"], crowd["kuba"])
    his = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    hers = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_18,
        versions=(four,),
    )
    assert (await says_yes(client, sergio, his)).status_code == 200
    assert (await says_yes(client, marta, hers)).status_code == 200
    await switches_on(client, marta)

    hers_on_his = await says_yes(client, marta, his)
    his_on_hers = await says_yes(client, sergio, hers)

    assert (hers_on_his.status_code, code_of(hers_on_his)) == (409, "no_longer_fits")
    assert (his_on_hers.status_code, code_of(his_on_hers)) == (409, "no_longer_fits")
    assert await live_ids(client, marta) == [str(hers)]
    assert await live_ids(client, sergio) == [str(his)]


async def test_new_nerea_passes_at_least_high(
    client, session_factory, clock, club, crowd, group
):
    """Nerea reads 50 — Medium — and is New: she is dealt Marta's card and her
    yes lands beside Marta's."""

    marta, nerea = crowd["marta"], crowd["nerea"]
    await switches_on(client, marta)
    card = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((marta, nerea, crowd["ola"], crowd["kuba"]),),
    )
    assert (await says_yes(client, marta, card)).status_code == 200

    assert ids_of(await deck_of(client, nerea, group)) == [str(card)]
    said = await says_yes(client, nerea, card)
    assert said.status_code == 200, said.text
    assert said.json()["open_seats"] == 2


# --------------------------------------------------------------------------- #
# Yeses already given stand
# --------------------------------------------------------------------------- #


async def test_her_yes_given_before_she_switched_it_on_stands_and_the_game_books(
    client, session_factory, clock, club, crowd, group
):
    """Her yes on Saturday's card, where Sergio is In, stands: the last yes
    books the four, the two of them included."""

    marta, sergio, ola, kuba = (
        crowd[name] for name in ("marta", "sergio", "ola", "kuba")
    )
    saturday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((marta, sergio, ola, kuba),),
    )
    for player in (marta, sergio, ola):
        assert (await says_yes(client, player, saturday)).status_code == 200

    await switches_on(client, marta)
    assert await live_ids(client, marta) == [str(saturday)]
    last = await says_yes(client, kuba, saturday)

    assert last.status_code == 200, last.text
    booked = last.json()["booked"]
    assert booked is not None
    for player in (marta, sergio):
        [game] = [
            game
            for game in await home_of(client, player)
            if game["booking_id"] == booked["booking_id"]
        ]
        assert game["status"] == "BOOKED"


async def test_a_yes_given_before_sergio_dropped_below_her_filter_stands(
    client, session_factory, payments, clock, club, crowd, group
):
    """Sergiusz at 75 is High when he says yes beside her; an evening he never
    came to drops him to 50. His yes stands and the game books — and from then
    on a new yes of his beside hers is refused."""

    marta, ola, kuba = crowd["marta"], crowd["ola"], crowd["kuba"]
    sergiusz = await a_member(client, session_factory, payments, "sergiusz")
    await a_history(session_factory, sergiusz["id"], AT_75)
    joined = await client.post(
        f"/api/v1/groups/{group}/membership", headers=sergiusz["headers"]
    )
    assert joined.status_code in (200, 201), joined.text
    await switches_on(client, marta)
    four = (marta, sergiusz, ola, kuba)
    saturday = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )
    later = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SAT_19,
        versions=(four,),
    )
    for player in (marta, sergiusz, ola):
        said = await says_yes(client, player, saturday)
        assert said.status_code == 200, said.text
    assert (await says_yes(client, marta, later)).status_code == 200

    await a_history(session_factory, sergiusz["id"], ((MISSED, 2),))
    last = await says_yes(client, kuba, saturday)
    refused = await says_yes(client, sergiusz, later)

    assert last.status_code == 200, last.text
    assert last.json()["booked"] is not None
    assert (refused.status_code, code_of(refused)) == (409, "no_longer_fits")


async def test_a_paused_yes_beside_sergio_comes_back_when_her_week_frees(
    client, session_factory, clock, mailbox, club, crowd, group
):
    """Marta plays one game a week: Saturday's booking paused her Sunday yes,
    where Sergio is In. She switches the filter on, then leaves Saturday's
    game — her Sunday yes comes back, a yes given before."""

    marta, sergio, ola, kuba = (
        crowd[name] for name in ("marta", "sergio", "ola", "kuba")
    )
    capped = await client.put(
        "/api/v1/players/me/games-and-money",
        json={"games_per_week": 1, "most_ill_pay_grosze": None},
        headers=marta["headers"],
    )
    assert capped.status_code == 200, capped.text
    sunday = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 10),
        versions=((marta, sergio, ola, kuba),),
    )
    for player in (marta, sergio):
        assert (await says_yes(client, player, sunday)).status_code == 200
    booking = await books(
        client,
        session_factory,
        clock,
        group=group,
        club=club,
        four=(marta, crowd["nerea"], ola, kuba),
        start=SATURDAY_FIVE,
    )
    await mailbox.drain()
    assert str(sunday) not in await live_ids(client, marta), "paused by the booking"

    await switches_on(client, marta)
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=marta["headers"]
    )
    assert left.status_code == 200, left.text
    await mailbox.drain()

    assert await live_ids(client, marta) == [str(sunday)]


async def test_a_booked_game_with_sergio_on_it_never_changes(
    client, session_factory, clock, club, crowd, group
):
    marta, sergio = crowd["marta"], crowd["sergio"]
    booking = await books(
        client,
        session_factory,
        clock,
        group=group,
        club=club,
        four=(marta, sergio, crowd["ola"], crowd["kuba"]),
        start=SATURDAY_FIVE,
    )

    await switches_on(client, marta)
    await proposes(session_factory, clock, group)

    for player in (marta, sergio):
        [game] = [
            g for g in await home_of(client, player) if g["booking_id"] == booking
        ]
        assert game["status"] == "BOOKED"
    details = await client.get(f"/api/v1/bookings/{booking}", headers=marta["headers"])
    assert details.status_code == 200, details.text


# --------------------------------------------------------------------------- #
# Posts — the posting fits, dealing a post, joining from the sheet
# --------------------------------------------------------------------------- #


async def test_her_post_never_reaches_sergio_and_his_never_reaches_her(
    client, session_factory, payments, clock
):
    """Saturday evening. Marta's grid counts the three who fit her, her post at
    18:00 is dealt to them and never to Sergio, he finds it on no sheet and
    cannot join it; his post at 17:00 is neither dealt to her nor on her
    sheet, though she is free for it."""

    club = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    evening = [{"day": 6, "hour": 17}, {"day": 6, "hour": 18}]
    crowd = {
        name: await a_member(client, session_factory, payments, name, week=evening)
        for name in ("marta", "sergio", "ola", "kuba", "ewa")
    }
    await a_history(session_factory, crowd["sergio"]["id"], SERGIO_AT_65)
    marta, sergio, ola = crowd["marta"], crowd["sergio"], crowd["ola"]
    group = await a_group(client, marta, club, *list(crowd.values())[1:])
    await switches_on(client, marta)
    posting = {"sport": "PADEL", "kind": "COMPETITIVE", "who": "ANYONE"}

    async def sheet_of(player: dict) -> list[str]:
        read = await client.get(
            f"/api/v1/pools/{group}/posting-grid/slot",
            params={**posting, "day": SATURDAY.isoformat(), "range": "EVENING"},
            headers=player["headers"],
        )
        assert read.status_code == 200, read.text
        return [post["proposal_id"] for post in read.json()["posts"]]

    async def posts(player: dict, start) -> dict:
        answer = await client.post(
            f"/api/v1/pools/{group}/posts",
            json={**posting, "club_id": club, "starts_at": start.isoformat()},
            headers=player["headers"],
        )
        assert answer.status_code == 201, answer.text
        return answer.json()

    async def fits_free_for(player: dict) -> int:
        grid = await client.get(
            f"/api/v1/pools/{group}/posting-grid",
            params=posting,
            headers=player["headers"],
        )
        assert grid.status_code == 200, grid.text
        [cell] = [
            cell
            for row in grid.json()["days"]
            if row["day"] == SATURDAY.isoformat()
            for cell in row["cells"]
            if cell["range"] == "EVENING"
        ]
        return cell["fits_free"]

    # Ola, Kuba and Ewa for each of them — never the other.
    assert await fits_free_for(marta) == 3
    assert await fits_free_for(sergio) == 3

    hers = await posts(marta, SAT_18)
    assert hers["dealt_to"] == 3
    assert await deck_of(client, sergio, group) == []
    assert hers["proposal_id"] not in await sheet_of(sergio)
    joined = await says_yes(client, sergio, UUID(hers["proposal_id"]))
    assert (joined.status_code, code_of(joined)) == (409, "no_longer_fits")

    his = await posts(sergio, SATURDAY_FIVE)
    assert his["proposal_id"] in ids_of(await deck_of(client, ola, group))
    assert his["proposal_id"] not in ids_of(await deck_of(client, marta, group))
    assert his["proposal_id"] not in await sheet_of(marta)


# --------------------------------------------------------------------------- #
# Seat open and Fill in
# --------------------------------------------------------------------------- #


async def test_a_seat_on_his_game_is_never_offered_to_her_and_on_hers_never_to_him(
    client, session_factory, payments, clock, mailbox, club
):
    """Two booked games, each left by one of its four: Sergio's at 17:00 is on
    Zosia's Fill in and not Marta's, and her seat is refused her; Marta's at
    19:00 is on Zosia's and not Sergio's."""

    names = ("marta", "sergio", "ola", "kuba", "ewa", "tomek", "ania", "piotr", "zosia")
    crowd = {
        name: await a_member(client, session_factory, payments, name) for name in names
    }
    await a_history(session_factory, crowd["sergio"]["id"], SERGIO_AT_65)
    marta, sergio, zosia = crowd["marta"], crowd["sergio"], crowd["zosia"]
    group = await a_group(client, marta, club, *list(crowd.values())[1:])
    his = await books(
        client,
        session_factory,
        clock,
        group=group,
        club=club,
        four=(sergio, crowd["ola"], crowd["kuba"], crowd["ewa"]),
        start=SATURDAY_FIVE,
    )
    hers = await books(
        client,
        session_factory,
        clock,
        group=group,
        club=club,
        four=(marta, crowd["tomek"], crowd["ania"], crowd["piotr"]),
        start=SAT_19,
    )
    await switches_on(client, marta)
    for leaver, booking in ((crowd["ola"], his), (crowd["tomek"], hers)):
        left = await client.post(
            f"/api/v1/bookings/{booking}/departure", headers=leaver["headers"]
        )
        assert left.status_code == 200, left.text
    await mailbox.drain()

    assert await fill_in(client, marta, group) == []
    assert await fill_in(client, sergio, group) == []
    assert set(await fill_in(client, zosia, group)) == {his, hers}
    # No Seat open card either — she would be one of his seat's best fits.
    assert his not in ids_of(await deck_of(client, marta, group))
    assert hers not in ids_of(await deck_of(client, sergio, group))
    for player, booking in ((marta, his), (sergio, hers)):
        joined = await client.post(
            f"/api/v1/bookings/{booking}/seats", headers=player["headers"]
        )
        assert (joined.status_code, code_of(joined)) == (409, "rescue_not_offered")


async def test_a_seat_kept_for_sergio_before_she_switched_it_on_is_still_his(
    client, session_factory, payments, clock, mailbox, club, crowd, group
):
    """Nerea leaves Marta's Saturday game; Sergio's bank checks his *I'm in*,
    so the seat is kept for him for thirty minutes (#640). Marta switches her
    filter on meanwhile — a claim made before stands: he confirms in time and
    takes the seat."""

    marta, sergio, nerea = crowd["marta"], crowd["sergio"], crowd["nerea"]
    booking = await books(
        client,
        session_factory,
        clock,
        group=group,
        club=club,
        four=(marta, nerea, crowd["ola"], crowd["kuba"]),
        start=SATURDAY_FIVE,
    )
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=nerea["headers"]
    )
    assert left.status_code == 200, left.text
    answer = await refused_rescuer(client, payments, booking, sergio)

    await switches_on(client, marta)
    clock.move(timedelta(minutes=20))
    confirmed = await confirms(client, payments, sergio, answer["your_payment"])

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["booked"]["booking_id"] == booking


# --------------------------------------------------------------------------- #
# The record — the two lines, naming nobody
# --------------------------------------------------------------------------- #


async def a_mate(client, group: UUID, name: str) -> dict:
    """Somebody in the group: signed up, a profile, joined — nothing more."""

    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token)
    headers = players.auth(token)
    joined = await client.post(f"/api/v1/groups/{group}/membership", headers=headers)
    assert joined.status_code in (200, 201), joined.text
    return {"id": player_id, "token": token, "headers": headers}


async def test_her_record_reads_that_her_filter_hides_2_of_the_11_players_in_her_groups(
    client, session_factory, payments, clock, club
):
    """Eleven others in her group: Sergio at 65 and Kasia at 15 are below *at
    least High*; Nerea, at 50, is New; eight have nothing behind them. Sergio
    reads that at 75 he's dealt with everyone again — and nothing on his record
    names her."""

    marta = await a_member(client, session_factory, payments, "marta")
    group = await a_group(client, marta, club)
    mates = {
        name: await a_mate(client, group, name)
        for name in (
            "sergio",
            "kasia",
            "nerea",
            "ola",
            "kuba",
            "ewa",
            "tomek",
            "ania",
            "piotr",
            "zosia",
            "marek",
        )
    }
    await a_history(session_factory, mates["sergio"]["id"], SERGIO_AT_65)
    await a_history(session_factory, mates["kasia"]["id"], LOW_AT_15)
    await a_history(session_factory, mates["nerea"]["id"], NEW_AT_50)

    before = (await own_record(client, marta))["reliability"]["filter"]
    await switches_on(client, marta)
    hers = (await own_record(client, marta))["reliability"]
    sergio = await client.get(
        "/api/v1/players/me/record", headers=mates["sergio"]["headers"]
    )
    nerea = (await own_record(client, mates["nerea"]))["reliability"]

    assert before == {"hides": 0, "of": 11}
    assert hers["filter"] == {"minimum": "HIGH", "hides": 2, "of": 11}
    assert sergio.json()["reliability"]["player_score"] == 65
    assert sergio.json()["reliability"]["filter"] == {
        "hides": 0,
        "of": 11,
        "back_with_everyone": {"band": "HIGH", "points": 75},
    }
    assert str(marta["id"]) not in sergio.text and "marta" not in sergio.text
    assert "back_with_everyone" not in nerea["filter"]


async def test_nobody_else_s_record_carries_a_filter(
    client, session_factory, clock, crowd, group
):
    """Her filter is about other people: on her record as Ola reads it, and on
    Sergio's as she reads it, there is no filter at all."""

    marta, sergio, ola = crowd["marta"], crowd["sergio"], crowd["ola"]
    await switches_on(client, marta)

    hers_to_ola = await client.get(
        f"/api/v1/players/{marta['id']}/record", headers=ola["headers"]
    )
    his_to_her = await client.get(
        f"/api/v1/players/{sergio['id']}/record", headers=marta["headers"]
    )

    assert hers_to_ola.status_code == 200, hers_to_ola.text
    assert "filter" not in hers_to_ola.json()["reliability"]
    assert "filter" not in his_to_her.json()["reliability"]


async def test_switching_it_off_deals_them_together_again(
    client, session_factory, clock, club, crowd, group
):
    marta, sergio = crowd["marta"], crowd["sergio"]
    his = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((marta, sergio, crowd["ola"], crowd["kuba"]),),
    )
    assert (await says_yes(client, sergio, his)).status_code == 200
    await switches_on(client, marta)
    assert await deck_of(client, marta, group) == []

    await switches_on(client, marta, None)

    assert ids_of(await deck_of(client, marta, group)) == [str(his)]
    assert (await says_yes(client, marta, his)).status_code == 200
    assert (await own_record(client, marta))["reliability"]["filter"] == {
        "hides": 0,
        "of": 4,
    }


async def test_switching_it_makes_her_pools_due_for_the_proposer(
    client, session_factory, clock, crowd, group
):
    """Who she may be dealt changed in every pool she is in, so the short tick
    deals from them without waiting for the sweep — as a changed week does."""

    marta = crowd["marta"]
    due = DueForProposing()
    await players.deliver_the_outbox(session_factory, proposer_due=due)
    due.take()

    await switches_on(client, marta)
    await players.deliver_the_outbox(session_factory, proposer_due=due)

    async with session_factory() as session:
        pools = await build_propose_games(session, clock=clock).pools_due(due.take())
    assert pools == [group]
