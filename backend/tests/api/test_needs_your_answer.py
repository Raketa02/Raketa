"""**What's new in Needs your answer, kept on the server** — over HTTP as the
player app calls it (#815; ``docs/adr/0205`` §3; the decision log §3.2).

``GET /home`` answers ``needs_your_answer``: how many of the items waiting on
the reader arrived since they last closed the sheet, and the watermark of this
read — the newest arrival among them. Closing the sheet sends that watermark
back (``POST /players/me/needs-your-answer/visit``), and only what arrived
after it is new, on every phone.

The cast is **Kazimierz crew** (``test_friends.py``) — Karol's padel group,
with Inés, Tomek, Kuba, Magda and Michał in it — for the friend requests and
the visit's own rules, and **Ogrody open play** (``test_level_asks_on_home.py``)
for the asks for a level: Zofia, rated in tennis alone, a friend of Tomek's,
Kuba's and Ania's. A friends game invitation and a payment to confirm are
driven in their own worlds, ``test_needs_your_answer_invitations.py`` and
``test_needs_your_answer_payments.py``. Every act moves the clock first, so
each arrival has an instant of its own.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from tests.api.test_friends import accepts, asks, crew, sets_aside
from tests.api.test_level_asks_on_home import asks_her, not_now, ogrody

__all__ = ["crew", "ogrody"]

HOME = "/api/v1/home"
VISIT = "/api/v1/players/me/needs-your-answer/visit"
NOTICES = "/api/v1/players/me/notices"


def parsed(served: str) -> datetime:
    return datetime.fromisoformat(served.replace("Z", "+00:00"))


async def home_of(client, player: dict) -> dict:
    read = await client.get(HOME, headers=player["headers"])
    assert read.status_code == 200, read.text
    return read.json()


async def new_for(client, player: dict) -> int:
    """The envelope's badge as this phone reads it now."""

    return (await home_of(client, player))["needs_your_answer"]["new_count"]


async def watermark_of(client, player: dict) -> str | None:
    """The watermark of a read of Home now — what a sheet drawn from it sends
    back."""

    return (await home_of(client, player))["needs_your_answer"]["watermark"]


async def closes(client, player: dict, watermark: str | None):
    return await client.post(
        VISIT, json={"watermark": watermark}, headers=player["headers"]
    )


async def closes_the_sheet(client, player: dict, watermark: str | None) -> None:
    closed = await closes(client, player, watermark)
    assert closed.status_code == 204, closed.text


async def asks_to_be_friends(client, clock, requester: dict, addressee: dict) -> None:
    """A minute on, ``requester`` asks ``addressee`` from Members."""

    clock.move(timedelta(minutes=1))
    asked = await asks(client, requester, addressee)
    assert asked.status_code == 200, asked.text


async def a_second_phone(client, name: str) -> dict:
    """The same player signed in on another phone: a session of its own."""

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{name}@example.com", "password": "hunter22!"},
    )
    assert login.status_code == 200, login.text
    return {"headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}


# --------------------------------------------------------------------------- #
# Before any visit, and the read's watermark
# --------------------------------------------------------------------------- #


async def test_before_any_visit_everything_waiting_is_new(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)

    home = await home_of(client, ines)

    assert home["needs_your_answer"]["new_count"] == 2
    # The read's watermark is the newest arrival, Kuba's request, to the
    # millisecond.
    newest = home["friend_requests"][0]
    assert newest["player_id"] == str(crew["kuba"]["id"])
    asked_at = parsed(newest["asked_at"])
    assert parsed(home["needs_your_answer"]["watermark"]) == asked_at.replace(
        microsecond=asked_at.microsecond // 1000 * 1000
    )


async def test_nothing_waiting_is_nothing_new_and_no_watermark(client, clock, crew):
    assert (await home_of(client, crew["ines"]))["needs_your_answer"] == {
        "new_count": 0,
        "watermark": None,
    }


async def test_the_count_rises_with_each_friend_request(client, clock, crew):
    ines = crew["ines"]

    for count, requester in enumerate(("tomek", "kuba", "magda"), start=1):
        await asks_to_be_friends(client, clock, crew[requester], ines)
        assert await new_for(client, ines) == count


# --------------------------------------------------------------------------- #
# The visit
# --------------------------------------------------------------------------- #


async def test_a_visit_clears_it(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)

    await closes_the_sheet(client, ines, await watermark_of(client, ines))

    assert await new_for(client, ines) == 0
    # Seen, not answered: both still wait on her.
    assert len((await home_of(client, ines))["friend_requests"]) == 2


async def test_what_arrives_after_a_visit_is_new(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await closes_the_sheet(client, ines, await watermark_of(client, ines))

    await asks_to_be_friends(client, clock, crew["kuba"], ines)

    assert await new_for(client, ines) == 1


async def test_an_item_that_arrived_after_the_read_the_visit_names_stays_new(
    client, clock, crew
):
    """The phone read Home, Kuba asked, and only then did the sheet close: the
    watermark is the read's, never the moment of the close, so Kuba's request
    was never shown and is still new."""

    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    shown = await watermark_of(client, ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)
    clock.move(timedelta(seconds=20))

    await closes_the_sheet(client, ines, shown)

    assert await new_for(client, ines) == 1


async def test_an_older_visit_changes_nothing(client, clock, crew):
    """Her phone closed on an older read after her tablet closed on a newer
    one: 204, and the newer watermark stands."""

    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    older = await watermark_of(client, ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)
    newer = await watermark_of(client, ines)
    await closes_the_sheet(client, ines, newer)

    await closes_the_sheet(client, ines, older)

    assert await new_for(client, ines) == 0


async def test_the_same_visit_twice_records_nothing_twice(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    shown = await watermark_of(client, ines)

    await closes_the_sheet(client, ines, shown)
    clock.move(timedelta(minutes=1))
    await closes_the_sheet(client, ines, shown)

    assert await new_for(client, ines) == 0


async def test_two_phones_see_one_count(client, clock, crew):
    ines = crew["ines"]
    tablet = await a_second_phone(client, "ines")
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)
    assert (await new_for(client, ines), await new_for(client, tablet)) == (2, 2)

    await closes_the_sheet(client, tablet, await watermark_of(client, tablet))

    assert (await new_for(client, ines), await new_for(client, tablet)) == (0, 0)
    await asks_to_be_friends(client, clock, crew["magda"], ines)
    assert (await new_for(client, ines), await new_for(client, tablet)) == (1, 1)


async def test_a_watermark_past_the_servers_clock_is_refused_and_records_nothing(
    client, clock, crew
):
    """No read served it: it is a phone's own clock, which would leave
    everything arriving until then seen and never shown."""

    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    ahead = (clock.now() + timedelta(minutes=5)).isoformat()

    refused = await closes(client, ines, ahead)

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == "watermark_in_the_future"
    assert await new_for(client, ines) == 1


async def test_a_watermark_with_no_offset_or_no_instant_is_unprocessable(
    client, clock, crew
):
    ines = crew["ines"]

    for watermark in ("2026-10-05T06:00:00", "yesterday"):
        answer = await closes(client, ines, watermark)
        assert answer.status_code == 422, answer.text


async def test_closing_on_a_read_with_nothing_waiting_records_nothing(
    client, clock, crew
):
    """The last answer emptied the sheet, and the phone sends the watermark of
    the read that followed, which is `null`. Nothing it showed is left."""

    ines = crew["ines"]
    await closes_the_sheet(client, ines, await watermark_of(client, ines))
    await asks_to_be_friends(client, clock, crew["tomek"], ines)

    assert await new_for(client, ines) == 1


async def test_a_watermark_kept_to_the_millisecond_is_the_same_watermark(
    client, clock, crew
):
    """A phone that turns the watermark into its own date and back sends it
    with three decimals: everything it covered is still seen."""

    ines = crew["ines"]
    # Tomek's request lands 456 µs into a millisecond, which three decimals lose.
    clock.move(timedelta(microseconds=1456 - clock.now().microsecond % 1000))
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    served = parsed(await watermark_of(client, ines))

    await closes_the_sheet(client, ines, served.isoformat(timespec="milliseconds"))

    assert await new_for(client, ines) == 0


async def test_a_visit_needs_a_signed_in_player(client, clock):
    answer = await client.post(VISIT, json={"watermark": clock.now().isoformat()})

    assert answer.status_code == 401, answer.text


# --------------------------------------------------------------------------- #
# Answering takes an item out
# --------------------------------------------------------------------------- #


async def test_accepting_a_request_drops_it_from_the_count(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await asks_to_be_friends(client, clock, crew["kuba"], ines)

    accepted = await accepts(client, ines, crew["tomek"])

    assert accepted.status_code == 200, accepted.text
    assert await new_for(client, ines) == 1


async def test_not_now_on_a_request_drops_it_from_the_count(client, clock, crew):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)

    set_aside = await sets_aside(client, ines, crew["tomek"])

    assert set_aside.status_code == 204, set_aside.text
    assert (await home_of(client, ines))["needs_your_answer"] == {
        "new_count": 0,
        "watermark": None,
    }


# --------------------------------------------------------------------------- #
# Asks for a level: each asker by their own ask
# --------------------------------------------------------------------------- #


async def test_the_count_rises_with_an_ask_for_a_level(client, clock, ogrody):
    zofia = ogrody["zofia"]
    assert await new_for(client, zofia) == 0

    await asks_her(client, clock, ogrody, "tomek")

    assert await new_for(client, zofia) == 1


async def test_a_new_asker_on_a_card_already_there_counts_by_their_own_ask(
    client, clock, ogrody
):
    """Tomek asked her for padel and she saw it; then Kuba asked for padel too.
    One card, and Kuba is a new person on it."""

    zofia = ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek")
    await closes_the_sheet(client, zofia, await watermark_of(client, zofia))

    await asks_her(client, clock, ogrody, "kuba")

    home = await home_of(client, zofia)
    [card] = home["level_asks"]
    assert [asker["nickname"] for asker in card["askers"]] == ["kuba", "tomek"]
    assert home["needs_your_answer"]["new_count"] == 1


async def test_not_now_on_an_ask_drops_every_asker_from_the_count(
    client, clock, ogrody
):
    zofia = ogrody["zofia"]
    await asks_her(client, clock, ogrody, "tomek", "kuba")
    assert await new_for(client, zofia) == 2

    set_aside = await not_now(client, zofia)

    assert set_aside.status_code == 204, set_aside.text
    assert await new_for(client, zofia) == 0


# --------------------------------------------------------------------------- #
# Unchanged
# --------------------------------------------------------------------------- #


async def test_a_visit_moves_neither_homes_badge_nor_the_bells_number(
    client, clock, mailbox, crew
):
    ines = crew["ines"]
    await asks_to_be_friends(client, clock, crew["tomek"], ines)
    await mailbox.drain()
    before = await client.get(NOTICES, headers=ines["headers"])
    assert before.json()["new_count"] == 1

    await closes_the_sheet(client, ines, await watermark_of(client, ines))

    after = await client.get(NOTICES, headers=ines["headers"])
    assert after.json()["new_count"] == 1
    assert (await home_of(client, ines))["needing_you"] == 0
