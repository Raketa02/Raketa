"""**The friend link** — every player has one, and opening it puts its owner's
request on the opener's Home, over HTTP as the player app and the public site
call it (``docs/adr/0202`` §1–§2; the mechanics §4; #748).

The cast:

- **Tomek** shares ``rakieta.app/f/<code>``. **Zofia** signs up through it and
  shares no group with him; **Ania**, in his group already, opens it too. Each
  finds *Tomek wants to be your friend · Invited you to Rakieta* on Home.
- Tomek's link leaks into a big chat, so he takes a **New link**: the old code
  reads as not found, in the app and on the public site.
- **Michał**, whom Tomek blocked, opens it and finds nothing on Home — the one
  place a block could be guessed, and a cost ADR-0202 names.
"""

from __future__ import annotations

import re

import pytest

from app.core.config import get_settings
from app.modules.groups.domain.value_objects import (
    GROUP_CODE_ALPHABET,
    GROUP_CODE_LENGTH,
)
from tests.api import players_world as players
from tests.api.test_friends import bell_of, blocks, requests_of
from tests.api.test_friends_on_every_face import home_requests
from tests.api.test_group_members import a_padel_player
from tests.api.test_groups import a_club, a_group, a_player, join

LINK = "/api/v1/friends/link"


@pytest.fixture
async def tomek(client) -> dict:
    return await a_player(client, "tomek")


async def link_of(client, player: dict) -> dict:
    read = await client.get(LINK, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


# --------------------------------------------------------------------------- #
# The code
# --------------------------------------------------------------------------- #


async def test_a_players_link_is_made_on_first_read_and_read_the_same_after(
    client, tomek
):
    first = await link_of(client, tomek)
    again = await link_of(client, tomek)

    assert first == again
    code = first["code"]
    # Shaped like a group's code: letters and digits with no look-alikes.
    assert len(code) == GROUP_CODE_LENGTH
    assert set(code) <= set(GROUP_CODE_ALPHABET)
    site = re.escape(get_settings().PUBLIC_SITE_URL.rstrip("/"))
    assert re.fullmatch(rf"{site}/f/{code}", first["link"])


async def test_every_player_has_a_link_of_their_own(client, tomek):
    ania = await a_player(client, "ania")

    assert (await link_of(client, tomek))["code"] != (await link_of(client, ania))[
        "code"
    ]


async def test_a_link_nobody_can_guess_from_the_nickname(client, tomek):
    assert "tomek" not in (await link_of(client, tomek))["link"]


async def test_a_new_link_kills_the_old_code_in_the_app_and_on_the_public_site(
    client, tomek
):
    zofia = await a_player(client, "zofia")
    old = await link_of(client, tomek)

    taken = await client.post(f"{LINK}/replacement", headers=tomek["headers"])

    assert taken.status_code == 200, taken.text
    new = taken.json()
    assert new["code"] != old["code"]
    assert await link_of(client, tomek) == new
    dead = await opens(client, zofia, old["code"])
    assert dead.status_code == 404
    assert dead.json()["code"] == "friend_link_not_found"
    assert (await the_page(client, old["code"])).json()["code"] == (
        "friend_link_not_found"
    )
    assert (await opens(client, zofia, new["code"])).status_code == 200


async def test_a_new_link_before_any_read_is_simply_made(client, tomek):
    taken = await client.post(f"{LINK}/replacement", headers=tomek["headers"])

    assert taken.status_code == 200, taken.text
    assert await link_of(client, tomek) == taken.json()


async def test_requests_made_through_the_old_link_stay(client, tomek):
    zofia = await a_player(client, "zofia")
    await opens(client, zofia, (await link_of(client, tomek))["code"])

    await client.post(f"{LINK}/replacement", headers=tomek["headers"])

    [card] = await home_requests(client, zofia)
    assert card["player_id"] == str(tomek["id"])


async def test_a_replaced_code_is_never_handed_out_again(
    client, session_factory, monkeypatch, tomek
):
    """The minter draws the replaced code first, and draws again."""

    from app.bootstrap.composition import build_friend_link_codes
    from app.modules.friends.infrastructure import random_friend_link_codes

    old = (await link_of(client, tomek))["code"]
    await client.post(f"{LINK}/replacement", headers=tomek["headers"])
    draws = iter(old + "k7pm2qxa")
    monkeypatch.setattr(
        random_friend_link_codes.secrets, "choice", lambda alphabet: next(draws)
    )

    async with session_factory() as session:
        minted = await build_friend_link_codes(session).mint()

    assert minted.value == "k7pm2qxa"


# --------------------------------------------------------------------------- #
# Opening it
# --------------------------------------------------------------------------- #

REQUESTS = "/api/v1/friends/requests"


async def opens(client, opener: dict, code: str):
    return await client.post(
        f"/api/v1/friends/links/{code}/opening", headers=opener["headers"]
    )


async def opened(client, opener: dict, owner: dict) -> str:
    answer = await opens(client, opener, (await link_of(client, owner))["code"])
    assert answer.status_code == 200, answer.text
    return answer.json()["relation"]


async def friends_of(client, reader: dict) -> list[str]:
    read = await client.get("/api/v1/friends", headers=reader["headers"])
    assert read.status_code == 200, read.text
    return [friend["player_id"] for friend in read.json()["friends"]]


@pytest.fixture
async def his_group(client) -> dict:
    """Tomek's padel group, with Ania in it."""

    tomek = await a_padel_player(client, "tomek")
    ania = await a_padel_player(client, "ania")
    group = await a_group(client, tomek, await a_club(client), name="Kazimierz crew")
    joined = await join(client, ania, group)
    assert joined.status_code in (200, 201), joined.text
    return {"tomek": tomek, "ania": ania, "group": group}


async def test_a_new_player_who_opens_it_finds_his_request_on_home(
    client, mailbox, tomek
):
    """Zofia signed up through it, and shares no group with Tomek."""

    zofia = await a_player(client, "zofia")

    assert await opened(client, zofia, tomek) == "ASKED_YOU"

    [card] = await home_requests(client, zofia)
    assert card["player_id"] == str(tomek["id"])
    assert card["nickname"] == "tomek"
    assert card["by_link"] is True
    assert card["group"] is None
    assert card["sport"] is None
    [notice] = (await bell_of(client, mailbox, zofia))["notices"]
    assert notice["kind"] == "FRIEND_REQUEST"
    assert notice["title"] == "tomek wants to be your friend"
    assert notice["body"] == "Invited you to Rakieta"
    assert notice["player_id"] == str(tomek["id"])
    # His side: the request is his, as if he had pressed + Add.
    [sent] = await requests_of(client, tomek, "YOU_ASKED")
    assert sent["player_id"] == str(zofia["id"])
    assert (await bell_of(client, mailbox, tomek))["notices"] == []


async def test_a_player_who_already_has_the_app_finds_it_on_home_too(client, his_group):
    tomek, ania = his_group["tomek"], his_group["ania"]

    assert await opened(client, ania, tomek) == "ASKED_YOU"

    [card] = await home_requests(client, ania)
    assert card["by_link"] is True
    # Made by link, so it names no group though they share one.
    assert card["group"] is None


async def test_accepting_a_request_by_link_makes_them_friends(client, tomek):
    zofia = await a_player(client, "zofia")
    await opened(client, zofia, tomek)

    accepted = await client.post(
        f"{REQUESTS}/{tomek['id']}/acceptance", headers=zofia["headers"]
    )

    assert accepted.status_code == 200, accepted.text
    assert await friends_of(client, zofia) == [str(tomek["id"])]
    assert await friends_of(client, tomek) == [str(zofia["id"])]


async def test_the_code_is_read_in_any_case(client, tomek):
    zofia = await a_player(client, "zofia")
    code = (await link_of(client, tomek))["code"]

    answer = await opens(client, zofia, code.upper())

    assert answer.status_code == 200, answer.text
    assert answer.json()["relation"] == "ASKED_YOU"


async def test_your_own_link_does_nothing(client, mailbox, tomek):
    assert await opened(client, tomek, tomek) == "NONE"

    assert await home_requests(client, tomek) == []
    assert await requests_of(client, tomek, "YOU_ASKED") == []


async def test_a_friends_link_does_nothing(client, mailbox, his_group):
    tomek, ania = his_group["tomek"], his_group["ania"]
    await opened(client, ania, tomek)
    await client.post(f"{REQUESTS}/{tomek['id']}/acceptance", headers=ania["headers"])
    told = len((await bell_of(client, mailbox, tomek))["notices"])

    assert await opened(client, ania, tomek) == "FRIEND"
    assert await opened(client, tomek, ania) == "FRIEND"

    assert await home_requests(client, ania) == []
    assert await home_requests(client, tomek) == []
    assert len((await bell_of(client, mailbox, tomek))["notices"]) == told


async def test_opening_it_after_asking_its_owner_makes_friends_at_once(
    client, mailbox, his_group
):
    tomek, ania, group = his_group["tomek"], his_group["ania"], his_group["group"]
    asked = await client.post(
        REQUESTS,
        json={
            "player_id": str(tomek["id"]),
            "made_from": "MEMBERS",
            "group_id": group["id"],
            "sport": "PADEL",
        },
        headers=ania["headers"],
    )
    assert asked.status_code == 200, asked.text

    assert await opened(client, ania, tomek) == "FRIEND"

    assert await friends_of(client, tomek) == [str(ania["id"])]
    assert await home_requests(client, tomek) == []
    [made] = [
        notice
        for notice in (await bell_of(client, mailbox, ania))["notices"]
        if notice["kind"] == "FRIENDS_MADE"
    ]
    assert made["title"] == "You and tomek are friends now"


async def test_opening_it_twice_makes_no_second_request(client, mailbox, tomek):
    zofia = await a_player(client, "zofia")
    await opened(client, zofia, tomek)
    await bell_of(client, mailbox, zofia)

    assert await opened(client, zofia, tomek) == "ASKED_YOU"

    assert len(await home_requests(client, zofia)) == 1
    assert len((await bell_of(client, mailbox, zofia))["notices"]) == 1


async def test_a_request_he_made_from_a_group_is_left_as_it_was(client, his_group):
    tomek, ania, group = his_group["tomek"], his_group["ania"], his_group["group"]
    await client.post(
        REQUESTS,
        json={
            "player_id": str(ania["id"]),
            "made_from": "MEMBERS",
            "group_id": group["id"],
            "sport": "PADEL",
        },
        headers=tomek["headers"],
    )

    assert await opened(client, ania, tomek) == "ASKED_YOU"

    [card] = await home_requests(client, ania)
    assert card["by_link"] is False
    assert card["group"]["name"] == "Kazimierz crew"


async def test_a_request_set_aside_comes_back_to_home_when_his_link_is_opened(
    client, mailbox, tomek
):
    """The call the mechanics §12 left to this ticket: *Not now* was hers, and
    opening his link is asking to see his request."""

    zofia = await a_player(client, "zofia")
    await opened(client, zofia, tomek)
    set_aside = await client.post(
        f"{REQUESTS}/{tomek['id']}/set-aside", headers=zofia["headers"]
    )
    assert set_aside.status_code == 204
    assert await home_requests(client, zofia) == []

    assert await opened(client, zofia, tomek) == "ASKED_YOU"

    [card] = await home_requests(client, zofia)
    assert card["player_id"] == str(tomek["id"])
    [waiting] = await requests_of(client, zofia, "ASKED_YOU")
    assert waiting["set_aside"] is False
    # Back in the bell as it was, and told nobody a second time.
    assert len((await bell_of(client, mailbox, zofia))["notices"]) == 1


async def test_a_link_its_owner_blocked_the_opener_from_is_swallowed(
    client, session_factory, mailbox, his_group
):
    """Michał opens the link of Tomek, who blocked him: he reads what anybody
    reads, and finds nothing on Home — the cost ADR-0202 names."""

    tomek = his_group["tomek"]
    michal = await a_padel_player(client, "michal")
    await join(client, michal, his_group["group"])
    await blocks(client, session_factory, tomek, michal)

    assert await opened(client, michal, tomek) == "ASKED_YOU"

    assert await home_requests(client, michal) == []
    assert await requests_of(client, michal, "ASKED_YOU") == []
    assert await requests_of(client, tomek, "YOU_ASKED") == []
    assert (await bell_of(client, mailbox, michal))["notices"] == []
    # Nothing comes back when Tomek unblocks him: nothing was recorded.
    await client.delete(f"/api/v1/blocks/{michal['id']}", headers=tomek["headers"])
    await players.deliver_the_outbox(session_factory)
    assert await home_requests(client, michal) == []


async def test_opening_the_link_of_somebody_you_blocked_is_refused(
    client, session_factory, his_group
):
    tomek, ania = his_group["tomek"], his_group["ania"]
    await blocks(client, session_factory, ania, tomek)

    answer = await opens(client, ania, (await link_of(client, tomek))["code"])

    assert answer.status_code == 409
    assert answer.json()["code"] == "unblock_them_first"
    assert await requests_of(client, tomek, "YOU_ASKED") == []


@pytest.mark.parametrize("code", ["abcdefgh", "abc", "0o0o0o0o", "abcdefghj"])
async def test_a_code_no_link_carries_is_not_found(client, tomek, code):
    answer = await opens(client, tomek, code)

    assert answer.status_code == 404
    assert answer.json()["code"] == "friend_link_not_found"


async def test_opening_a_link_needs_a_session(client, tomek):
    code = (await link_of(client, tomek))["code"]

    assert (
        await client.post(f"/api/v1/friends/links/{code}/opening")
    ).status_code == 401


async def test_a_request_hidden_from_her_stays_hidden_when_she_opens_his_link(
    client, session_factory, mailbox, his_group
):
    """Tomek asked Ania while she had blocked him: *unseen* — she never sees it,
    and unblocking brings nothing back (the mechanics §3.5). Opening his link
    does not either: its card would name the group he asked from, and tell her
    he asked across her block."""

    tomek, ania, group = his_group["tomek"], his_group["ania"], his_group["group"]
    await blocks(client, session_factory, ania, tomek)
    asked = await client.post(
        REQUESTS,
        json={
            "player_id": str(ania["id"]),
            "made_from": "MEMBERS",
            "group_id": group["id"],
            "sport": "PADEL",
        },
        headers=tomek["headers"],
    )
    assert asked.status_code == 200, asked.text
    await client.delete(f"/api/v1/blocks/{tomek['id']}", headers=ania["headers"])
    await players.deliver_the_outbox(session_factory)

    assert await opened(client, ania, tomek) == "ASKED_YOU"

    assert await home_requests(client, ania) == []
    assert await requests_of(client, ania, "ASKED_YOU") == []
    assert (await bell_of(client, mailbox, ania))["notices"] == []


async def test_a_block_not_yet_delivered_still_swallows_the_request(
    client, session_factory, his_group
):
    """The owner's blocks are read live, not from anything the block's delivery
    writes."""

    tomek, ania = his_group["tomek"], his_group["ania"]
    made = await players.block_between(
        client, tomek["headers"]["Authorization"].split()[1], ania["id"]
    )
    assert made.status_code == 204, made.text

    assert await opened(client, ania, tomek) == "ASKED_YOU"

    assert await home_requests(client, ania) == []
    assert await requests_of(client, tomek, "YOU_ASKED") == []


# --------------------------------------------------------------------------- #
# The public site's read
# --------------------------------------------------------------------------- #

PAGE = "/api/v1/public/friend-links"


async def the_page(client, code: str):
    return await client.get(f"{PAGE}/{code}")


async def test_the_public_site_reads_the_owners_nickname_and_face_and_nothing_else(
    client, tomek
):
    page = await the_page(client, (await link_of(client, tomek))["code"])

    assert page.status_code == 200, page.text
    assert page.json() == {"nickname": "tomek", "photo_url": None}


@pytest.mark.parametrize("code", ["abcdefgh", "abc", "0o0o0o0o"])
async def test_a_code_no_link_carries_reads_as_nothing_at_that_link(client, code):
    page = await the_page(client, code)

    assert page.status_code == 404
    assert page.json()["code"] == "friend_link_not_found"
