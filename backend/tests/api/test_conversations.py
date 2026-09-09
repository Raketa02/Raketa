"""The four conversation routes, end to end over HTTP.

The whole reachable path in one file: a court is built, sent, and answered — and
the acceptance opens a **room**, through the outbox, in a context neither
``challenges`` nor ``games`` knows exists.

What is asserted here and nowhere else:

**The first acceptance opens the room and writes no line.** ``seq`` 1 is whatever
happens next, and the room's first read genuinely carries ``last_entry: null``.

**Membership is the gate on every route.** A non-member reads nothing and writes
nothing, and gets the same code a room that does not exist gets.

**The sequence is gapless across both shapes**, and paging is a cursor over it
with no ``has_more`` anywhere.

**A repeat records nothing.** The same ``client_message_id`` answers with the same
message and the same ``seq``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from tests.api import matchmaking_world as world
from tests.unit.fake_event_store import FrozenClock


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_sent_challenge(client, searcher) -> str:
    response = await world.lineup(client, searcher["token"])
    assert response.status_code == 200, response.text
    body = response.json()
    court = [
        {
            "side": seat["side"],
            "player_id": seat.get("player_id", str(searcher["id"])),
        }
        for seat in body["lineup"]["seats"]
    ]
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": body["search"]["search_id"], "court": court},
        headers=world.auth(searcher["token"]),
    )
    assert sent.status_code == 201, sent.text
    return sent.json()["challenge_id"]


async def _accept(client, challenge_id: str, token: str) -> None:
    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept", headers=world.auth(token)
    )
    assert answered.status_code == 200, answered.text


async def _rooms(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/conversations", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["conversations"]


async def _say(client, conversation_id: str, token: str, text: str, client_id: str):
    return await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"text": text, "client_message_id": client_id},
        headers=world.auth(token),
    )


@pytest.fixture
async def a_room(client, session_factory, candidate_source, searcher):
    """A padel four, one acceptance in — so the room exists and is still growing."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_sent_challenge(client, searcher)
    await _accept(client, challenge_id, people["ana"]["token"])
    await world.deliver_the_outbox(session_factory)
    rooms = await _rooms(client, searcher["token"])
    assert len(rooms) == 1, rooms
    return {
        "people": people,
        "searcher": searcher,
        "challenge_id": challenge_id,
        "room": rooms[0],
    }


# -- the opening -----------------------------------------------------------


async def test_the_first_acceptance_opens_a_room_and_writes_no_line(a_room):
    """``the-words.md`` §23.1 — it **is** the opening; ``seq`` 1 is whatever
    happens next, and the first acceptor is a founding member rather than a
    sentence."""

    row = a_room["room"]

    assert row["last_entry"] is None
    assert row["challenge_id"] == a_room["challenge_id"]
    assert row["sport"] == "PADEL"


async def test_a_room_whose_line_up_is_still_filling_has_no_game(a_room):
    """``docs/adr/0148`` §2 — nullable, so a client draws no *Details* door
    rather than a dead one."""

    assert a_room["room"]["game_id"] is None


async def test_the_room_draws_the_members_it_has_and_not_the_court(a_room):
    """``docs/adr/0146`` §7 — membership grows one acceptance at a time; four
    faces on a two-member room would be drawing the court."""

    members = {member["player_id"] for member in a_room["room"]["members"]}

    assert members == {
        str(a_room["searcher"]["id"]),
        str(a_room["people"]["ana"]["id"]),
    }


async def test_the_room_grows_with_each_further_acceptance(
    client, session_factory, a_room
):
    await _accept(client, a_room["challenge_id"], a_room["people"]["bo"]["token"])
    await world.deliver_the_outbox(session_factory)

    row = (await _rooms(client, a_room["searcher"]["token"]))[0]

    assert len(row["members"]) == 3
    assert row["last_entry"]["type"] == "system_line"
    assert row["last_entry"]["code"] == "SEAT_ACCEPTED"
    assert row["last_entry"]["actor_id"] == str(a_room["people"]["bo"]["id"])
    assert row["last_entry"]["seq"] == 1


async def test_a_later_acceptance_names_its_actor_and_repeats_no_handle(
    client, session_factory, a_room
):
    """``docs/adr/0148`` §4 — ``values`` never repeats what membership says."""

    await _accept(client, a_room["challenge_id"], a_room["people"]["bo"]["token"])
    await world.deliver_the_outbox(session_factory)

    line = (await _rooms(client, a_room["searcher"]["token"]))[0]["last_entry"]

    assert line["values"] == {}


async def test_a_decline_writes_one_code_with_the_answer_as_a_value(
    client, session_factory, a_room
):
    """``the-words.md`` §23 — one leave code, and a lapse is still not a decline."""

    declined = await client.post(
        f"/api/v1/challenges/{a_room['challenge_id']}/decline",
        headers=world.auth(a_room["people"]["bo"]["token"]),
    )
    assert declined.status_code == 200, declined.text
    await world.deliver_the_outbox(session_factory)

    line = (await _rooms(client, a_room["searcher"]["token"]))[0]["last_entry"]

    assert line["code"] == "SEAT_LEFT"
    assert line["values"] == {"departure": "DECLINED"}
    assert line["actor_id"] == str(a_room["people"]["bo"]["id"])


async def test_the_send_itself_opens_nothing(
    client, session_factory, candidate_source, searcher
):
    """``the-words.md`` §23.1 — no conversation exists yet, so there is nowhere
    to write."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    await _a_sent_challenge(client, searcher)
    await world.deliver_the_outbox(session_factory)

    assert await _rooms(client, searcher["token"]) == []


# -- membership is the gate ------------------------------------------------


async def test_a_non_member_reads_nothing_and_is_told_no_such_room(client, a_room):
    """``docs/adr/0148`` §9 — 404 and not 403, on ``challenge_not_found``'s
    argument: a 403 would answer *is this id real* about a stranger's evening."""

    stranger = a_room["people"]["cy"]
    conversation_id = a_room["room"]["conversation_id"]

    detail = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=world.auth(stranger["token"]),
    )
    entries = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=world.auth(stranger["token"]),
    )

    assert detail.status_code == 404
    assert detail.json()["code"] == "conversation_not_found"
    assert entries.status_code == 404
    assert await _rooms(client, stranger["token"]) == []


async def test_a_non_member_writes_nothing(client, a_room):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["people"]["cy"]["token"],
        "let me in",
        "11111111-1111-1111-1111-111111111111",
    )

    assert refused.status_code == 404
    assert refused.json()["code"] == "conversation_not_found"


async def test_a_room_that_does_not_exist_answers_the_same_code(client, searcher):
    response = await client.get(
        "/api/v1/conversations/11111111-2222-3333-4444-555555555555",
        headers=world.auth(searcher["token"]),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "conversation_not_found"


# -- the header and the newest page ----------------------------------------


async def test_the_header_and_the_newest_page_come_back_in_one_fold(client, a_room):
    """``docs/adr/0148`` §3 — one instant, so members and entries cannot
    disagree."""

    response = await client.get(
        f"/api/v1/conversations/{a_room['room']['conversation_id']}",
        headers=world.auth(a_room["searcher"]["token"]),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["read_at"]
    assert body["entries"] == []
    assert len(body["members"]) == 2
    assert body["conversation_id"] == a_room["room"]["conversation_id"]


# -- saying something ------------------------------------------------------


async def test_a_message_lands_at_seq_one_and_carries_no_id_of_its_own(client, a_room):
    """``docs/adr/0148`` §4 — ``(conversation_id, seq)`` already identifies it."""

    said = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["searcher"]["token"],
        "  six on Thursday?  ",
        "22222222-2222-2222-2222-222222222222",
    )

    assert said.status_code == 200, said.text
    body = said.json()
    assert body["seq"] == 1
    assert body["type"] == "message"
    assert body["text"] == "six on Thursday?"
    assert "id" not in body


async def test_a_repeat_answers_the_same_message_and_records_nothing(client, a_room):
    """``docs/adr/0148`` §5 — a paused send that resumes must not become two."""

    conversation_id = a_room["room"]["conversation_id"]
    token = a_room["searcher"]["token"]
    client_id = "33333333-3333-3333-3333-333333333333"

    first = await _say(client, conversation_id, token, "on my way", client_id)
    again = await _say(client, conversation_id, token, "on my way", client_id)

    assert first.status_code == again.status_code == 200
    assert first.json() == again.json()
    page = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=world.auth(token),
    )
    assert len(page.json()["entries"]) == 1


async def test_an_empty_message_is_refused_rather_than_recorded(client, a_room):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["searcher"]["token"],
        "   ",
        "44444444-4444-4444-4444-444444444444",
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "message_is_empty"


async def test_a_message_past_the_cap_is_refused_rather_than_truncated(client, a_room):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["searcher"]["token"],
        "x" * 1001,
        "55555555-5555-5555-5555-555555555555",
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "message_is_too_long"


# -- the sequence, and paging over it --------------------------------------


async def test_the_sequence_is_gapless_across_messages_and_lines(
    client, session_factory, a_room
):
    conversation_id = a_room["room"]["conversation_id"]
    token = a_room["searcher"]["token"]

    await _say(
        client, conversation_id, token, "one", "aaaaaaaa-0000-0000-0000-000000000001"
    )
    await _accept(client, a_room["challenge_id"], a_room["people"]["bo"]["token"])
    await world.deliver_the_outbox(session_factory)
    await _say(
        client, conversation_id, token, "two", "aaaaaaaa-0000-0000-0000-000000000002"
    )

    page = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=world.auth(token),
    )

    entries = page.json()["entries"]
    assert [entry["seq"] for entry in entries] == [1, 2, 3]
    assert [entry["type"] for entry in entries] == [
        "message",
        "system_line",
        "message",
    ]


async def test_paging_is_a_cursor_over_seq_with_no_has_more_anywhere(client, a_room):
    """``docs/adr/0148`` §3 — a gapless sequence makes ``seq`` 1 the beginning,
    and a flag beside that is the same fact twice."""

    conversation_id = a_room["room"]["conversation_id"]
    token = a_room["searcher"]["token"]
    for n in range(1, 6):
        await _say(
            client,
            conversation_id,
            token,
            f"{n}",
            f"bbbbbbbb-0000-0000-0000-00000000000{n}",
        )

    newest = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries?limit=2",
        headers=world.auth(token),
    )
    older = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries?before_seq=4&limit=2",
        headers=world.auth(token),
    )
    beginning = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries?before_seq=1",
        headers=world.auth(token),
    )

    assert [entry["seq"] for entry in newest.json()["entries"]] == [4, 5]
    assert [entry["seq"] for entry in older.json()["entries"]] == [2, 3]
    assert beginning.json()["entries"] == []
    assert "has_more" not in newest.json()


async def test_an_over_large_limit_is_a_422_and_never_a_silent_clamp(client, a_room):
    """``docs/adr/0148`` §3 — a route that quietly returns something other than
    what was asked for cannot be told apart from one that ran out."""

    response = await client.get(
        f"/api/v1/conversations/{a_room['room']['conversation_id']}/entries?limit=101",
        headers=world.auth(a_room["searcher"]["token"]),
    )

    assert response.status_code == 422


# -- the whole line-up, and the game --------------------------------------


async def test_a_completed_line_up_gives_the_room_its_game_and_no_line(
    client, session_factory, a_room
):
    """``the-words.md`` §23.1 — the seats already imply it, so there is no *Game
    on* line; the event still arrives, because the room learns its game from it."""

    for who in ("bo", "cy"):
        await _accept(client, a_room["challenge_id"], a_room["people"][who]["token"])
    await world.deliver_the_outbox(session_factory)

    row = (await _rooms(client, a_room["searcher"]["token"]))[0]

    assert row["game_id"] is not None
    assert [entry["code"] for entry in await _entries(client, row, a_room)] == [
        "SEAT_ACCEPTED",
        "SEAT_ACCEPTED",
    ]


async def _entries(client, row, a_room) -> list[dict]:
    response = await client.get(
        f"/api/v1/conversations/{row['conversation_id']}/entries",
        headers=world.auth(a_room["searcher"]["token"]),
    )
    assert response.status_code == 200, response.text
    return response.json()["entries"]


async def test_the_played_line_is_the_answer_to_what_the_room_asked(
    client, session_factory, a_room
):
    """``the-words.md`` §23.1 — ``GamePlayed`` is the exception and earns it."""

    for who in ("bo", "cy"):
        await _accept(client, a_room["challenge_id"], a_room["people"][who]["token"])
    await world.deliver_the_outbox(session_factory)
    row = (await _rooms(client, a_room["searcher"]["token"]))[0]

    played = await client.post(
        f"/api/v1/games/{row['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(a_room["searcher"]["token"]),
    )
    assert played.status_code == 200, played.text
    await world.deliver_the_outbox(session_factory)

    last = (await _rooms(client, a_room["searcher"]["token"]))[0]["last_entry"]

    assert last["code"] == "GAME_PLAYED"
    assert last["actor_id"] == str(a_room["searcher"]["id"])


async def test_the_result_argument_writes_no_line_because_it_is_games(
    client, session_factory, a_room
):
    """``the-words.md`` §23.1 — one fact in one place; ``games`` has its own
    conversation for the argument."""

    for who in ("bo", "cy"):
        await _accept(client, a_room["challenge_id"], a_room["people"][who]["token"])
    await world.deliver_the_outbox(session_factory)
    row = (await _rooms(client, a_room["searcher"]["token"]))[0]
    await client.post(
        f"/api/v1/games/{row['game_id']}/result",
        json={"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}},
        headers=world.auth(a_room["searcher"]["token"]),
    )
    await world.deliver_the_outbox(session_factory)
    before = len(await _entries(client, row, a_room))

    countered = await client.post(
        f"/api/v1/games/{row['game_id']}/result",
        json={"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}},
        headers=world.auth(a_room["people"]["ana"]["token"]),
    )
    assert countered.status_code == 200, countered.text
    await world.deliver_the_outbox(session_factory)

    assert len(await _entries(client, row, a_room)) == before


# -- the lifetime ----------------------------------------------------------

#: Any uuid does; it is spelled rather than minted so the send below is the same
#: send on every run.
_A_CLIENT_MESSAGE_ID = "44444444-4444-4444-4444-444444444444"


async def _decline(client, challenge_id: str, token: str) -> None:
    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/decline", headers=world.auth(token)
    )
    assert answered.status_code == 200, answered.text


@pytest.fixture
async def a_room_that_ends(client, session_factory, a_room):
    """The same room, with its court declined to a standstill.

    A departure is the last thing that happened to this arrangement, so the room
    ends one ``CONVERSATION_GRACE`` after it (``docs/adr/0153`` §3) — the
    unanchored case, reached over HTTP rather than described.
    """

    for who in ("bo", "cy"):
        await _decline(client, a_room["challenge_id"], a_room["people"][who]["token"])
    await world.deliver_the_outbox(session_factory)
    rows = await _rooms(client, a_room["searcher"]["token"])
    assert len(rows) == 1, rows
    assert rows[0]["last_entry"]["code"] == "SEAT_LEFT"
    return a_room


def the_day_after_next(client) -> None:
    """Move the clock past every grace in this file, and nothing else.

    The room's end is derived from what it was told, so the only way to reach it
    is to be somewhere later. It is the **API's** clock that moves, which is what
    a real tomorrow moves — nothing in the database is rewritten, and the room
    that was readable a line ago is the same room.

    Shared with the stream suite, which needs the same instant against the same
    grace: a second spelling of *later than 48 hours* is how two files start
    disagreeing about which side of the boundary they are testing.
    """

    at = FrozenClock(at=datetime.now(timezone.utc) + timedelta(hours=49))
    world.override(client, get_clock, lambda: at)


async def test_a_room_past_its_end_is_gone_from_the_list(client, a_room_that_ends):
    """``docs/adr/0153`` §5 — *destroyed, not delisted*, and the read is the
    truth whether or not a sweep has run."""

    token = a_room_that_ends["searcher"]["token"]
    assert len(await _rooms(client, token)) == 1

    the_day_after_next(client)

    assert await _rooms(client, token) == []


@pytest.mark.parametrize("route", ["", "/entries"])
async def test_every_read_on_an_ended_room_answers_not_found(
    client, a_room_that_ends, route
):
    """``docs/adr/0153`` §5 — **one code for three cases**: never existed,
    destroyed, and past its end but not yet swept."""

    conversation_id = a_room_that_ends["room"]["conversation_id"]
    token = a_room_that_ends["searcher"]["token"]
    the_day_after_next(client)

    response = await client.get(
        f"/api/v1/conversations/{conversation_id}{route}", headers=world.auth(token)
    )

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "conversation_not_found"


async def test_nobody_can_say_anything_in_a_room_past_its_end(
    client, a_room_that_ends
):
    """The send is gated by the same seam every read is, so there is one place
    the answer is decided."""

    conversation_id = a_room_that_ends["room"]["conversation_id"]
    token = a_room_that_ends["searcher"]["token"]
    the_day_after_next(client)

    said = await _say(
        client, conversation_id, token, "still there?", _A_CLIENT_MESSAGE_ID
    )

    assert said.status_code == 404, said.text
    assert said.json()["code"] == "conversation_not_found"


async def test_the_room_stands_right_up_to_its_end(client, a_room_that_ends):
    """The grace is not a rounding: a room a day after the departure is a room
    two people can still be in."""

    conversation_id = a_room_that_ends["room"]["conversation_id"]
    token = a_room_that_ends["searcher"]["token"]

    response = await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=world.auth(token)
    )

    assert response.status_code == 200, response.text


# -- the withdrawal --------------------------------------------------------


async def test_a_withdrawal_destroys_the_room_in_the_same_act(
    client, session_factory, a_room_that_ends
):
    """``docs/adr/0153`` §2 — the withdrawal destroys it and writes no line,
    because there is nobody left to read one. The news is on the challenge
    screen."""

    token = a_room_that_ends["searcher"]["token"]
    conversation_id = a_room_that_ends["room"]["conversation_id"]

    withdrawn = await client.post(
        f"/api/v1/challenges/{a_room_that_ends['challenge_id']}/withdrawal",
        headers=world.auth(token),
    )
    assert withdrawn.status_code == 200, withdrawn.text
    await world.deliver_the_outbox(session_factory)

    assert await _rooms(client, token) == []
    gone = await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=world.auth(token)
    )
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"


async def test_a_withdrawn_room_is_gone_for_everybody_who_was_in_it(
    client, session_factory, a_room_that_ends
):
    """It is destroyed rather than hidden from the organiser: the member who
    accepted loses the room too, and reads the news on the challenge."""

    ana = a_room_that_ends["people"]["ana"]["token"]
    assert len(await _rooms(client, ana)) == 1

    await client.post(
        f"/api/v1/challenges/{a_room_that_ends['challenge_id']}/withdrawal",
        headers=world.auth(a_room_that_ends["searcher"]["token"]),
    )
    await world.deliver_the_outbox(session_factory)

    assert await _rooms(client, ana) == []
