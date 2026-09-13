"""The four challenge routes, end to end over HTTP.

The whole reachable path in one file: a searcher builds a court with ⚡, sends it,
and the people on it find it and answer. Every assertion lands on the routes,
because what is under test is the product's promise rather than a use case's
signature — and because the court a client posts is the court ⚡ handed it, which
is the only shape the send has to accept.

Four things are asserted here and nowhere else:

**A send is one act.** One request asks everybody, and every invitee gets their
own day from the moment their own seat was invited.

**A refused send leaves nothing.** Not a half-sent challenge, not a row: the list
afterwards is empty, which is the only way whole-send is provable.

**A refusal names nobody.** No player id crosses in the body of one, and the
organiser's remedy is to re-read what they already own.

**Answering is the invitee's own.** They find the challenge on their own list and
answer it with their own token, and the standing moves without anybody being told
anything about anybody else.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_block_query,
    build_challenge_hold_query,
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_open_challenge_query,
    build_planned_game_handover,
    build_origin_search_query,
    build_player_profile_repository,
    build_ruleset,
    build_search_store,
    build_settled_game_query,
    build_user_repository,
)
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)
from app.modules.challenges.application.send_challenge import SendChallenge
from app.modules.challenges.presentation.dependencies import get_send_challenge
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.infrastructure.challenges_mutual_challenge import (
    ChallengesMutualChallenge,
)
from app.modules.matchmaking.presentation.dependencies import (
    InterestLedgerDep,
    get_express_interest,
)
from tests.api import matchmaking_world as world


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    """Three other players, each with a token of their own.

    Signed in rather than folded in alone, because two of the four things this
    file asserts are things only an invitee can do: answer a seat, and block
    somebody.
    """

    people = {}
    for name, delta in (("ana", 0.0), ("bo", 0.05), ("cy", -0.05)):
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _a_court(client, searcher) -> tuple[str, list[dict]]:
    """⚡, and the court it seated — as the client would post it back."""

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
    return body["search"]["search_id"], court


async def _send(client, token: str, search_id: str, court: list[dict]):
    return await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(token),
    )


async def _challenges(client, token: str) -> list[dict]:
    response = await client.get("/api/v1/challenges", headers=world.auth(token))
    assert response.status_code == 200, response.text
    return response.json()["challenges"]


async def test_one_send_asks_everybody_on_the_court(
    client, session_factory, candidate_source, searcher
):
    """**One challenge containing four**, and never four invitations."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)

    sent = await _send(client, searcher["token"], search_id, court)

    assert sent.status_code == 201, sent.text
    challenge_id = sent.json()["challenge_id"]
    for person in people.values():
        theirs = await _challenges(client, person["token"])
        assert [one["challenge_id"] for one in theirs] == [challenge_id]
        assert theirs[0]["standing"] == "AWAITING_ANSWERS"
        assert theirs[0]["organiser_id"] == str(searcher["id"])


async def test_the_organisers_seat_is_accepted_from_birth_and_the_rest_are_not(
    client, session_factory, candidate_source, searcher
):
    """They are the one proposing, so nothing asks whether they want to play the
    game they just built — and that is what makes *every seat accepted* the whole
    of the completion rule."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)

    await _send(client, searcher["token"], search_id, court)

    mine = (await _challenges(client, searcher["token"]))[0]
    seats = {seat["player_id"]: seat for seat in mine["seats"]}
    organiser = seats[str(searcher["id"])]
    assert organiser["answer"] == "ACCEPTED"
    assert organiser.get("answer_by") is None
    invited = [
        seat for seat in mine["seats"] if seat["player_id"] != str(searcher["id"])
    ]
    assert len(invited) == 3
    assert all(seat.get("answer") is None for seat in invited)
    assert all(seat["answer_by"] is not None for seat in invited)


async def test_the_window_and_the_kind_of_evening_come_from_the_search(
    client, session_factory, candidate_source, searcher
):
    """There is no window picker anywhere, and nothing on the request said either."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)

    await _send(client, searcher["token"], search_id, court)

    mine = (await _challenges(client, searcher["token"]))[0]
    assert mine["sport"] == "PADEL"
    assert mine["mode"] == "COMPETITIVE"
    assert mine["window"] in {"TODAY", "TOMORROW", "WEEKEND", "THIS_WEEK", "ANY"}


async def test_an_invitee_accepts_and_it_matters_on_its_own(
    client, session_factory, candidate_source, searcher
):
    """Each acceptance is consequential by itself — there is no waiting room and
    no single moment where the game becomes real."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]

    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(people["ana"]["token"]),
    )

    assert answered.status_code == 200, answered.text
    body = answered.json()
    assert body["standing"] == "AWAITING_ANSWERS", "two people have not answered"
    seats = {seat["player_id"]: seat for seat in body["seats"]}
    assert seats[str(people["ana"]["id"])]["answer"] == "ACCEPTED"


async def test_every_seat_accepted_is_the_whole_of_the_completion_rule(
    client, session_factory, candidate_source, searcher
):
    """No special case for the organiser and none for singles: their seat is
    accepted from birth, so *every seat accepted* is the whole rule."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]

    standing = None
    for person in people.values():
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/accept",
            headers=world.auth(person["token"]),
        )
        assert answered.status_code == 200, answered.text
        standing = answered.json()["standing"]
    assert standing == "ON"


async def test_a_decline_reopens_one_seat_and_kills_nothing(
    client, session_factory, candidate_source, searcher
):
    """*My no is about me.* The people who already agreed did nothing wrong."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]

    refused = await client.post(
        f"/api/v1/challenges/{challenge_id}/decline",
        headers=world.auth(people["ana"]["token"]),
    )

    assert refused.status_code == 200, refused.text
    body = refused.json()
    assert body["standing"] == "AWAITING_ANSWERS"
    seats = {seat["player_id"]: seat for seat in body["seats"]}
    assert seats[str(people["ana"]["id"])]["answer"] == "DECLINED"


async def test_a_seat_is_answered_once(
    client, session_factory, candidate_source, searcher
):
    """**Not idempotent, deliberately**: *yes* after *no* is a different answer
    and not a repeat of one."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]

    await client.post(
        f"/api/v1/challenges/{challenge_id}/decline",
        headers=world.auth(people["ana"]["token"]),
    )
    again = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(people["ana"]["token"]),
    )

    assert again.status_code == 409
    assert again.json()["code"] == "seat_already_answered"


async def test_a_stranger_is_told_the_challenge_does_not_exist(
    client, session_factory, candidate_source, searcher
):
    """One code for two cases, because separating them would answer *is this id
    real* about a stranger's evening."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]
    _, outsider = await world.register(client, "zed")

    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept", headers=world.auth(outsider)
    )

    assert answered.status_code == 404
    assert answered.json()["code"] == "challenge_not_found"


async def test_a_block_taken_since_the_search_refuses_the_whole_send(
    client, session_factory, candidate_source, searcher
):
    """The line-up was built an hour ago and nothing in Play refetches it, so the
    send is where this is caught — and it refuses **whole**, naming nobody."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    blocked = await world.block_between(
        client, people["ana"]["token"], people["bo"]["id"]
    )
    assert blocked.status_code == 204, blocked.text

    sent = await _send(client, searcher["token"], search_id, court)

    assert sent.status_code == 409, sent.text
    body = sent.json()
    assert body["code"] == "line_up_no_longer_sendable"
    assert body.get("details") in (None, {})
    spelled = sent.text
    assert not any(
        str(person["id"]) in spelled for person in people.values()
    ), "a refusal named the withheld seat"
    assert await _challenges(client, searcher["token"]) == []


async def test_a_second_send_to_the_same_people_is_refused(
    client, session_factory, candidate_source, searcher
):
    """One person is asked one thing at a time."""

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    first = await _send(client, searcher["token"], search_id, court)
    assert first.status_code == 201, first.text

    again = await _send(client, searcher["token"], search_id, court)

    assert again.status_code == 409, again.text
    assert again.json()["code"] == "open_challenge_stands"
    assert len(await _challenges(client, searcher["token"])) == 1


async def test_a_held_organiser_is_refused_at_the_entry_point(
    client, session_factory, candidate_source, searcher
):
    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    _hold_everybody(client)

    sent = await _send(client, searcher["token"], search_id, court)

    assert sent.status_code == 403, sent.text
    assert sent.json()["code"] == "account_held"


async def test_a_court_citing_somebody_elses_search_is_refused(
    client, session_factory, candidate_source, searcher
):
    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)

    sent = await _send(client, people["ana"]["token"], search_id, court)

    assert sent.status_code == 409, sent.text
    assert sent.json()["code"] == "court_origin_not_found"


def _hold_everybody(client) -> None:
    """A hold on every account, wired at ``challenges``' own port.

    It is a **second** declaration of the same absent provider, and overriding it
    separately here is the point: a test that reached for the matcher's port
    would pass while the send read a different answer.
    """

    class HoldingEverybody:
        async def held_among(self, player_ids):
            return frozenset(player_ids)

    def factory(
        db: DbSession,
        clock: ClockDep,
        uow: UnitOfWorkDep,
        event_store: DomainEventStoreDep,
        events: EventPublisherDep,
    ) -> SendChallenge:
        return SendChallenge(
            challenges=build_challenge_repository(
                event_store=event_store, events=events
            ),
            open_challenges=build_open_challenge_query(db),
            origins=build_origin_search_query(db),
            safety=CourtSafety(
                blocks=build_block_query(db),
                holds=HoldingEverybody(),
                accounts=build_user_repository(db),
                profiles=build_player_profile_repository(
                    event_store=build_domain_event_store(db),
                    events=build_event_publisher(db),
                ),
            ),
            uow=uow,
            clock=clock,
        )

    world.override(client, get_send_challenge, factory)


# ---------------------------------------------------------------------------
# The challenge two yeses that met open, inline
# ---------------------------------------------------------------------------


async def test_a_mutual_yes_opens_a_game_immediately(
    client, session_factory, candidate_source, searcher
):
    """*That player has left the deck for good, because you now have an open game
    together* — a promise about what somebody will never see again, so it does
    not wait for a worker.

    Both seats are accepted from birth and neither has a deadline: each of them
    has already said yes to the other, and asking either to answer again would
    make the sentence above not yet true.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )

    back = await world.a_yes(
        client, session_factory, candidate_source, sender=other, towards=searcher["id"]
    )

    assert back.json()["mutual"] is True
    mine = await _challenges(client, searcher["token"])
    theirs = await _challenges(client, other["token"])
    assert len(mine) == 1
    # **The tap names the game it opened** (``docs/adr/0154`` §5). The player who
    # closed the loop gets a door to it rather than a sentence about it, and the
    # id is the one both of their inboxes are about.
    assert back.json()["challenge_id"] == mine[0]["challenge_id"]
    assert [one["challenge_id"] for one in mine] == [
        one["challenge_id"] for one in theirs
    ]
    game = mine[0]
    # **A one-to-one padel challenge is half a game.** The pair take the court's
    # first two positions, which leaves a whole side to fill — and the standing
    # says so rather than pretending a four is on.
    assert game["standing"] == "LINE_UP_INCOMPLETE"
    assert game.get("window") is None, "no grid was proposed from"
    assert game.get("mode") is None, "nobody picked a kind of evening"
    seated = [seat for seat in game["seats"] if seat.get("player_id")]
    assert {seat["player_id"] for seat in seated} == {
        str(searcher["id"]),
        str(other["id"]),
    }
    assert all(seat["answer"] == "ACCEPTED" for seat in seated)
    assert all(seat.get("answer_by") is None for seat in seated)


async def test_a_block_between_two_stale_yeses_mints_nothing(
    client, session_factory, candidate_source, searcher
):
    """A *Let's play* may cite a search from a month ago — the record is
    immutable and never expires — so this check is the only thing standing
    between a block and a challenge minted inline with nobody looking.

    **The whole observable is that no challenge exists afterwards.** There is no
    organiser at a screen and no press to refuse: the yes stands and the mutual is
    still a mutual.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )
    # The second player's search runs **before** the block, which is the whole
    # scenario: a search record never expires, so the origin still resolves and
    # the yes is still accepted long after the pool would no longer show them.
    stale = (await world.search(client, other["token"])).json()["search"]["search_id"]
    blocked = await world.block_between(client, other["token"], searcher["id"])
    assert blocked.status_code == 204, blocked.text

    back = await world.express_interest(
        client, other["token"], player_id=searcher["id"], search_id=stale
    )

    assert back.status_code in (200, 201), back.text
    assert back.json()["mutual"] is True, "the yes still landed"
    assert back.json()["challenge_id"] is None, "there is no game to name"
    assert await _challenges(client, other["token"]) == []
    assert await _challenges(client, searcher["token"]) == []


async def test_a_gate_that_cannot_be_read_costs_the_game_and_never_the_yes(
    client, session_factory, candidate_source, searcher
):
    """*A gate that cannot be evaluated excludes* — and on this path excluding
    means minting nothing, never refusing the tap.

    A raise would reach the only other thing in this transaction: somebody's own
    *Let's play*. Losing that to a hiccup in a gate query is strictly worse than
    the pair having a mutual with no game opened, and the next tap tries again.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )
    stale = (await world.search(client, other["token"])).json()["search"]["search_id"]
    _break_the_block_read(client)

    back = await world.express_interest(
        client, other["token"], player_id=searcher["id"], search_id=stale
    )

    assert back.status_code in (200, 201), back.text
    assert back.json()["mutual"] is True, "the yes stands, and it is still mutual"
    assert back.json()["challenge_id"] is None, "there is no game to name"
    listed = (await world.read_interest(client, other["token"])).json()
    assert [row["player_id"] for row in listed["mutual"]] == [str(searcher["id"])]


def _break_the_block_read(client) -> None:
    """A block query that cannot answer, wired where the *mint* reads it.

    The interest route holds two block readers — its own list read and the one
    inside the mint — and only the second is broken here, so the yes goes
    through the path a working platform gives it.
    """

    class Unreadable:
        async def blocked_pairs_among(self, player_ids):
            raise BlockStateUnavailable("the block mask could not be read")

        async def exclusions_for(self, player_id):
            raise BlockStateUnavailable("the block set could not be read")

        async def blocked_between(self, first, second):
            raise BlockStateUnavailable("the pair could not be read")

    def factory(
        db: DbSession,
        clock: ClockDep,
        uow: UnitOfWorkDep,
        interest: InterestLedgerDep,
    ) -> ExpressInterest:
        return ExpressInterest(
            clock=clock,
            ruleset=build_ruleset(),
            interest=interest,
            searches=build_search_store(db),
            challenges=ChallengesMutualChallenge(
                OpenChallengeFromMutualInterest(
                    challenges=build_challenge_repository(
                        event_store=build_domain_event_store(db),
                        events=build_event_publisher(db),
                    ),
                    open_challenges=build_open_challenge_query(db),
                    settled_games=build_settled_game_query(db),
                    safety=CourtSafety(
                        blocks=Unreadable(),
                        holds=build_challenge_hold_query(db),
                        accounts=build_user_repository(db),
                        profiles=build_player_profile_repository(
                            event_store=build_domain_event_store(db),
                            events=build_event_publisher(db),
                        ),
                    ),
                    clock=clock,
                    planned_games=build_planned_game_handover(db),
                )
            ),
            unit_of_work=uow,
        )

    world.override(client, get_express_interest, factory)


# ---------------------------------------------------------------------------
# The withdraw — *Remove the challenge*, while nobody has joined (ADR-0165 §4)
# ---------------------------------------------------------------------------


async def _withdraw(client, token: str, challenge_id: str):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/withdrawal", headers=world.auth(token)
    )


async def _a_court_nobody_has_answered(
    client, session_factory, candidate_source, searcher
) -> tuple[str, dict]:
    """A padel four just sent: three people deciding, nobody in but the
    organiser. `AWAITING_ANSWERS`, and the state ``docs/adr/0142`` §2 refused
    the withdraw in — reversed by ``docs/adr/0165`` §4."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]
    return challenge_id, people


async def _a_court_nobody_will_finish(
    client, session_factory, candidate_source, searcher
) -> tuple[str, dict]:
    """A padel four with one acceptance on it and nobody left deciding.

    One yes and two noes leaves the organiser and the acceptor in, two seats
    open and nothing awaiting — `LINE_UP_INCOMPLETE`, reached through the routes
    alone. It is the state the withdraw was written for, and the state it is
    now refused in: somebody has joined, and the court is as much theirs.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]
    for name, act in (("ana", "accept"), ("bo", "decline"), ("cy", "decline")):
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/{act}",
            headers=world.auth(people[name]["token"]),
        )
        assert answered.status_code == 200, answered.text
    assert answered.json()["standing"] == "LINE_UP_INCOMPLETE"
    return challenge_id, people


async def test_the_organiser_removes_a_challenge_nobody_has_answered(
    client, session_factory, candidate_source, searcher
):
    """**The Phase 1 withdraw, admitted.** The reply is the redraw, at
    `WITHDRAWN`, with every seat exactly as it was — three questions still on
    the court with their deadlines — and the invitees are told the same: the
    row reads `WITHDRAWN`, the detail draws no card, and a yes or a no meets
    `challenge_is_over` rather than opening a room for a court that is over."""

    challenge_id, people = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    not_theirs = await _withdraw(client, people["cy"]["token"], challenge_id)
    assert not_theirs.status_code == 403, not_theirs.text
    assert not_theirs.json()["code"] == "withdraw_is_the_organisers"

    withdrawn = await _withdraw(client, searcher["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    body = withdrawn.json()
    assert body["standing"] == "WITHDRAWN"
    assert body["ended_at"] is not None
    invited = [
        seat for seat in body["seats"] if seat["player_id"] != str(searcher["id"])
    ]
    assert [seat["answer"] for seat in invited] == [None, None, None]
    assert all(seat["answer_by"] is not None for seat in invited)

    for name, act in (("ana", "accept"), ("bo", "decline")):
        (row,) = await _challenges(client, people[name]["token"])
        assert row["standing"] == "WITHDRAWN"
        detail = await client.get(
            f"/api/v1/challenges/{challenge_id}",
            headers=world.auth(people[name]["token"]),
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["standing"] == "WITHDRAWN"
        assert all("card" not in seat for seat in detail.json()["seats"])
        assert "pairing_absence" not in detail.json()
        refused = await client.post(
            f"/api/v1/challenges/{challenge_id}/{act}",
            headers=world.auth(people[name]["token"]),
        )
        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "challenge_is_over"


async def test_a_court_somebody_has_joined_is_nobodys_to_remove_for_the_others(
    client, session_factory, candidate_source, searcher
):
    """``docs/adr/0165`` §4 — B accepts and the organiser's removal is refused
    with a named code; B leaves while C and D are still deciding and the
    organiser is alone again, so it is admitted again. The room B's yes opened
    is destroyed in the act, though B had already left it."""

    challenge_id, people = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    accepted = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(people["ana"]["token"]),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["standing"] == "AWAITING_ANSWERS"
    await world.deliver_the_outbox(session_factory)
    rooms = await client.get(
        "/api/v1/conversations", headers=world.auth(searcher["token"])
    )
    assert len(rooms.json()["conversations"]) == 1, rooms.text

    refused = await _withdraw(client, searcher["token"], challenge_id)
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "somebody_has_joined"
    assert str(people["ana"]["id"]) not in refused.text, "the refusal names nobody"

    left = await client.post(
        f"/api/v1/challenges/{challenge_id}/departure",
        headers=world.auth(people["ana"]["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "AWAITING_ANSWERS", "C and D are still deciding"

    withdrawn = await _withdraw(client, searcher["token"], challenge_id)

    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["standing"] == "WITHDRAWN"
    seats = {seat["player_id"]: seat for seat in withdrawn.json()["seats"]}
    assert seats[str(people["ana"]["id"])]["answer"] == "LEFT"
    assert seats[str(people["bo"]["id"])]["answer"] is None
    await world.deliver_the_outbox(session_factory)
    rooms = await client.get(
        "/api/v1/conversations", headers=world.auth(searcher["token"])
    )
    assert rooms.json()["conversations"] == []


async def test_a_withdrawn_challenge_keeps_its_row_and_says_what_it_is(
    client, session_factory, candidate_source, searcher
):
    """A list that quietly dropped this morning's is a list that lies — and the
    person who was asked has to be able to find out the court is closed."""

    challenge_id, people = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    await _withdraw(client, searcher["token"], challenge_id)

    hers = await _challenges(client, people["ana"]["token"])

    assert [row["standing"] for row in hers] == ["WITHDRAWN"]


async def test_an_invitee_is_told_the_withdraw_is_the_organisers(
    client, session_factory, candidate_source, searcher
):
    """**403 and not 404**: they hold a seat on this court and can already see
    it, so pretending it is not there would be the wrong refusal. Somebody who
    joined and somebody who said no are told the same — and told it before
    anything about the court is read, so the one who joined never hears
    `somebody_has_joined`. Somebody still deciding is told it in the removal
    test above."""

    challenge_id, people = await _a_court_nobody_will_finish(
        client, session_factory, candidate_source, searcher
    )

    for name in ("ana", "bo"):
        refused = await _withdraw(client, people[name]["token"], challenge_id)
        assert refused.status_code == 403, refused.text
        assert refused.json()["code"] == "withdraw_is_the_organisers"


async def test_a_court_that_ended_by_itself_has_no_withdraw(
    client, session_factory, candidate_source, searcher
):
    """One yes, two noes, and the yes taken back: the organiser is alone with
    nobody deciding, and the court is over as `DECLINED` — by itself, a
    departure being a no. The withdraw meets the word every act uses for an
    ended challenge, and never a word about who has joined."""

    challenge_id, people = await _a_court_nobody_will_finish(
        client, session_factory, candidate_source, searcher
    )
    left = await client.post(
        f"/api/v1/challenges/{challenge_id}/departure",
        headers=world.auth(people["ana"]["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "DECLINED"

    refused = await _withdraw(client, searcher["token"], challenge_id)

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "challenge_is_over"


async def test_a_withdrawal_does_not_come_back(
    client, session_factory, candidate_source, searcher
):
    """Irreversible: re-asking the same people is a **new** challenge, and a
    second press is refused as an ended challenge refuses everything."""

    challenge_id, _ = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    assert (await _withdraw(client, searcher["token"], challenge_id)).status_code == 200

    again = await _withdraw(client, searcher["token"], challenge_id)

    assert again.status_code == 409
    assert again.json()["code"] == "challenge_is_over"


async def test_a_stranger_cannot_withdraw_and_is_told_nothing_exists(
    client, session_factory, candidate_source, searcher
):
    """One code for two cases, exactly as the answers refuse: separating them
    would answer *is this id real* about a stranger's evening."""

    challenge_id, _ = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    _, outsider = await world.register(client, "zed")

    refused = await _withdraw(client, outsider, challenge_id)

    assert refused.status_code == 404
    assert refused.json()["code"] == "challenge_not_found"


# ---------------------------------------------------------------------------
# When it ended — what a shelf life is subtracted from
# ---------------------------------------------------------------------------


async def test_a_row_that_still_stands_says_so_by_saying_nothing(
    client, session_factory, candidate_source, searcher
):
    """``ended_at`` is ``null`` on the three standings that are not endings, and
    it is **in** the row.

    Every nullable field on this list is a measured nothing rather than an
    absence, so a client reads one key and never two — *this challenge has not
    ended* is the answer, not the lack of one.
    """

    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    await _send(client, searcher["token"], search_id, court)

    (row,) = await _challenges(client, searcher["token"])

    assert row["standing"] == "AWAITING_ANSWERS"
    assert "ended_at" in row
    assert row["ended_at"] is None


async def test_an_ended_row_carries_the_instant_its_shelf_life_is_measured_from(
    client, session_factory, candidate_source, searcher
):
    """*An ended challenge keeps its row, in place, and it leaves 24 h after the
    challenge ended* (`the-loop-screens.md` §1.1) — one subtraction,
    ``read_at − ended_at``, and until #388 the field it subtracts did not exist.

    **A withdrawal is dated by the act and not by a deadline.** The client used
    to derive an ending from the latest ``answer_by`` on the court, which for a
    withdrawal says nothing at all — so such a row was kept indefinitely. Every
    deadline here is still two days out, and the instant served is neither of
    them.
    """

    challenge_id, people = await _a_court_nobody_has_answered(
        client, session_factory, candidate_source, searcher
    )
    assert (await _withdraw(client, searcher["token"], challenge_id)).status_code == 200

    response = await client.get(
        "/api/v1/challenges", headers=world.auth(people["ana"]["token"])
    )
    body = response.json()
    (row,) = body["challenges"]

    assert row["standing"] == "WITHDRAWN"
    ended = datetime.fromisoformat(row["ended_at"])
    assert datetime.fromisoformat(row["opened_at"]) <= ended
    assert ended <= datetime.fromisoformat(body["read_at"])
    deadlines = [seat["answer_by"] for seat in row["seats"] if seat["answer_by"]]
    assert deadlines
    assert all(ended < datetime.fromisoformat(one) for one in deadlines)


async def test_a_court_everybody_turned_down_is_dated_by_the_seats(
    client, session_factory, candidate_source, searcher
):
    """The other way an ending arrives at this route: not an act on the challenge
    but the last person asked leaving it.

    A decline is the one departure the wire cannot date exactly, and the bound is
    the tighter of that seat's own deadline and the last thing that happened here.
    **This route cannot pin which**, because it has no clock to move; what it can
    show is that the answer is neither of the two instants the client used to have
    to guess from — it is inside the request rather than two days out at a
    deadline. The arithmetic is pinned in ``tests/unit/test_challenge_aggregate.py``.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id, court = await _a_court(client, searcher)
    challenge_id = (
        await _send(client, searcher["token"], search_id, court)
    ).json()["challenge_id"]
    for name in ("ana", "bo", "cy"):
        refused = await client.post(
            f"/api/v1/challenges/{challenge_id}/decline",
            headers=world.auth(people[name]["token"]),
        )
        assert refused.status_code == 200, refused.text

    response = await client.get(
        "/api/v1/challenges", headers=world.auth(searcher["token"])
    )
    body = response.json()
    (row,) = body["challenges"]

    assert row["standing"] == "DECLINED"
    ended = datetime.fromisoformat(row["ended_at"])
    assert datetime.fromisoformat(row["opened_at"]) <= ended
    assert ended <= datetime.fromisoformat(body["read_at"])
    deadlines = [seat["answer_by"] for seat in row["seats"] if seat["answer_by"]]
    assert deadlines
    assert all(ended < datetime.fromisoformat(one) for one in deadlines)


async def test_a_refused_mint_and_an_innocent_one_name_the_same_nothing(
    client, session_factory, candidate_source, searcher
):
    """**The fold is the safety property** (``docs/adr/0154`` §3).

    A pair already arranging a game and a pair a gate refused reach the wire as
    the same ``challenge_id: null``. That is not a coincidence to be tidied up
    later: if absence ever meant *a gate refused about one of you* and nothing
    else, it would be the trace ``docs/adr/0095`` guarantees a block never leaves
    anywhere in any response, and the field would have to go.

    Here the innocent cause is this mutual's **own** half-built court. A padel
    mutual is `LINE_UP_INCOMPLETE` with a side still to fill, so the pair rule
    holds the second tap — over a court these two made themselves — and the
    answer is still nothing, because a half-built court is not a game they have
    but one they are still making.
    """

    other = await world.a_searcher(client, name="bea")
    await world.fold_the_log(session_factory, candidate_source)
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )
    # **One search, cited twice.** It has to be taken before the mutual: once
    # these two are arranging a court they leave each other's deck, so a search
    # run afterwards would not show them and the origin could not resolve. A
    # search record never expires, which is what makes the second tap reachable
    # at all — and is the same property the stale-block test turns on.
    origin = (await world.search(client, other["token"])).json()["search"]["search_id"]

    opened = await world.express_interest(
        client, other["token"], player_id=searcher["id"], search_id=origin
    )
    assert opened.json()["challenge_id"] is not None

    again = await world.express_interest(
        client, other["token"], player_id=searcher["id"], search_id=origin
    )

    assert again.status_code in (200, 201), again.text
    assert again.json()["mutual"] is True, "the mutual is still what the rows say"
    assert again.json()["challenge_id"] is None
    assert len(await _challenges(client, other["token"])) == 1, "no second court"
