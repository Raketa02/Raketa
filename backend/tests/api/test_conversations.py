"""The conversation routes, end to end over HTTP.

The whole reachable path in one file: a game is booked, and its ``GamePlanned``
— the one with an hour on it — opens a **room** through the outbox, in a
context ``games`` does not know exists (#575).

What is asserted here and nowhere else:

**A booked game opens its room and writes no line.** The room is filed under
the booking, born about the game, and ``seq`` 1 is whatever happens next.

**Membership is the gate on every route.** A non-member reads nothing and writes
nothing, and gets the same code a room that does not exist gets.

**The sequence is gapless across both shapes**, and paging is a cursor over it
with no ``has_more`` anywhere.

**A repeat records nothing.** The same ``client_message_id`` answers with the same
message and the same ``seq``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.bootstrap.composition import (
    build_domain_event_store,
    build_event_publisher,
    build_game_repository,
)
from app.kernel import instant
from app.modules.conversations.domain.lifetime import CONVERSATION_GRACE
from tests.api import players_world as players

#: Any uuid does; it is spelled rather than minted so the send below is the same
#: send on every run.
_A_CLIENT_MESSAGE_ID = "44444444-4444-4444-4444-444444444444"

_A_SCORE = {"score": {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}}
_THE_OTHER_SCORE = {"score": {"sets": [{"a": 4, "b": 6}, {"a": 3, "b": 6}]}}


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
async def four(client, session_factory) -> dict:
    """``ana`` and ``bo`` against ``cy`` and ``dee``, each rated in padel."""

    people = {}
    for name in ("ana", "bo", "cy", "dee"):
        player_id, token = await players.a_player_on_the_log(
            client, session_factory, name, mu=2.75
        )
        people[name] = {"id": player_id, "token": token}
    return people


async def _book(session_factory, four: dict, *, starts_at: datetime) -> dict:
    return await players.a_booked_game(
        session_factory,
        side_a=(four["ana"]["id"], four["bo"]["id"]),
        side_b=(four["cy"]["id"], four["dee"]["id"]),
        starts_at=starts_at,
    )


async def _a_booked_room(client, session_factory, four, *, starts_at) -> dict:
    booked = await _book(session_factory, four, starts_at=starts_at)
    await players.deliver_the_outbox(session_factory)
    rooms = await _rooms(client, four["ana"]["token"])
    assert len(rooms) == 1, rooms
    return {**booked, "people": four, "room": rooms[0], "starts_at": starts_at}


@pytest.fixture
async def a_room(client, session_factory, four):
    """A padel four booked for this time tomorrow, its room opened."""

    return await _a_booked_room(
        client, session_factory, four, starts_at=_now() + timedelta(days=1)
    )


@pytest.fixture
async def a_played_room(client, session_factory, four):
    """A padel four whose booked hour began an hour ago — so *we played* is
    what somebody says next."""

    return await _a_booked_room(
        client, session_factory, four, starts_at=_now() - timedelta(hours=1)
    )


async def _rooms(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/conversations", headers=players.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["conversations"]


async def _room_read(client, conversation_id: str, token: str):
    return await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=players.auth(token)
    )


async def _entries(client, conversation_id: str, token: str) -> list[dict]:
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=players.auth(token),
    )
    assert response.status_code == 200, response.text
    return response.json()["entries"]


async def _say(client, conversation_id: str, token: str, text: str, client_id: str):
    return await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"text": text, "client_message_id": client_id},
        headers=players.auth(token),
    )


async def _state(client, game_id: UUID, token: str, score: dict = _A_SCORE):
    stated = await client.post(
        f"/api/v1/games/{game_id}/result", json=score, headers=players.auth(token)
    )
    assert stated.status_code == 200, stated.text


async def _on_the_game(session_factory, game_id: UUID, act) -> None:
    """One act on the booked game, through the aggregate — as ``bookings`` tells
    it in its own transaction; this file has no booking to leave through."""

    async with session_factory() as session:
        games = build_game_repository(
            session=session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        game = await games.load(game_id)
        assert game is not None
        act(game, instant(_now()))
        await games.save(game)
        await session.commit()


async def _leaves(session_factory, game_id: UUID, player_id: UUID) -> None:
    await _on_the_game(
        session_factory,
        game_id,
        lambda game, at: game.vacate(player_id, occurred_at=at),
    )


def _faces(people: list[dict]) -> dict[str, str | None]:
    return {person["player_id"]: person["nickname"] for person in people}


# -- the opening -----------------------------------------------------------


async def test_a_booked_game_opens_its_room_about_the_game_and_writes_no_line(
    client, session_factory, four
):
    """#575 — the outbox opens it, not the booking's own transaction; it is
    born about the game, and ``seq`` 1 is whatever happens next."""

    booked = await _book(session_factory, four, starts_at=_now() + timedelta(days=1))
    assert await _rooms(client, four["ana"]["token"]) == []

    await players.deliver_the_outbox(session_factory)

    (row,) = await _rooms(client, four["ana"]["token"])
    assert row["game_id"] == str(booked["game_id"])
    assert row["last_entry"] is None
    assert row["sport"] == "PADEL"


async def test_a_booked_room_is_found_by_its_booking(client, a_room):
    """#575 — the row and the read both carry the booking the game was opened
    from, and nothing a challenge named."""

    row = a_room["room"]
    read = await _room_read(
        client, row["conversation_id"], a_room["people"]["ana"]["token"]
    )

    assert read.status_code == 200, read.text
    assert row["booking_id"] == str(a_room["booking_id"])
    assert read.json()["booking_id"] == str(a_room["booking_id"])
    assert "challenge_id" not in row
    assert "challenge_id" not in read.json()


async def test_the_room_s_members_are_the_game_s_line_up(a_room):
    """``docs/adr/0146`` §7 — the people booked on this game, read off it."""

    members = {member["player_id"] for member in a_room["room"]["members"]}

    assert members == {str(person["id"]) for person in a_room["people"].values()}


async def test_every_player_on_the_game_finds_the_same_room(client, a_room):
    for person in a_room["people"].values():
        (row,) = await _rooms(client, person["token"])
        assert row["conversation_id"] == a_room["room"]["conversation_id"]


# -- membership is the gate ------------------------------------------------


@pytest.fixture
async def stranger(client) -> dict:
    player_id, token = await players.register(client, "eve")
    return {"id": player_id, "token": token}


async def test_a_non_member_reads_nothing_and_is_told_no_such_room(
    client, a_room, stranger
):
    """``docs/adr/0148`` §9 — 404 and not 403: a 403 would answer *is this id
    real* about a stranger's evening."""

    conversation_id = a_room["room"]["conversation_id"]

    detail = await _room_read(client, conversation_id, stranger["token"])
    entries = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=players.auth(stranger["token"]),
    )

    assert detail.status_code == 404
    assert detail.json()["code"] == "conversation_not_found"
    assert entries.status_code == 404
    assert await _rooms(client, stranger["token"]) == []


async def test_a_non_member_writes_nothing(client, a_room, stranger):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        stranger["token"],
        "let me in",
        "11111111-1111-1111-1111-111111111111",
    )

    assert refused.status_code == 404
    assert refused.json()["code"] == "conversation_not_found"


async def test_a_room_that_does_not_exist_answers_the_same_code(client, a_room):
    response = await _room_read(
        client,
        "11111111-2222-3333-4444-555555555555",
        a_room["people"]["ana"]["token"],
    )

    assert response.status_code == 404
    assert response.json()["code"] == "conversation_not_found"


# -- the header and the newest page ----------------------------------------


async def test_the_header_and_the_newest_page_come_back_in_one_fold(client, a_room):
    """``docs/adr/0148`` §3 — one instant, so members and entries cannot
    disagree."""

    response = await _room_read(
        client, a_room["room"]["conversation_id"], a_room["people"]["ana"]["token"]
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["read_at"]
    assert body["entries"] == []
    assert len(body["members"]) == 4
    assert body["conversation_id"] == a_room["room"]["conversation_id"]
    assert body["game_id"] == str(a_room["game_id"])


# -- saying something ------------------------------------------------------


async def test_a_message_lands_at_seq_one_and_carries_no_id_of_its_own(client, a_room):
    """``docs/adr/0148`` §4 — ``(conversation_id, seq)`` already identifies it."""

    said = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["people"]["ana"]["token"],
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
    token = a_room["people"]["ana"]["token"]
    client_id = "33333333-3333-3333-3333-333333333333"

    first = await _say(client, conversation_id, token, "on my way", client_id)
    again = await _say(client, conversation_id, token, "on my way", client_id)

    assert first.status_code == again.status_code == 200
    assert first.json() == again.json()
    assert len(await _entries(client, conversation_id, token)) == 1


async def test_an_empty_message_is_refused_rather_than_recorded(client, a_room):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["people"]["ana"]["token"],
        "   ",
        "44444444-4444-4444-4444-444444444444",
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "message_is_empty"


async def test_a_message_past_the_cap_is_refused_rather_than_truncated(client, a_room):
    refused = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["people"]["ana"]["token"],
        "x" * 1001,
        "55555555-5555-5555-5555-555555555555",
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "message_is_too_long"


# -- the sequence, and paging over it --------------------------------------


async def test_the_sequence_is_gapless_across_messages_and_lines(
    client, session_factory, a_played_room
):
    conversation_id = a_played_room["room"]["conversation_id"]
    token = a_played_room["people"]["ana"]["token"]

    await _say(
        client, conversation_id, token, "one", "aaaaaaaa-0000-0000-0000-000000000001"
    )
    await _state(client, a_played_room["game_id"], token)
    await players.deliver_the_outbox(session_factory)
    await _say(
        client, conversation_id, token, "two", "aaaaaaaa-0000-0000-0000-000000000002"
    )

    entries = await _entries(client, conversation_id, token)

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
    token = a_room["people"]["ana"]["token"]
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
        headers=players.auth(token),
    )
    older = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries?before_seq=4&limit=2",
        headers=players.auth(token),
    )
    beginning = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries?before_seq=1",
        headers=players.auth(token),
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
        headers=players.auth(a_room["people"]["ana"]["token"]),
    )

    assert response.status_code == 422


# -- somebody leaves the game -----------------------------------------------


@pytest.fixture
async def a_room_somebody_left(client, session_factory, a_room):
    """The same room, where ``bo`` said something and then left the game.

    His message is the newest entry and its author is **no longer a member**:
    membership is the game's current line-up, so ``bo`` is named by the page and
    by nothing the roster says ([#408](https://github.com/Rakieta02/Rakieta/issues/408)).
    """

    said = await _say(
        client,
        a_room["room"]["conversation_id"],
        a_room["people"]["bo"]["token"],
        "can't make it, sorry",
        "66666666-6666-6666-6666-666666666666",
    )
    assert said.status_code == 200, said.text
    await _leaves(session_factory, a_room["game_id"], a_room["people"]["bo"]["id"])
    return a_room


async def test_a_leaver_drops_out_of_the_room_the_moment_they_leave(
    client, a_room_somebody_left
):
    """``docs/adr/0146`` §7 — the roster moves with the court, read live, and
    the one who left reads and writes nothing in it any more."""

    room = a_room_somebody_left
    conversation_id = room["room"]["conversation_id"]
    bo = room["people"]["bo"]

    (row,) = await _rooms(client, room["people"]["ana"]["token"])
    assert {member["player_id"] for member in row["members"]} == {
        str(room["people"][name]["id"]) for name in ("ana", "cy", "dee")
    }
    assert await _rooms(client, bo["token"]) == []
    gone = await _room_read(client, conversation_id, bo["token"])
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"
    said = await _say(
        client, conversation_id, bo["token"], "wait", _A_CLIENT_MESSAGE_ID
    )
    assert said.status_code == 404, said.text


async def test_the_room_names_the_person_who_left_beside_the_members(
    client, a_room_somebody_left
):
    """[#408](https://github.com/Rakieta02/Rakieta/issues/408) — *bo* and never
    *?*. ``people`` is everybody the response names, resolved once, and the
    departed are among them."""

    room = a_room_somebody_left
    response = await _room_read(
        client, room["room"]["conversation_id"], room["people"]["ana"]["token"]
    )

    assert response.status_code == 200, response.text
    body = response.json()
    bo = str(room["people"]["bo"]["id"])
    assert body["entries"][-1]["author_id"] == bo
    assert bo not in {member["player_id"] for member in body["members"]}
    assert _faces(body["people"])[bo] == "bo"
    assert set(_faces(body["people"])) == {
        member["player_id"] for member in body["members"]
    } | {bo}


async def test_the_row_names_the_person_its_last_entry_is_about(
    client, a_room_somebody_left
):
    """The Chats row's second line is the last entry, and its author may have
    left the court since."""

    room = a_room_somebody_left
    (row,) = await _rooms(client, room["people"]["ana"]["token"])

    bo = str(room["people"]["bo"]["id"])
    assert row["last_entry"]["author_id"] == bo
    assert _faces(row["people"])[bo] == "bo"
    assert {member["player_id"] for member in row["members"]} <= set(
        _faces(row["people"])
    )


async def test_a_page_names_the_people_on_it_and_nobody_else(
    client, a_room_somebody_left
):
    """A page carries no header and no roster — only the faces of whoever it
    names, so a client paging back can fill every ``{name}`` on it."""

    room = a_room_somebody_left
    conversation_id = room["room"]["conversation_id"]
    token = room["people"]["ana"]["token"]
    await _say(client, conversation_id, token, "still on?", _A_CLIENT_MESSAGE_ID)

    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=players.auth(token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [entry["type"] for entry in body["entries"]] == ["message", "message"]
    assert _faces(body["people"]) == {
        str(room["people"]["bo"]["id"]): "bo",
        str(room["people"]["ana"]["id"]): "ana",
    }


async def test_a_room_where_nothing_has_happened_names_only_its_members(a_room):
    """``people`` is a superset of ``members`` on the row and on the room, and
    with no entry it is exactly the members."""

    row = a_room["room"]

    assert row["last_entry"] is None
    assert _faces(row["people"]) == _faces(row["members"])


async def test_people_are_ordered_by_id_and_never_by_a_set(
    client, a_room_somebody_left
):
    """``docs/adr/0105`` §1 — two identical requests answer in one order."""

    room = a_room_somebody_left
    response = await _room_read(
        client, room["room"]["conversation_id"], room["people"]["ana"]["token"]
    )

    ids = [person["player_id"] for person in response.json()["people"]]
    assert ids == sorted(ids)


async def test_a_called_off_game_takes_its_room_with_it(
    client, session_factory, a_room
):
    """``docs/adr/0165`` §3 — the club takes the court back, and the call-off
    destroys the room and writes no line: there is nobody left to read one."""

    conversation_id = a_room["room"]["conversation_id"]
    await _on_the_game(
        session_factory,
        a_room["game_id"],
        lambda game, at: game.call_off_whole(occurred_at=at),
    )
    await players.deliver_the_outbox(session_factory)

    for person in a_room["people"].values():
        token = person["token"]
        assert await _rooms(client, token) == []
        gone = await _room_read(client, conversation_id, token)
        assert gone.status_code == 404, gone.text
        assert gone.json()["code"] == "conversation_not_found"


# -- we played ---------------------------------------------------------------


async def test_the_played_line_is_the_answer_to_what_the_room_asked(
    client, session_factory, a_played_room
):
    """``the-words.md`` §23.1 — ``GamePlayed`` is the one line a booked room is
    told, and it names who said so and nothing else."""

    ana = a_played_room["people"]["ana"]
    await _state(client, a_played_room["game_id"], ana["token"])
    await players.deliver_the_outbox(session_factory)

    (row,) = await _rooms(client, ana["token"])

    assert row["last_entry"]["type"] == "system_line"
    assert row["last_entry"]["code"] == "GAME_PLAYED"
    assert row["last_entry"]["actor_id"] == str(ana["id"])
    assert row["last_entry"]["values"] == {}
    assert row["last_entry"]["seq"] == 1


async def test_the_result_argument_writes_no_line_because_it_is_games(
    client, session_factory, a_played_room
):
    """``the-words.md`` §23.1 — one fact in one place; ``games`` has its own
    conversation for the argument."""

    conversation_id = a_played_room["room"]["conversation_id"]
    ana = a_played_room["people"]["ana"]
    await _state(client, a_played_room["game_id"], ana["token"])
    await players.deliver_the_outbox(session_factory)
    before = await _entries(client, conversation_id, ana["token"])

    await _state(
        client,
        a_played_room["game_id"],
        a_played_room["people"]["cy"]["token"],
        _THE_OTHER_SCORE,
    )
    await players.deliver_the_outbox(session_factory)

    assert await _entries(client, conversation_id, ana["token"]) == before


# -- the end, before anything sweeps -----------------------------------------
#
# The ``clock`` fixture is the API's: a room's end is derived from what it was
# told, so the only way to reach it is to be somewhere later. Nothing in the
# store is rewritten, and nothing here runs the sweep.


async def _entry_closes_at(client, token: str) -> datetime:
    """The instant the game's own read says *we played* stops being sayable."""

    games = await client.get("/api/v1/games", headers=players.auth(token))
    assert games.status_code == 200, games.text
    (game,) = games.json()["games"]
    return datetime.fromisoformat(game["entry_closes_at"])


async def test_an_unrecorded_games_room_ends_when_its_entry_window_closes(
    client, clock, a_room
):
    """``docs/adr/0153`` §2 — measured from the booked hour: the instant *we
    played* stops being sayable, the room goes with the game."""

    token = a_room["people"]["ana"]["token"]
    conversation_id = a_room["room"]["conversation_id"]
    closes_at = await _entry_closes_at(client, token)

    clock.at = closes_at - timedelta(seconds=1)
    standing = await _room_read(client, conversation_id, token)
    assert standing.status_code == 200, standing.text

    clock.at = closes_at
    assert await _rooms(client, token) == []
    gone = await _room_read(client, conversation_id, token)
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"


async def test_a_played_games_room_still_ends_when_its_entry_window_closes(
    client, session_factory, clock, four
):
    """``docs/adr/0153`` §2 — the **earlier** of the two anchors. No score is
    taken before the hour (#654), so *we played* plus its forty-eight hours
    always falls after a booked game's entry window closes, a day after its
    hour: a played game's room goes when the window does."""

    starts_at = clock.at + timedelta(days=4)
    room = await _a_booked_room(client, session_factory, four, starts_at=starts_at)
    token = four["ana"]["token"]
    conversation_id = room["room"]["conversation_id"]
    closes_at = await _entry_closes_at(client, token)
    said_at = clock.at = starts_at + timedelta(hours=1, minutes=5)
    await _state(client, room["game_id"], token)
    await players.deliver_the_outbox(session_factory)
    assert said_at + CONVERSATION_GRACE > closes_at

    clock.at = closes_at - timedelta(seconds=1)
    standing = await _room_read(client, conversation_id, token)
    assert standing.status_code == 200, standing.text

    clock.at = closes_at
    assert await _rooms(client, token) == []
    gone = await _room_read(client, conversation_id, token)
    assert gone.status_code == 404, gone.text
    assert gone.json()["code"] == "conversation_not_found"


@pytest.fixture
async def an_ended_room(client, clock, a_room):
    """The same room, with the API's clock at its game's entry window closing —
    *past its end but not yet swept*, literally."""

    clock.at = await _entry_closes_at(client, a_room["people"]["ana"]["token"])
    return a_room


@pytest.mark.parametrize("route", ["", "/entries"])
async def test_every_read_on_an_ended_room_answers_not_found(
    client, an_ended_room, route
):
    """``docs/adr/0153`` §5 — **one code for three cases**: never existed,
    destroyed, and past its end but not yet swept."""

    conversation_id = an_ended_room["room"]["conversation_id"]
    token = an_ended_room["people"]["ana"]["token"]

    response = await client.get(
        f"/api/v1/conversations/{conversation_id}{route}", headers=players.auth(token)
    )

    assert response.status_code == 404, response.text
    assert response.json()["code"] == "conversation_not_found"


async def test_nobody_can_say_anything_in_a_room_past_its_end(client, an_ended_room):
    """The send is gated by the same seam every read is, so there is one place
    the answer is decided."""

    said = await _say(
        client,
        an_ended_room["room"]["conversation_id"],
        an_ended_room["people"]["ana"]["token"],
        "still there?",
        _A_CLIENT_MESSAGE_ID,
    )

    assert said.status_code == 404, said.text
    assert said.json()["code"] == "conversation_not_found"
