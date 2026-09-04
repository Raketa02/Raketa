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
    build_planned_game_opening,
    build_origin_search_query,
    build_player_profile_repository,
    build_ruleset,
    build_search_store,
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
                    planned_games=build_planned_game_opening(db),
                )
            ),
            unit_of_work=uow,
        )

    world.override(client, get_express_interest, factory)
