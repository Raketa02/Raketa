"""**The *friend* tag on every face, and only the reader's** (``docs/adr/0202``
§2; the mechanics §3.6; #745) — the deck's tiles, a game's details, Home's
booked games, Fill in, the result's *PLAYED WITH* card and the record — and
**Home's friend requests** (§3.7).

Ola, Kuba, Ewa, Tomek, Zosia and Marek play padel in one group. **Ola and Kuba
are friends; so are Ewa and Tomek.** Ola reads *friend* on Kuba and on nobody
else; Zosia, who is friends with nobody, reads it on nobody — and never learns
who the others are friends with.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the game is
**Saturday 10 October, 17:00** at Bonarka Arena.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_ask_to_be_friends
from app.kernel import Sport
from app.modules.friends.application.commands import AskCommand
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import RequestOrigin
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
)
from tests.unit.fake_clock import MovableClock

FRIENDS = "/api/v1/friends"
HOME = "/api/v1/home"


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


@pytest.fixture
async def crowd(client, session_factory, payments) -> dict[str, dict]:
    return {
        name: await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek", "zosia", "marek")
    }


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    ola, *rest = crowd.values()
    return await a_group(client, ola, club, *rest)


async def befriend(client, group: UUID, asker: dict, answerer: dict) -> None:
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={
            "player_id": str(answerer["id"]),
            "made_from": "MEMBERS",
            "group_id": str(group),
            "sport": "PADEL",
        },
        headers=asker["headers"],
    )
    assert asked.status_code == 200, asked.text
    accepted = await client.post(
        f"{FRIENDS}/requests/{asker['id']}/acceptance", headers=answerer["headers"]
    )
    assert accepted.status_code == 200, accepted.text


@pytest.fixture
async def friends(client, group, crowd) -> None:
    """Ola and Kuba; Ewa and Tomek."""

    await befriend(client, group, crowd["kuba"], crowd["ola"])
    await befriend(client, group, crowd["ewa"], crowd["tomek"])


def tags(tiles: list[dict]) -> dict[str, bool]:
    return {tile["nickname"]: tile["friend"] for tile in tiles}


def every_tile(sides: dict) -> list[dict]:
    return [*sides["yours"], *sides["theirs"]]


async def a_card_for_the_four(session_factory, clock, club, group, crowd) -> UUID:
    four = tuple(crowd[name] for name in ("ola", "kuba", "ewa", "tomek"))
    return await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(four,)
    )


async def booked(client, session_factory, clock, club, group, crowd) -> str:
    proposal = await a_card_for_the_four(session_factory, clock, club, group, crowd)
    for name in ("ola", "kuba", "ewa"):
        assert (await says_yes(client, crowd[name], proposal)).status_code == 200
    last = await says_yes(client, crowd["tomek"], proposal)
    assert last.status_code == 200, last.text
    return last.json()["booked"]["booking_id"]


# --------------------------------------------------------------------------- #
# A game still filling: the deck and the details
# --------------------------------------------------------------------------- #


async def test_a_deck_tile_is_tagged_only_with_the_readers_own_friends(
    client, session_factory, clock, club, group, crowd, friends
):
    proposal = await a_card_for_the_four(session_factory, clock, club, group, crowd)

    seen: dict[str, dict[str, bool]] = {}
    for name in ("ola", "ewa"):
        read = await client.get(
            f"/api/v1/pools/{group}/deck",
            params={"sport": "PADEL", "kind": "COMPETITIVE"},
            headers=crowd[name]["headers"],
        )
        assert read.status_code == 200, read.text
        [card] = [c for c in read.json()["cards"] if c["proposal_id"] == str(proposal)]
        seen[name] = tags(every_tile(card["sides"]))

    assert seen["ola"] == {"ola": False, "kuba": True, "ewa": False, "tomek": False}
    assert seen["ewa"] == {"ola": False, "kuba": False, "ewa": False, "tomek": True}


async def test_a_games_details_tag_the_readers_friends(
    client, session_factory, clock, club, group, crowd, friends
):
    proposal = await a_card_for_the_four(session_factory, clock, club, group, crowd)

    read = await client.get(
        f"/api/v1/proposals/{proposal}", headers=crowd["kuba"]["headers"]
    )

    assert read.status_code == 200, read.text
    assert tags(every_tile(read.json()["sides"])) == {
        "ola": True,
        "kuba": False,
        "ewa": False,
        "tomek": False,
    }


# --------------------------------------------------------------------------- #
# A booked game: Home, its details, the result's PLAYED WITH
# --------------------------------------------------------------------------- #


async def test_home_tags_the_readers_friends_on_a_booked_game(
    client, session_factory, clock, club, group, crowd, friends
):
    await booked(client, session_factory, clock, club, group, crowd)

    read = await client.get(HOME, headers=crowd["tomek"]["headers"])

    assert read.status_code == 200, read.text
    [game] = read.json()["games"]
    assert tags(every_tile(game["sides"])) == {
        "ola": False,
        "kuba": False,
        "ewa": True,
        "tomek": False,
    }


async def test_the_result_lists_who_the_reader_played_with_and_where_they_stand(
    client, session_factory, clock, club, group, crowd, friends
):
    booking = await booked(client, session_factory, clock, club, group, crowd)
    # Ola asked Ewa, and Tomek asked Ola.
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={"player_id": str(crowd["ewa"]["id"]), "made_from": "RESULT"},
        headers=crowd["ola"]["headers"],
    )
    assert asked.status_code == 200, asked.text
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={"player_id": str(crowd["ola"]["id"]), "made_from": "RESULT"},
        headers=crowd["tomek"]["headers"],
    )
    assert asked.status_code == 200, asked.text

    read = await client.get(
        f"/api/v1/bookings/{booking}", headers=crowd["ola"]["headers"]
    )

    assert read.status_code == 200, read.text
    details = read.json()
    names = {
        tile["player_id"]: tile["nickname"] for tile in every_tile(details["sides"])
    }
    assert {
        names[row["player_id"]]: row["relation"] for row in details["played_with"]
    } == {
        "kuba": "FRIEND",
        "ewa": "SENT",
        "tomek": "ASKED_YOU",
    }
    assert tags(every_tile(details["sides"]))["kuba"] is True


async def test_nobody_reads_whom_the_others_are_friends_with(
    client, session_factory, clock, club, group, crowd, friends
):
    booking = await booked(client, session_factory, clock, club, group, crowd)

    home = await client.get(HOME, headers=crowd["kuba"]["headers"])
    details = await client.get(
        f"/api/v1/bookings/{booking}", headers=crowd["kuba"]["headers"]
    )

    [game] = home.json()["games"]
    # Kuba is Ola's friend, and reads nothing about Ewa and Tomek.
    assert tags(every_tile(game["sides"])) == {
        "ola": True,
        "kuba": False,
        "ewa": False,
        "tomek": False,
    }
    assert {row["relation"] for row in details.json()["played_with"]} == {
        "FRIEND",
        "NONE",
    }


# --------------------------------------------------------------------------- #
# Fill in
# --------------------------------------------------------------------------- #


async def test_fill_in_tags_the_readers_friends_on_a_seat_to_fill(
    client, session_factory, clock, club, group, crowd, friends
):
    booking = await booked(client, session_factory, clock, club, group, crowd)
    # Zosia and Tomek are friends too; Ewa leaves, and Zosia reads the seat.
    await befriend(client, group, crowd["zosia"], crowd["tomek"])
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=crowd["ewa"]["headers"]
    )
    assert left.status_code == 200, left.text

    read = await client.get(
        f"/api/v1/pools/{group}/fill-in",
        params={"sport": "PADEL"},
        headers=crowd["zosia"]["headers"],
    )

    assert read.status_code == 200, read.text
    [row] = read.json()["seats_to_fill"]
    assert tags(row["players"]) == {"ola": False, "kuba": False, "tomek": True}


# --------------------------------------------------------------------------- #
# The record
# --------------------------------------------------------------------------- #


async def test_the_record_reads_the_readers_relation(client, group, crowd, friends):
    ola, kuba, ewa = crowd["ola"], crowd["kuba"], crowd["ewa"]

    on_kuba = await client.get(
        f"/api/v1/players/{kuba['id']}/record", headers=ola["headers"]
    )
    on_ewa = await client.get(
        f"/api/v1/players/{ewa['id']}/record", headers=ola["headers"]
    )
    own = await client.get("/api/v1/players/me/record", headers=ola["headers"])

    assert on_kuba.status_code == on_ewa.status_code == own.status_code == 200
    assert on_kuba.json()["relation"] == "FRIEND"
    assert on_ewa.json()["relation"] == "NONE"
    assert own.json()["relation"] == "NONE"


async def test_the_record_reads_sent_and_asked_you(client, group, crowd):
    ola, marek = crowd["ola"], crowd["marek"]
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={"player_id": str(marek["id"]), "made_from": "RECORD"},
        headers=ola["headers"],
    )
    assert asked.status_code == 200, asked.text

    by_ola = await client.get(
        f"/api/v1/players/{marek['id']}/record", headers=ola["headers"]
    )
    by_marek = await client.get(
        f"/api/v1/players/{ola['id']}/record", headers=marek["headers"]
    )

    assert by_ola.json()["relation"] == "SENT"
    assert by_marek.json()["relation"] == "ASKED_YOU"


# --------------------------------------------------------------------------- #
# Home's FRIEND REQUESTS
# --------------------------------------------------------------------------- #


async def home_requests(client, player: dict) -> list[dict]:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()["friend_requests"]


async def test_a_request_is_a_card_on_home_naming_the_group_level_and_reliability(
    client, group, crowd
):
    ola, zosia = crowd["ola"], crowd["zosia"]
    asked = await client.post(
        f"{FRIENDS}/requests",
        json={
            "player_id": str(ola["id"]),
            "made_from": "MEMBERS",
            "group_id": str(group),
            "sport": "PADEL",
        },
        headers=zosia["headers"],
    )
    assert asked.status_code == 200, asked.text

    [card] = await home_requests(client, ola)

    assert card["player_id"] == str(zosia["id"])
    assert card["nickname"] == "zosia"
    assert card["by_link"] is False
    assert card["group"] == {"id": str(group), "name": "Sobotni padel"}
    assert card["sport"] == "PADEL"
    assert card["level"] == pytest.approx(2.5, abs=0.01)
    assert card["player_score"] == 100
    assert card["reliability_band"] == "VERY_HIGH"
    assert await home_requests(client, zosia) == []


async def test_not_now_and_accept_take_a_card_off_home(client, group, crowd):
    ola = crowd["ola"]
    for name in ("zosia", "marek"):
        asked = await client.post(
            f"{FRIENDS}/requests",
            json={"player_id": str(ola["id"]), "made_from": "RECORD"},
            headers=crowd[name]["headers"],
        )
        assert asked.status_code == 200, asked.text
    assert [card["nickname"] for card in await home_requests(client, ola)] == [
        "marek",
        "zosia",
    ]

    await client.post(
        f"{FRIENDS}/requests/{crowd['zosia']['id']}/set-aside", headers=ola["headers"]
    )
    assert [card["nickname"] for card in await home_requests(client, ola)] == ["marek"]

    await client.post(
        f"{FRIENDS}/requests/{crowd['marek']['id']}/acceptance", headers=ola["headers"]
    )
    assert await home_requests(client, ola) == []


async def test_a_request_from_a_screen_with_no_group_names_none(client, group, crowd):
    ola = crowd["ola"]
    await client.post(
        f"{FRIENDS}/requests",
        json={"player_id": str(ola["id"]), "made_from": "RECORD"},
        headers=crowd["zosia"]["headers"],
    )

    [card] = await home_requests(client, ola)

    assert card["group"] is None
    assert card["sport"] is None
    assert card["level"] is None


async def test_a_group_either_left_is_no_longer_named(client, group, crowd):
    ola, zosia = crowd["ola"], crowd["zosia"]
    await client.post(
        f"{FRIENDS}/requests",
        json={
            "player_id": str(ola["id"]),
            "made_from": "MEMBERS",
            "group_id": str(group),
            "sport": "PADEL",
        },
        headers=zosia["headers"],
    )
    left = await client.delete(
        f"/api/v1/groups/{group}/membership", headers=zosia["headers"]
    )
    assert left.status_code in (200, 204), left.text

    [card] = await home_requests(client, ola)

    assert card["group"] is None
    assert card["sport"] == "PADEL"


async def test_a_request_made_by_link_reads_as_from_a_link(
    client, session_factory, clock, crowd
):
    """The link is #748's; what Home draws for its request is this ticket's."""

    ola, stranger = crowd["ola"], crowd["marek"]
    async with session_factory() as session:
        await build_ask_to_be_friends(session, clock=clock).execute(
            AskCommand(
                requester_id=stranger["id"],
                addressee_id=ola["id"],
                where=Where(made_from=RequestOrigin.LINK),
            )
        )

    [card] = await home_requests(client, ola)

    assert card["by_link"] is True
    assert card["group"] is None


async def test_a_request_is_not_a_game_that_needs_you(client, group, crowd):
    ola = crowd["ola"]
    await client.post(
        f"{FRIENDS}/requests",
        json={"player_id": str(ola["id"]), "made_from": "RECORD"},
        headers=crowd["zosia"]["headers"],
    )

    read = await client.get(HOME, headers=ola["headers"])

    assert read.json()["needing_you"] == 0
    assert len(read.json()["friend_requests"]) == 1


async def test_relations_survive_leaving_a_group(client, group, crowd, friends):
    """A friendship is per pair, across every group (the mechanics §3.1)."""

    left = await client.delete(
        f"/api/v1/groups/{group}/membership", headers=crowd["kuba"]["headers"]
    )
    assert left.status_code in (200, 204), left.text

    read = await client.get(FRIENDS, headers=crowd["ola"]["headers"])

    assert [friend["nickname"] for friend in read.json()["friends"]] == ["kuba"]
    assert Sport.PADEL.value in {
        sport["sport"] for sport in read.json()["friends"][0]["sports"]
    }


async def test_post_a_games_sheet_tags_the_posters_friends(
    client, session_factory, clock, club, group, crowd, friends
):
    """The slot sheet's best fits are faces too (the mechanics §3.6)."""

    from datetime import date

    read = await client.get(
        f"/api/v1/pools/{group}/posting-grid/slot",
        params={
            "sport": "PADEL",
            "kind": "COMPETITIVE",
            "who": "ANYONE",
            "day": date(2026, 10, 10).isoformat(),
            "range": "EVENING",
        },
        headers=crowd["ola"]["headers"],
    )

    assert read.status_code == 200, read.text
    fits = {fit["nickname"]: fit["friend"] for fit in read.json()["fits"]}
    assert fits["kuba"] is True
    assert {name for name, friend in fits.items() if friend} == {"kuba"}
