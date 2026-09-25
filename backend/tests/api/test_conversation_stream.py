"""The live channel end to end: `GET /conversations/{id}/stream`.

**Every stream in this file closes on its own**, because `ASGITransport` runs the
whole application before handing back a response — it buffers rather than
streams. That is not a workaround for the assertions here, it is what makes them
sharp: a stream is opened with a **deliberately short-lived access token**, so
what is asserted is the real closing mechanism (`docs/adr/0147` §6) and the body
that comes back is every frame the stream emitted before it closed.

What is asserted here and nowhere else:

**The frame is exactly `{v, conversation_id, last_seq}`** on the wire, and one
arrives the moment the stream opens carrying the room's current high-water mark.

**A message and a system line both nudge**, through the one mechanism — the send
path and the outbox path, which is the whole of *what actually goes live*.

**A lost frame self-heals**, because the client fetches from its own high-water
mark and never from the number in the frame.

**Three things close a stream, and none of them costs a message**: the token
expiring, a subscriber that is gone, and a non-member being refused before the
response starts.

**A Redis outage takes nothing else down.** `/health` is about the process, and
sign-in and the send keep working.

**And presence rides the same stream as a second named event** (`docs/adr/0156`):
a typing frame reaches a follower, carries no `last_seq`, leaves the room's own
`last_seq` exactly where it was, and is invisible to a client following only
`nudge`. **The killed app is asserted for its own sake** — no *stopped* is sent
by anybody, the heartbeat's key expires, and the indicator goes away because
nothing kept it alive.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.modules.auth.domain.audience import Audience
from app.bootstrap.composition import build_token_service, build_typing_roster
from app.core.config import get_settings
from app.infrastructure.redis_client import get_redis, get_redis_subscriber
from app.modules.conversations.domain.live import TYPING_CHECK, TYPING_TTL
from app.modules.conversations.infrastructure.redis_live_channel import channel_for
from tests.api import matchmaking_world as world
from tests.unit.fake_redis import BrokenRedis

#: Long enough for a couple of round trips through the in-memory app, short
#: enough that a suite waiting for it is waiting for seconds and not minutes.
#: The **mechanism** under test is the token's own `exp`, which is why this is a
#: token TTL rather than a deadline handed to the route.
A_SHORT_LIFE_SECONDS = 2


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


@pytest.fixture
async def a_room(client, session_factory, candidate_source, searcher, live_channel):
    """A padel four, one acceptance in, with one thing said in it.

    The message is what gives the room a non-zero high-water mark, so that an
    opening frame carrying it is distinguishable from one carrying nothing.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_sent_challenge(client, searcher)
    accepted = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(people["ana"]["token"]),
    )
    assert accepted.status_code == 200, accepted.text
    await world.deliver_the_outbox(session_factory, live_channel=live_channel)

    rooms = await client.get(
        "/api/v1/conversations", headers=world.auth(searcher["token"])
    )
    assert rooms.status_code == 200, rooms.text
    room = rooms.json()["conversations"][0]

    said = await _say(client, room["conversation_id"], searcher["token"], "shall we")
    assert said.status_code == 200, said.text

    return {
        "people": people,
        "searcher": searcher,
        "challenge_id": challenge_id,
        "conversation_id": room["conversation_id"],
        "reader": people["ana"],
        "live_channel": live_channel,
    }


async def _say(client, conversation_id: str, token: str, text: str):
    return await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"client_message_id": str(uuid4()), "text": text},
        headers=world.auth(token),
    )


def _a_token_expiring_in(seconds: int, player_id) -> str:
    """A real access token with a real `exp`, minted seconds out.

    Through the application's own token service over a copied settings object, so
    what the route decodes is a token this application would issue — the deadline
    under test is the one written into the credential, not one a test handed the
    route through a seam.
    """

    settings = get_settings().model_copy(
        update={"ACCESS_TOKEN_EXPIRE_SECONDS": seconds}
    )
    return (
        build_token_service(settings)
        .issue_access(str(player_id), audience=Audience.PLAYER_APP)
        .token
    )


def _expires_at(token: str) -> datetime:
    """The `exp` the application itself reads off that token.

    Read back rather than computed from the TTL, because `exp` is stamped as a
    **whole second** — so a token minted at `.93` past the second expires up to a
    second earlier than its nominal life, and an assertion built on the TTL is one
    that fails on a fast morning.
    """

    decoded = build_token_service(get_settings()).decode_access(
        token, audience=Audience.PLAYER_APP
    )
    return datetime.fromtimestamp(int(decoded["exp"]), tz=timezone.utc)


def _frames(body: str) -> list[dict]:
    """Every `data:` line of an SSE body, decoded. **Both kinds.**"""

    return [
        json.loads(line[len("data:") :].strip())
        for line in body.splitlines()
        if line.startswith("data:")
    ]


def _named(body: str) -> list[tuple[str, dict]]:
    """Every frame with the `event:` name it rode under.

    **The name is the kind** (`docs/adr/0156` §5), so a test that read only the
    `data:` lines would be asserting the half of the contract a client does not
    dispatch on.
    """

    named: list[tuple[str, dict]] = []
    event: str | None = None
    for line in body.splitlines():
        if line.startswith("event:"):
            event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            named.append((event or "message", json.loads(line[len("data:") :].strip())))
            event = None
    return named


def _of_kind(body: str, kind: str) -> list[dict]:
    """What a client subscribed to exactly one event name would see."""

    return [frame for name, frame in _named(body) if name == kind]


async def _type(client, conversation_id: str, token: str):
    return await client.post(
        f"/api/v1/conversations/{conversation_id}/typing",
        headers=world.auth(token),
    )


async def _follow(client, conversation_id: str, token: str):
    return await client.get(
        f"/api/v1/conversations/{conversation_id}/stream",
        headers=world.auth(token),
    )


# -- the frame -------------------------------------------------------------


async def test_the_stream_is_an_event_stream_and_opens_with_the_high_water_mark(
    client, a_room
):
    token = _a_token_expiring_in(A_SHORT_LIFE_SECONDS, a_room["reader"]["id"])

    response = await _follow(client, a_room["conversation_id"], token)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")
    frames = _frames(response.text)
    assert frames[0] == {
        "v": 1,
        "conversation_id": a_room["conversation_id"],
        "last_seq": 1,
    }


async def test_the_frame_carries_no_content_at_all(client, a_room):
    """The whole live contract, and the reason a lost frame is harmless.

    Nothing here is a message, a system line or a plan slot — so *whether the UI
    may render what it did not read from the authoritative path* is not a rule
    anybody keeps, it is a thing this wire cannot express.
    """

    token = _a_token_expiring_in(A_SHORT_LIFE_SECONDS, a_room["reader"]["id"])
    said = await _say(
        client, a_room["conversation_id"], a_room["searcher"]["token"], "seven?"
    )
    assert said.status_code == 200

    response = await _follow(client, a_room["conversation_id"], token)

    for frame in _frames(response.text):
        assert set(frame) == {"v", "conversation_id", "last_seq"}
        assert "seven?" not in json.dumps(frame)


# -- what nudges -----------------------------------------------------------


async def _while_following_body(
    client, a_room, act, live_channel, *, seconds=A_SHORT_LIFE_SECONDS, who=None
) -> str:
    """Open a stream, do something to the room, and return the whole SSE body.

    **It waits for the subscription rather than sleeping at it.** A nudge
    published to a channel nobody is on is delivered to nobody — real pub/sub,
    asserted for its own sake below — so the act cannot run until the stream is
    actually on the channel. Polling the fake for that is deterministic where a
    sleep is a guess that goes flaky on a loaded machine.
    """

    follower = who or a_room["reader"]
    token = _a_token_expiring_in(seconds, follower["id"])
    channel = channel_for(UUID(a_room["conversation_id"]))
    following = asyncio.create_task(_follow(client, a_room["conversation_id"], token))
    while live_channel.subscribers_on(channel) == 0:
        assert not following.done(), "the stream ended before it subscribed"
        await asyncio.sleep(0.01)
    await act()
    return (await asyncio.wait_for(following, timeout=30)).text


async def _while_following(
    client, a_room, act, live_channel, *, seconds=A_SHORT_LIFE_SECONDS
):
    return _frames(
        await _while_following_body(client, a_room, act, live_channel, seconds=seconds)
    )


async def test_a_message_from_another_member_nudges_the_room(
    client, a_room, live_channel
):
    async def _say_something():
        said = await _say(
            client, a_room["conversation_id"], a_room["searcher"]["token"], "seven?"
        )
        assert said.status_code == 200, said.text

    frames = await _while_following(client, a_room, _say_something, live_channel)

    assert [frame["last_seq"] for frame in frames] == [1, 2]


async def test_a_system_line_written_by_the_outbox_nudges_the_room(
    client, a_room, session_factory, live_channel
):
    """**One mechanism carries messages and system lines alike.**

    `challenges` publishes a seat's acceptance, the room writes a line for it in
    a context that does not know a conversation exists, and the same nudge rides
    out. There is no separate live-plan feature to build and none to defer.
    """

    async def _another_seat_accepts():
        accepted = await client.post(
            f"/api/v1/challenges/{a_room['challenge_id']}/accept",
            headers=world.auth(a_room["people"]["bo"]["token"]),
        )
        assert accepted.status_code == 200, accepted.text
        await world.deliver_the_outbox(session_factory, live_channel=live_channel)

    frames = await _while_following(client, a_room, _another_seat_accepts, live_channel)

    assert [frame["last_seq"] for frame in frames] == [1, 2]


# -- a lost frame ----------------------------------------------------------


async def test_a_frame_published_while_nobody_follows_reaches_nobody(
    client, a_room, live_channel
):
    """At-most-once on the bus, driven rather than assumed."""

    channel = channel_for(UUID(a_room["conversation_id"]))
    assert live_channel.subscribers_on(channel) == 0
    before = len(live_channel.published)

    said = await _say(
        client, a_room["conversation_id"], a_room["searcher"]["token"], "anyone?"
    )
    assert said.status_code == 200

    published = live_channel.published[before:]
    assert [entry[0] for entry in published] == [channel]
    assert live_channel.subscribers_on(channel) == 0


async def test_a_dropped_frame_is_repaired_by_the_next_one(
    client, a_room, live_channel
):
    """The property the whole envelope was chosen for (`docs/adr/0147` §3).

    Two things are said while the reader is following, so two frames arrive. The
    reader **drops the first** — exactly as a severed connection, a backgrounded
    app or a missed publish would drop it — and acts only on the second, fetching
    from **its own** high-water mark rather than from that frame's `last_seq`.
    Both entries come back. The lost frame needed no detection and no repair of
    its own, which is the whole reason the frame carries no content.
    """

    reader = a_room["reader"]
    held = await client.get(
        f"/api/v1/conversations/{a_room['conversation_id']}",
        headers=world.auth(reader["token"]),
    )
    assert held.status_code == 200, held.text
    my_high_water_mark = held.json()["entries"][-1]["seq"]

    async def _say_two_things():
        for text in ("seven?", "or eight"):
            said = await _say(
                client, a_room["conversation_id"], a_room["searcher"]["token"], text
            )
            assert said.status_code == 200, said.text

    frames = await _while_following(client, a_room, _say_two_things, live_channel)

    # The room announced itself three times: on connect, and once per entry.
    assert [frame["last_seq"] for frame in frames] == [1, 2, 3]

    # **The drop.** Everything but the last frame is thrown away unread, and the
    # number in the one frame that survived is never used as a cursor — the
    # request below carries no `before_seq` and asks the read path from the
    # reader's own mark.
    acted_on = frames[-1]
    caught_up = await client.get(
        f"/api/v1/conversations/{a_room['conversation_id']}/entries",
        headers=world.auth(reader["token"]),
    )
    assert caught_up.status_code == 200, caught_up.text
    missed = [
        entry
        for entry in caught_up.json()["entries"]
        if entry["seq"] > my_high_water_mark
    ]

    # The entry the dropped frame would have announced is here, delivered by
    # acting on a later one.
    assert [entry["text"] for entry in missed] == ["seven?", "or eight"]
    assert acted_on["last_seq"] == my_high_water_mark + len(missed)


# -- what closes a stream --------------------------------------------------


async def test_the_stream_closes_when_the_access_token_does(client, a_room):
    """Not a timer the route was handed — the `exp` on the credential presented.

    It is what keeps revocation prompt, and the dividend is that reconnect runs
    every fifteen minutes in production rather than only on deploys.
    """

    token = _a_token_expiring_in(A_SHORT_LIFE_SECONDS, a_room["reader"]["id"])
    expires_at = _expires_at(token)

    response = await asyncio.wait_for(
        _follow(client, a_room["conversation_id"], token), timeout=30
    )
    closed_at = datetime.now(timezone.utc)

    assert response.status_code == 200
    # **At the token's own expiry**, not before it and not long after — a stream
    # that closed early would be a timer somebody chose, and one that closed late
    # would be live delivery on a credential that had run out.
    assert expires_at <= closed_at <= expires_at + timedelta(seconds=2)
    assert _frames(response.text) == [
        {"v": 1, "conversation_id": a_room["conversation_id"], "last_seq": 1}
    ]


async def test_a_server_whose_subscriber_is_gone_closes_the_stream(
    client, app, a_room
):
    """**A chat that is not live has to look not-live** (`docs/adr/0147` §8).

    A connection held open delivering nothing is the failure that looks like a
    quiet room. The read path is untouched, which is what makes closing the
    affordable answer.
    """

    app.dependency_overrides[get_redis_subscriber] = lambda: BrokenRedis()
    token = _a_token_expiring_in(300, a_room["reader"]["id"])

    response = await asyncio.wait_for(
        _follow(client, a_room["conversation_id"], token), timeout=30
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert _frames(response.text) == [
        {"v": 1, "conversation_id": a_room["conversation_id"], "last_seq": 1}
    ]

    still_readable = await client.get(
        f"/api/v1/conversations/{a_room['conversation_id']}",
        headers=world.auth(a_room["reader"]["token"]),
    )
    assert still_readable.status_code == 200


async def test_a_non_member_is_refused_before_the_response_starts(
    client, a_room, session_factory
):
    """A stranger gets `conversation_not_found` as JSON, never an empty stream.

    The gate runs in a dependency for exactly this: an async generator's first
    exception is raised after `200 text/event-stream` is already on the wire.
    """

    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "outsider", mu=0.0
    )

    response = await _follow(client, a_room["conversation_id"], stranger)

    assert response.status_code == 404, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["code"] == "conversation_not_found"


async def _ended_but_not_yet_swept(client, a_room, session_factory) -> None:
    """The two undecided seats say no and the one who accepted leaves: the
    organiser is alone with nobody deciding, so the challenge is over by
    itself (``docs/adr/0165`` §3) — and the outbox is **not** delivered
    afterwards, so the row still stands in the store while the challenge it
    lives as long as is over (``docs/adr/0164`` §6). *Past its end but not yet
    swept*, literally.
    """

    for who in ("bo", "cy"):
        declined = await client.post(
            f"/api/v1/challenges/{a_room['challenge_id']}/decline",
            headers=world.auth(a_room["people"][who]["token"]),
        )
        assert declined.status_code == 200, declined.text
    await world.deliver_the_outbox(
        session_factory, live_channel=a_room["live_channel"]
    )
    left = await client.post(
        f"/api/v1/challenges/{a_room['challenge_id']}/departure",
        headers=world.auth(a_room["people"]["ana"]["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "DECLINED"


async def test_a_room_past_its_end_is_refused_before_the_response_starts(
    client, a_room, session_factory
):
    """``docs/adr/0153`` §5 — **every** route on an ended room answers the same
    code, and the stream is a route.

    It matters more here than anywhere else: the gate runs in a dependency, and a
    stream that opened before it was checked would sit at `200
    text/event-stream` waiting for nudges from a room that no longer exists.
    """

    await _ended_but_not_yet_swept(client, a_room, session_factory)

    response = await _follow(
        client, a_room["conversation_id"], a_room["searcher"]["token"]
    )

    assert response.status_code == 404, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["code"] == "conversation_not_found"


# -- what an outage does not take down -------------------------------------


async def test_a_redis_outage_takes_neither_health_nor_sign_in_nor_the_send(
    client, app, a_room
):
    """`/health` stays about the **process** (`docs/adr/0147` §8).

    The obvious fix — a health check that pings Redis — would fail every task at
    once and take sign-in, onboarding and challenges down with the chat. The
    send degrades instead: the message is committed and only the nudge is lost.
    """

    app.dependency_overrides[get_redis] = lambda: BrokenRedis()

    assert (await client.get("/health")).status_code == 200

    signed_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "hunter22!"},
    )
    assert signed_in.status_code == 200, signed_in.text

    said = await _say(
        client, a_room["conversation_id"], a_room["searcher"]["token"], "still here"
    )
    assert said.status_code == 200, said.text


# -- presence --------------------------------------------------------------
#
# `docs/adr/0156`. **The second named event**, and the one rule that governs all
# of it: nothing here is durable, nothing here moves a sequence, and the only
# thing that clears an indicator is a key running out.

#: Long enough for a roster check or two inside one stream, short enough that the
#: suite is still waiting for seconds. It is longer than `A_SHORT_LIFE_SECONDS`
#: because `TYPING_CHECK` is a whole second and `exp` is stamped as a whole one,
#: so a nominal two would be a stream that sometimes closes before it has asked.
A_LONGER_LIFE_SECONDS = 4

#: What the expiry needs: a check while somebody types, a killed app, and a check
#: after the key has gone. **The waiting is the store's clock moving, not five
#: real seconds** — that is what `FakeRedis.advance` is for.
LONG_ENOUGH_TO_EXPIRE_SECONDS = 6


async def test_a_typing_heartbeat_reaches_a_follower_under_its_own_event_name(
    client, a_room, live_channel
):
    """**Two named events on one stream** (`docs/adr/0156` §5).

    The kind is the `event:` field and not a discriminator inside the JSON, so a
    client subscribes per name and a frame it has never heard of is ignored by
    the transport rather than by a branch somebody wrote.
    """

    async def _somebody_types():
        typed = await _type(
            client, a_room["conversation_id"], a_room["searcher"]["token"]
        )
        assert typed.status_code == 204, typed.text
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 1.5)

    body = await _while_following_body(
        client, a_room, _somebody_types, live_channel, seconds=A_LONGER_LIFE_SECONDS
    )

    assert _of_kind(body, "typing")[0] == {
        "v": 1,
        "conversation_id": a_room["conversation_id"],
        "player_ids": [str(a_room["searcher"]["id"])],
    }


async def test_a_typing_frame_carries_no_sequence_and_moves_none(
    client, a_room, live_channel
):
    """**The single most important invariant in this feature** (§4).

    A typing frame is not an entry. It carries no `last_seq`, and the room's own
    high-water mark is exactly where it was after any number of heartbeats — so
    a client that keyed anything on the sequence cannot be moved by somebody
    resting a finger on a keyboard.
    """

    async def _types_a_lot():
        for _ in range(5):
            typed = await _type(
                client, a_room["conversation_id"], a_room["searcher"]["token"]
            )
            assert typed.status_code == 204, typed.text
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 1.5)

    body = await _while_following_body(
        client, a_room, _types_a_lot, live_channel, seconds=A_LONGER_LIFE_SECONDS
    )

    typing = _of_kind(body, "typing")
    assert typing, "no typing frame arrived at all"
    for frame in typing:
        assert set(frame) == {"v", "conversation_id", "player_ids"}

    # **The room is exactly as long as it was.** The opening nudge said 1 and the
    # read path still says 1; no second nudge went out, because nothing landed.
    assert [frame["last_seq"] for frame in _of_kind(body, "nudge")] == [1]
    held = await client.get(
        f"/api/v1/conversations/{a_room['conversation_id']}",
        headers=world.auth(a_room["reader"]["token"]),
    )
    assert held.json()["entries"][-1]["seq"] == 1


async def test_a_client_following_only_nudge_is_unaffected(
    client, a_room, live_channel
):
    """**The envelope version does not bump, because nothing it names moved.**

    An installed client subscribes to `nudge` and never hears the new name. What
    it sees while somebody types is exactly what it saw before this existed,
    which is why telling every shipped phone that `v` had changed would have been
    a lie about its own parser.
    """

    async def _types_then_says_something():
        typed = await _type(
            client, a_room["conversation_id"], a_room["searcher"]["token"]
        )
        assert typed.status_code == 204, typed.text
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 1.5)
        said = await _say(
            client, a_room["conversation_id"], a_room["searcher"]["token"], "seven?"
        )
        assert said.status_code == 200, said.text

    body = await _while_following_body(
        client,
        a_room,
        _types_then_says_something,
        live_channel,
        seconds=A_LONGER_LIFE_SECONDS,
    )

    assert _of_kind(body, "typing"), "the typing frames are meant to be there"
    assert [frame["last_seq"] for frame in _of_kind(body, "nudge")] == [1, 2]
    assert all(frame["v"] == 1 for _, frame in _named(body))


async def test_the_expiry_clears_the_indicator_with_no_stopped_signal_at_all(
    client, a_room, live_channel
):
    """**The killed-app case, and the whole reason the shape is a heartbeat.**

    Nobody sends *stopped* — there is no such call — and nothing here pretends
    the app said goodbye. The heartbeat's key simply runs out, and the next
    roster check finds nobody. A design where a *stopped* cleared the indicator
    would leave this room showing somebody typing for ever.
    """

    async def _types_and_is_killed():
        typed = await _type(
            client, a_room["conversation_id"], a_room["searcher"]["token"]
        )
        assert typed.status_code == 204, typed.text
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 1.5)
        # The phone goes away. No request is made, nothing is told, and the only
        # thing that happens is that time passes.
        live_channel.advance(TYPING_TTL.total_seconds() + 1)
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 1.5)

    body = await _while_following_body(
        client,
        a_room,
        _types_and_is_killed,
        live_channel,
        seconds=LONG_ENOUGH_TO_EXPIRE_SECONDS,
    )

    assert [frame["player_ids"] for frame in _of_kind(body, "typing")] == [
        [str(a_room["searcher"]["id"])],
        [],
    ]


async def test_your_own_typing_is_never_echoed_back_to_you(
    client, a_room, live_channel
):
    """Or the composer draws an indicator for the person using it (§4)."""

    async def _the_reader_types():
        typed = await _type(
            client, a_room["conversation_id"], a_room["reader"]["token"]
        )
        assert typed.status_code == 204, typed.text
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 2.5)

    body = await _while_following_body(
        client, a_room, _the_reader_types, live_channel, seconds=A_LONGER_LIFE_SECONDS
    )

    assert _of_kind(body, "typing") == []
    # **And it is a filter on the way out, not a refusal on the way in.** The
    # heartbeat was recorded — it is the reader's own stream that drops them, so
    # everybody else in the room sees it.
    roster = await build_typing_roster(live_channel).who_is_typing(
        UUID(a_room["conversation_id"])
    )
    assert roster == frozenset({a_room["reader"]["id"]})


async def test_a_non_member_cannot_say_they_are_typing(client, a_room, session_factory):
    """The send's own arm, verbatim: one code for *no such room* and *not yours*."""

    _, stranger = await world.a_signed_in_candidate(
        client, session_factory, "typist", mu=0.0
    )

    refused = await _type(client, a_room["conversation_id"], stranger)

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "conversation_not_found"


async def test_a_room_past_its_end_refuses_the_heartbeat(
    client, a_room, session_factory
):
    """`docs/adr/0153` §5 — **every** route on an ended room answers the same
    code, and this is a route."""

    await _ended_but_not_yet_swept(client, a_room, session_factory)

    refused = await _type(
        client, a_room["conversation_id"], a_room["searcher"]["token"]
    )

    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "conversation_not_found"


async def test_an_ephemeral_store_that_is_gone_costs_the_indicator_and_nothing_else(
    client, app, a_room, live_channel
):
    """**Redis absent: the app runs, the stream works, nobody is ever typing.**

    This is the one place the new pair does *not* mirror the nudge ports'
    asymmetry, and `docs/adr/0156` §6 argues it: a subscription **is** the room's
    liveness, so it closes the stream, while a roster is a courtesy read on the
    client with a two-second deadline, asked once a second by every open
    conversation screen. Failing it loud would let a merely slow store close
    every healthy stream on the platform — a flap invented to report that nobody
    is typing.
    """

    app.dependency_overrides[get_redis] = lambda: BrokenRedis()

    typed = await _type(client, a_room["conversation_id"], a_room["searcher"]["token"])
    assert typed.status_code == 204, typed.text

    async def _wait_for_a_check():
        await asyncio.sleep(TYPING_CHECK.total_seconds() * 2.5)

    body = await _while_following_body(
        client, a_room, _wait_for_a_check, live_channel, seconds=A_LONGER_LIFE_SECONDS
    )

    assert _of_kind(body, "nudge") == [
        {"v": 1, "conversation_id": a_room["conversation_id"], "last_seq": 1}
    ]
    assert _of_kind(body, "typing") == []
