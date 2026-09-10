"""The loop, walked end to end over HTTP — **the half of the gate that runs in CI.**

*Somebody asks, somebody answers, they arrange it, they play, and the result moves
both levels.* Every other file in this suite proves one link of that chain against
a world it stands up for itself; this one walks the whole chain once, in order, as
the two people walking it — and it is the only place the destination is asserted
at all.

**Nothing stands in for a step.** Every act is a request a phone makes: the send,
the inbox read, the detail read, the answer, the three slot writes, the entry, the
acceptance. The only two things that are not requests are the two that are not
requests in production either — the outbox poll that tells the room, and the
rating catch-up, which exists precisely because *nothing announces a confirmation*
(``docs/adr/0137``, ``docs/adr/0139``).

**It walks forward through eight hours rather than sitting still.** A result is
confirmed six hours after the score was proposed, so a journey that happened all
at one instant could not reach a moved Level without somebody advancing a clock
past the acceptance grace — and the honest way to do that is the way a Tuesday
does it: the journey starts eight hours ago and ends now. The API's clock is a
dependency and moving it is the whole mechanism; nothing in the database is
rewritten, and the catch-up at the end runs on the **wall** clock, unmoved,
because that is the clock the job holds in production.

**The standings are asserted at every step, and so are the card names folded from
them.** ``frontend_player/src/features/plans/domain/gameCard.ts`` folds a card's
name from a standing, a plan's slot count and one instant; :func:`_card_name`
below is that fold, spelled here so that a state which stops being reachable
fails in this repository rather than on somebody's phone. The client owns the
**names**; what this file owns is that the wire still carries what the fold needs.

**Two journeys, because the doubles path is a different shape.** The first is a
singles game from a send to two moved Levels. The second is the half-built court:
a line-up nobody finished, the ⚡ that names the challenge it completes, a second
acceptance growing the room, and the withdraw that destroys it — the one
conclusion the seats cannot reach (``docs/adr/0142``).

Its counterpart is ``app/seeds/`` — the same states, reached by ``make seed`` and
asserted there. **That half needs a database and does not run in CI. This half
does**, and the split is the same one the ruleset gate ships with.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_settle_ratings_on_results
from app.kernel import Sport, instant
from app.modules.games.domain.windows import ACCEPTANCE_GRACE
from app.modules.plans.domain.slots import local_day
from tests.api import matchmaking_world as world
from tests.unit.fake_event_store import FrozenClock

#: How far back the journey starts. **Comfortably past the acceptance grace**, so
#: that the score agreed part way through has genuinely settled by the time the
#: catch-up reads it, and still inside a single day so that no plan chip and no
#: answer window is crossed for a reason the journey did not intend.
A_WORKING_DAY = ACCEPTANCE_GRACE + timedelta(hours=2)

#: The score the winner states. Two straight sets, so which side won is not a
#: judgement anybody has to make twice.
STRAIGHT_SETS = {"sets": [{"a": 6, "b": 4}, {"a": 6, "b": 3}]}


# ---------------------------------------------------------------------------
# The fold the client draws its card names from
# ---------------------------------------------------------------------------


#: The plan's three slots, in the order ``docs/adr/0144`` fixed them.
SLOTS = ("place", "day", "hour")


def _card_name(game: dict, plan: dict | None, *, read_at: datetime) -> str:
    """Which card the Now rail draws for this game, folded the client's way.

    A transcription of ``features/plans/domain/gameCard.ts`` and the ladder it
    reads, kept in the same order: **the standing decides first**, and only
    ``AWAITING_ENTRY`` reaches the four rungs. It is spelled here rather than
    imported because it lives in the other app and the two may never import each
    other — what crosses between them is the contract, and what this asserts is
    that the contract still carries the three facts the fold reads.

    ``read_at`` is ``GET /games``' own instant and there is deliberately no second
    one: ``GET /plans`` carries none, so the rail folds against one clock by
    construction.

    **There is a second transcription of this fold and it is deliberate.**
    ``app/seeds/loop.py`` folds the same ladder over the *domain* objects a seed
    run holds, where this one folds it over the **wire** — which is the half a
    client actually reads, and the half that can lose a field without any domain
    test noticing. Neither can be written in terms of the other without an adapter
    between a dict and an aggregate; what keeps them together is that the ladder
    is nine lines and both name the file that owns it.
    """

    standing = game["standing"]
    if standing != "AWAITING_ENTRY":
        return {
            "AWAITING_ANSWER": "confirm",
            "CONFIRMED": "counted",
            "UNSCORED": "uncounted",
            "NEVER_PLAYED": "never-played",
        }[standing]
    agreed = None if plan is None else plan["agreed_point"]
    if agreed is not None and datetime.fromisoformat(agreed) <= read_at:
        return "needs-result"
    today = local_day(instant(read_at)).isoformat()
    if plan is not None and plan["day"] == today:
        return "today"
    if plan is not None and all(plan[slot] is not None for slot in SLOTS):
        return "game-on"
    return "planning"


# ---------------------------------------------------------------------------
# The two people, and the clock they walk through
# ---------------------------------------------------------------------------


@pytest.fixture
def journey_clock(client):
    """The API's clock, stopped at the moment this journey starts.

    Handed to the application through the same dependency a request resolves, so
    every ``occurred_at`` the journey writes is the journey's own — a seat's
    deadline, a proposal's window, a room's opening. Moving ``at`` is what makes
    time pass.
    """

    clock = FrozenClock(at=datetime.now(timezone.utc) - A_WORKING_DAY)
    world.override(client, get_clock, lambda: clock)
    return clock


async def _a_player(client, name: str, *, sport: Sport) -> dict:
    """One player ready to play this sport, through the four routes onboarding is.

    Registered, profiled, rated and declared — never appended into the log — so
    that the person this journey walks as is the person the platform makes.
    """

    player_id, token = await world.register(client, name)
    await world.commit_profile(client, token)
    mu = await world.rate(client, token, sport=sport)
    await world.declare_intent(client, token, sport=sport)
    return {"id": player_id, "token": token, "mu": mu, "name": name}


async def _challenges(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/challenges", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["challenges"]


async def _challenge(client, token: str, challenge_id: str) -> dict:
    response = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(token)
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _games(client, token: str) -> tuple[datetime, list[dict]]:
    """This player's games, and **the one instant they were all folded against.**"""

    response = await client.get("/api/v1/games", headers=world.auth(token))
    assert response.status_code == 200, response.text
    body = response.json()
    return datetime.fromisoformat(body["read_at"]), body["games"]


async def _plans(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/plans", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["plans"]


async def _rooms(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/conversations", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["conversations"]


async def _ratings(client, token: str) -> dict[str, float]:
    response = await client.get("/api/v1/ratings", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return {row["sport"]: row["mu"] for row in response.json()["ratings"]}


async def _the_card(client, token: str) -> tuple[dict, str]:
    """This player's one game and the name its card carries, read as they read it.

    **Two reads and a join**, which is what the rail is: ``GET /games`` folds the
    standing against its own instant and ``GET /plans`` carries no instant at all,
    so Now has one clock by construction (``docs/adr/0148`` §10).
    """

    read_at, games = await _games(client, token)
    (game,) = games
    plans = {plan["game_id"]: plan for plan in await _plans(client, token)}
    return game, _card_name(game, plans.get(game["game_id"]), read_at=read_at)


# ---------------------------------------------------------------------------
# The journey
# ---------------------------------------------------------------------------


async def test_a_challenge_becomes_a_game_and_the_game_moves_both_levels(
    client, session_factory, candidate_source, exposure_ledger, journey_clock
):
    """**The destination.** One send, one answer, one arrangement, one result.

    Asserted step by step rather than at the end, because the value of this test
    is which link broke and not that the chain did. Every assertion is a fact a
    screen draws: the standing at the top of the challenge screen, the row in the
    inbox, the room in the Chats tab, the card in the Now rail, and the two
    Levels the whole loop exists to move.
    """

    world.draw_real_cards(client, candidate_source, exposure_ledger)
    sender = await _a_player(client, "juno", sport=Sport.TENNIS)
    invitee = await _a_player(client, "milo", sport=Sport.TENNIS)
    await world.fold_the_log(session_factory, candidate_source)

    # --- somebody asks -----------------------------------------------------
    found = await world.search(client, sender["token"], sport=Sport.TENNIS)
    assert found.status_code == 200, found.text
    body = found.json()
    assert [row["player_id"] for row in body["candidates"]] == [str(invitee["id"])], (
        "the journey's own opponent has to be findable before anybody is asked"
    )
    sent = await client.post(
        "/api/v1/challenges",
        json={
            "search_id": body["search"]["search_id"],
            "court": [
                {"side": "A", "player_id": str(sender["id"])},
                {"side": "B", "player_id": str(invitee["id"])},
            ],
        },
        headers=world.auth(sender["token"]),
    )
    assert sent.status_code == 201, sent.text
    challenge_id = sent.json()["challenge_id"]

    # --- and the other one is told -----------------------------------------
    (row,) = await _challenges(client, invitee["token"])
    assert row["challenge_id"] == challenge_id
    assert row["standing"] == "AWAITING_ANSWERS"
    mine = [seat for seat in row["seats"] if seat["player_id"] == str(invitee["id"])]
    assert [seat["answer"] for seat in mine] == [None]
    assert mine[0]["answer_by"] is not None, (
        "the row the badge counts is the row with a clock of mine running"
    )

    detail = await _challenge(client, invitee["token"], challenge_id)
    assert detail["standing"] == "AWAITING_ANSWERS"
    theirs = next(
        seat for seat in detail["seats"] if seat["player_id"] == str(sender["id"])
    )
    assert theirs["nickname"] == sender["name"]
    assert "pairing_absence" not in detail
    assert theirs["card"]["person"]["nickname"] == sender["name"], (
        "an invitee reads who asked them, and the pairing is recomputed in "
        "their own direction (`docs/adr/0143`)"
    )
    assert theirs["card"]["pairing"]["terms"], "the reasons are on the card"

    # --- somebody answers ---------------------------------------------------
    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(invitee["token"]),
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["standing"] == "ON", (
        "a singles court every seat accepted is on, and the game exists already"
    )

    # --- a game nobody asked for, and a room nobody opened -------------------
    await world.deliver_the_outbox(session_factory)
    game_id = ""
    for token in (sender["token"], invitee["token"]):
        game, card = await _the_card(client, token)
        game_id = game["game_id"]
        assert game["challenge_id"] == challenge_id
        assert game["standing"] == "AWAITING_ENTRY"
        assert card == "planning", "nothing is agreed, so the card asks for a plan"
        (room,) = await _rooms(client, token)
        assert room["challenge_id"] == challenge_id
        assert room["game_id"] == game["game_id"]
        assert {member["player_id"] for member in room["members"]} == {
            str(sender["id"]),
            str(invitee["id"]),
        }

    # --- they arrange it, one slot at a time --------------------------------
    day = local_day(instant(journey_clock.at)) + timedelta(days=2)
    for writer, slot, value, expected in (
        (sender, "place", {"place": "Zabłocie Sport"}, "planning"),
        (invitee, "day", {"day": day.isoformat()}, "planning"),
        (sender, "hour", {"hour": "18:00"}, "game-on"),
    ):
        written = await client.put(
            f"/api/v1/plans/{game_id}/{slot}",
            json=value,
            headers=world.auth(writer["token"]),
        )
        assert written.status_code == 200, written.text
        _, drawn = await _the_card(client, invitee["token"])
        assert drawn == expected, f"the card after {slot} was written"

    (plan,) = await _plans(client, invitee["token"])
    assert plan["game_id"] == game_id
    assert [plan[slot] is not None for slot in SLOTS] == [True, True, True]
    assert plan["agreed_point"] is not None, "the third slot is the agreement"

    # --- they play it -------------------------------------------------------
    stated = await client.post(
        f"/api/v1/games/{game_id}/result",
        json={"score": STRAIGHT_SETS},
        headers=world.auth(sender["token"]),
    )
    assert stated.status_code == 200, stated.text
    assert stated.json()["standing"] == "AWAITING_ANSWER"
    _, card = await _the_card(client, invitee["token"])
    assert card == "confirm", "the other side is asked, and the card says so"

    agreed = await client.post(
        f"/api/v1/games/{game_id}/result/acceptance",
        headers=world.auth(invitee["token"]),
    )
    assert agreed.status_code == 200, agreed.text
    assert agreed.json()["standing"] == "AWAITING_ANSWER", (
        "an acceptance settles nothing inside its grace — a counter still beats it"
    )

    # --- and the grace passes ------------------------------------------------
    before = {
        one["name"]: await _ratings(client, one["token"]) for one in (sender, invitee)
    }
    journey_clock.at = datetime.now(timezone.utc)
    for token in (sender["token"], invitee["token"]):
        game, card = await _the_card(client, token)
        assert game["standing"] == "CONFIRMED"
        assert card == "counted"
        assert game["score"] is not None
    assert (await _games(client, sender["token"]))[1][0]["outcome"] == "WIN"
    assert (await _games(client, invitee["token"]))[1][0]["outcome"] == "LOSS"

    # --- both levels move ----------------------------------------------------
    async with session_factory() as session:
        settled = await build_settle_ratings_on_results(session).execute()
    assert settled.games == 1, settled

    after = {
        one["name"]: await _ratings(client, one["token"]) for one in (sender, invitee)
    }
    tennis = Sport.TENNIS.value
    assert after[sender["name"]][tennis] > before[sender["name"]][tennis], (
        "the winner's Level rose"
    )
    assert after[invitee["name"]][tennis] < before[invitee["name"]][tennis], (
        "the loser's Level fell"
    )


# ---------------------------------------------------------------------------
# The doubles journey: a court nobody finished, finished — and then ended
# ---------------------------------------------------------------------------


async def _a_court(client, token: str, court: list[dict]) -> str:
    found = await world.search(client, token)
    assert found.status_code == 200, found.text
    sent = await client.post(
        "/api/v1/challenges",
        json={"search_id": found.json()["search"]["search_id"], "court": court},
        headers=world.auth(token),
    )
    assert sent.status_code == 201, sent.text
    return sent.json()["challenge_id"]


async def _entries(client, token: str, conversation_id: str) -> list[dict]:
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/entries",
        headers=world.auth(token),
    )
    assert response.status_code == 200, response.text
    return response.json()["entries"]


async def _answer(client, token: str, challenge_id: str, act: str) -> dict:
    response = await client.post(
        f"/api/v1/challenges/{challenge_id}/{act}", headers=world.auth(token)
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_a_half_built_court_is_filled_a_room_grows_and_a_withdraw_ends_it(
    client, session_factory, candidate_source, journey_clock
):
    """**The doubles path, which is a different shape and not a longer one.**

    A padel four sent to one person is half a game: their acceptance produces
    ``LINE_UP_INCOMPLETE`` and — until ``docs/adr/0150`` — the search meant to
    finish the court excluded, by construction, everybody who had accepted it. So
    the fill **names the challenge it completes**, the room grows with each further
    acceptance rather than opening a second one, and the organiser's withdraw is
    the one conclusion the seats cannot reach.

    The last two steps are in this order because the platform requires it: a
    withdraw is legal in ``LINE_UP_INCOMPLETE`` and nowhere else, so a court that
    is awaiting an answer has to stop awaiting one first. The person whose no does
    that is the **reader who has left** — still on the court, still able to read
    it, and drawn no card by it.
    """

    organiser = await world.a_searcher(client)
    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=organiser["mu"] + delta
        )
        people[name] = {"id": player_id, "token": token, "name": name}
    await world.fold_the_log(session_factory, candidate_source)

    # --- half a game --------------------------------------------------------
    challenge_id = await _a_court(
        client,
        organiser["token"],
        [
            {"side": "A", "player_id": str(organiser["id"])},
            {"side": "A", "player_id": str(people["ana"]["id"])},
            {"side": "B"},
            {"side": "B"},
        ],
    )
    accepted = await _answer(client, people["ana"]["token"], challenge_id, "accept")
    assert accepted["standing"] == "LINE_UP_INCOMPLETE", (
        "the acceptance produces it, not the two seats nobody was put in"
    )

    await world.deliver_the_outbox(session_factory)
    (room,) = await _rooms(client, people["ana"]["token"])
    assert room["game_id"] is None, "no line-up has completed, so there is no game"
    assert {member["player_id"] for member in room["members"]} == {
        str(organiser["id"]),
        str(people["ana"]["id"]),
    }
    conversation_id = room["conversation_id"]

    # --- the ⚡ that names the challenge it completes -------------------------
    filling = await world.lineup(
        client, organiser["token"], completing_challenge_id=challenge_id
    )
    assert filling.status_code == 200, filling.text
    lineup = filling.json()["lineup"]
    seated = {seat.get("player_id") for seat in lineup["seats"]}
    assert str(people["ana"]["id"]) in seated, (
        "the person who accepted is on the court this search is completing — "
        "the whole of `docs/adr/0150`"
    )
    assert str(people["ana"]["id"]) not in {
        row["player_id"] for row in filling.json()["search"].get("candidates", [])
    }, "and nobody who answered it is offered again"

    filled = await client.post(
        f"/api/v1/challenges/{challenge_id}/seats",
        json={
            "search_id": filling.json()["search"]["search_id"],
            "court": [
                {
                    "side": seat["side"],
                    "player_id": seat.get("player_id", str(organiser["id"])),
                }
                for seat in lineup["seats"]
            ],
        },
        headers=world.auth(organiser["token"]),
    )
    assert filled.status_code == 200, filled.text
    # **Drained here rather than once at the end**, which is what a worker does
    # and what this assertion needs: the outbox orders by ``(created_at, id)``
    # and SQLite's ``CURRENT_TIMESTAMP`` has one-second granularity, so two rows
    # written a moment apart tie and the tie-break is a minted uuid
    # (``docs/adr/0097``). Two batches are two orders nobody has to guess.
    await world.deliver_the_outbox(session_factory)
    assert filled.json()["standing"] == "AWAITING_ANSWERS", (
        "somebody's answer is owed again, and the standing says so"
    )
    invited = [
        seat["player_id"]
        for seat in filled.json()["seats"]
        if seat["answer"] is None and seat["player_id"] is not None
    ]
    assert invited, "the fill seated somebody"
    fresh = {
        seat["player_id"]: seat["answer_by"]
        for seat in filled.json()["seats"]
        if seat["player_id"] in invited
    }
    assert all(when is not None for when in fresh.values()), (
        "each newly seated player gets their own day, dated from the fill"
    )

    # --- the room grows rather than a second one opening ----------------------
    newcomer = next(one for one in people.values() if str(one["id"]) in invited)
    await _answer(client, newcomer["token"], challenge_id, "accept")
    await world.deliver_the_outbox(session_factory)
    rooms = await _rooms(client, newcomer["token"])
    assert [row["conversation_id"] for row in rooms] == [conversation_id], (
        "one arrangement is one room, however many people accept into it"
    )
    assert str(newcomer["id"]) in {
        member["player_id"] for member in rooms[0]["members"]
    }
    codes = [
        entry["code"]
        for entry in await _entries(client, newcomer["token"], conversation_id)
        if entry["type"] == "system_line"
    ]
    assert codes == ["SEATS_INVITED", "SEAT_ACCEPTED"], (
        "the room carries the story without anybody narrating it — and the "
        "opening acceptance draws no line, because the room is the line"
    )

    # --- somebody leaves, and the court is half built again -------------------
    left = next(
        one
        for one in people.values()
        if str(one["id"]) in invited and one["name"] != newcomer["name"]
    )
    departed = await _answer(client, left["token"], challenge_id, "decline")
    assert departed["standing"] == "LINE_UP_INCOMPLETE", (
        "a decline reopens one seat and disturbs nothing else"
    )
    theirs = await _challenge(client, left["token"], challenge_id)
    assert theirs["standing"] == "LINE_UP_INCOMPLETE"
    assert "card" not in next(
        seat for seat in theirs["seats"] if seat["player_id"] == str(left["id"])
    ), "the reader who has left keeps their row and is drawn no card"
    assert await _rooms(client, left["token"]) == [], (
        "and they are not in the room: membership is the live members"
    )

    # --- and the organiser ends it -------------------------------------------
    ended = await client.post(
        f"/api/v1/challenges/{challenge_id}/withdrawal",
        headers=world.auth(organiser["token"]),
    )
    assert ended.status_code == 200, ended.text
    assert ended.json()["standing"] == "WITHDRAWN"

    await world.deliver_the_outbox(session_factory)
    for one in (organiser, people["ana"], newcomer):
        assert await _rooms(client, one["token"]) == [], (
            "a withdrawal destroys the room in the same act (`docs/adr/0153`)"
        )
        gone = await client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=world.auth(one["token"]),
        )
        assert gone.status_code == 404, gone.text
        assert gone.json()["code"] == "conversation_not_found"
        still_there = await _challenge(client, one["token"], challenge_id)
        assert still_there["standing"] == "WITHDRAWN", (
            "the challenge stays and explains where the room went"
        )
