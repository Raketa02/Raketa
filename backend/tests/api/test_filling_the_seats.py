"""Completing a half-built court — the fill, the gate that steps aside, the send.

The whole of ``docs/adr/0150`` over HTTP: a member of a court with open seats
searches for the people to finish it, and the players who already accepted stop
being invisible to that very search.

**The first test is the bug.** ⚡ with the accepted player locked is
``locked_seat_not_available``, every time, and it cannot be worked around from a
client — which is why the fix is a field on the request rather than something a
builder could have assembled out of what already existed.

What the rest assert is what the record decided: the fill **names** the challenge
and says nothing else about the court, the gate steps aside for that one
challenge and for **nothing else**, everybody who already answered it is out of
its own pool, the mode is inherited or resolved and the window is never
re-stamped, **any live member may fill and only the organiser may withdraw**, and
the send that follows is not refused for the pairs it is made of.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.api import matchmaking_world as world

#: One more than a padel four needs twice over, so that seats can be spent on
#: declines and second challenges and there is still a pool to fill from.
A_CITY = (("ana", 0.0), ("bo", 0.05), ("cy", -0.05), ("dee", 0.10), ("eve", -0.10))


@pytest.fixture
async def searcher(client):
    return await world.a_searcher(client)


async def _a_city(client, session_factory, candidate_source, mu: float) -> dict:
    """Five other players, each with a token of their own.

    Signed in rather than folded in alone, because most of what this file
    asserts is something only a person on the court can do: accept a seat,
    decline one, or press ⚡ on a court somebody else organised.
    """

    people = {}
    for name, delta in A_CITY:
        player_id, token = await world.a_signed_in_candidate(
            client, session_factory, name, mu=mu + delta
        )
        people[name] = {"id": player_id, "token": token}
    await world.fold_the_log(session_factory, candidate_source)
    return people


async def _search_id(client, token: str) -> str:
    found = await world.search(client, token)
    assert found.status_code == 200, found.text
    return found.json()["search"]["search_id"]


async def _send(client, token: str, search_id: str, court: list[dict]):
    return await client.post(
        "/api/v1/challenges",
        json={"search_id": search_id, "court": court},
        headers=world.auth(token),
    )


async def _fill(client, token: str, challenge_id: str, search_id: str, court):
    return await client.post(
        f"/api/v1/challenges/{challenge_id}/seats",
        json={"search_id": search_id, "court": court},
        headers=world.auth(token),
    )


def _court_of(lineup: dict, searcher_id) -> list[dict]:
    """The court ⚡ handed back, as the client posts it: a side and an occupant."""

    return [
        {
            "side": seat["side"],
            "player_id": seat.get("player_id", str(searcher_id)),
        }
        for seat in lineup["seats"]
    ]


async def _a_half_built_court(client, searcher, other):
    """A padel four sent to one person, who accepts. **Two seats still open.**

    Nobody is deciding — the two empty seats were never offered to anybody — so
    the acceptance is what produces ``LINE_UP_INCOMPLETE`` rather than the empty
    seats it was sent with.
    """

    search_id = await _search_id(client, searcher["token"])
    court = [
        {"side": "A", "player_id": str(searcher["id"])},
        {"side": "A", "player_id": str(other["id"])},
        {"side": "B"},
        {"side": "B"},
    ]
    sent = await _send(client, searcher["token"], search_id, court)
    assert sent.status_code == 201, sent.text
    challenge_id = sent.json()["challenge_id"]
    answered = await client.post(
        f"/api/v1/challenges/{challenge_id}/accept",
        headers=world.auth(other["token"]),
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["standing"] == "LINE_UP_INCOMPLETE"
    return challenge_id


def _seated(lineup: dict) -> set[str]:
    return {
        seat["player_id"] for seat in lineup["seats"] if seat.get("player_id")
    }


# ---------------------------------------------------------------------------
# The bug, and the field that fixes it
# ---------------------------------------------------------------------------


async def test_hand_seating_the_player_who_accepted_your_court_is_refused(
    client, session_factory, candidate_source, searcher
):
    """**The state of the world before this ticket, asserted so it stays fixed.**

    A locked seat resolves out of this search's own pool or not at all, the
    open-challenge gate excludes everybody the searcher is arranging with, and a
    half-built line-up holds its pairs for the whole of ``LINE_UP_INCOMPLETE``.
    So the person who accepted your court is, by construction, absent from the
    pool of any ordinary ⚡ — and locking them is refused.

    This is not a thing the fill made worse: it is what makes
    ``completing_challenge_id`` a field rather than something a client could have
    assembled out of the routes that already existed.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    await _a_half_built_court(client, searcher, people["ana"])

    refused = await world.lineup(
        client, searcher["token"], locked_seats=[people["ana"]["id"]]
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "locked_seat_not_available"


async def test_the_fill_names_the_challenge_and_the_court_comes_back_whole(
    client, session_factory, candidate_source, searcher
):
    """The same ⚡, naming the challenge, seats the people already on the court.

    They come back as **ordinary candidate rows** — which is why the builder can
    draw them at all — and the envelope says the engine is optimising for the
    group, because the searcher may end up with a worse individual match than an
    empty court would have given them.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    assert filled.status_code == 200, filled.text
    body = filled.json()
    assert str(people["ana"]["id"]) in _seated(body["lineup"])
    assert body["search"]["optimised_for"] == "GROUP"
    assert body["search"]["surface"] == "FILL_SEATS"
    assert all(
        "unfilled_reason" not in seat for seat in body["lineup"]["seats"]
    ), "a five-person city fills a padel four around one locked seat"


@pytest.mark.parametrize(
    "extra",
    [
        pytest.param({"sport": "PADEL"}, id="sport"),
        pytest.param({"mode": "COMPETITIVE"}, id="mode"),
        pytest.param({"locked_seats": [str(uuid4())]}, id="locked_seats"),
    ],
)
async def test_a_fill_says_nothing_else_about_the_court(
    client, session_factory, candidate_source, searcher, extra
):
    """Refused **beside** the challenge id rather than made optional.

    A caller supplying one of the three is offering a second place for a fact the
    challenge already holds — which is how somebody who is not in the challenge
    gets locked, or somebody who is gets forgotten.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])

    refused = await client.post(
        "/api/v1/lineups",
        json={"completing_challenge_id": challenge_id, **extra},
        headers=world.auth(searcher["token"]),
    )

    assert refused.status_code == 422, refused.text


async def test_a_line_up_that_names_no_challenge_still_owes_its_sport_and_mode(
    client, searcher
):
    """The three are refused beside a challenge and **required without one**."""

    refused = await client.post(
        "/api/v1/lineups", json={}, headers=world.auth(searcher["token"])
    )

    assert refused.status_code == 422, refused.text


# ---------------------------------------------------------------------------
# The gate steps aside for one challenge and for nothing else
# ---------------------------------------------------------------------------


async def test_every_other_open_challenge_still_keeps_its_people_out_of_the_pool(
    client, session_factory, candidate_source, searcher
):
    """*One thing at a time* is not weakened; it is read correctly.

    The searcher is arranging two games. Filling the first sees the people on
    **that** court and nobody from the second — which is the same rule, not an
    exception to it.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])
    elsewhere = await _search_id(client, searcher["token"])
    second = await _send(
        client,
        searcher["token"],
        elsewhere,
        [
            {"side": "A", "player_id": str(searcher["id"])},
            {"side": "A", "player_id": str(people["dee"]["id"])},
            {"side": "B"},
            {"side": "B"},
        ],
    )
    assert second.status_code == 201, second.text

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    assert filled.status_code == 200, filled.text
    seated = _seated(filled.json()["lineup"])
    assert str(people["ana"]["id"]) in seated, "the court being completed is seen"
    assert str(people["dee"]["id"]) not in seated, "the other one is not"


async def test_nobody_who_answered_this_challenge_is_a_candidate_for_its_own_fill(
    client, session_factory, candidate_source, searcher
):
    """A decline reopens a seat and releases the pair — so without this the
    person who turned your court down is back in the pool that fills it, and
    ``NobodyIsAskedTwice`` refuses the send **after** the player chose them.

    The aggregate's rule stays exactly where it is, as the backstop; it stops
    being a screen anybody reaches.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id = await _search_id(client, searcher["token"])
    sent = await _send(
        client,
        searcher["token"],
        search_id,
        [
            {"side": "A", "player_id": str(searcher["id"])},
            {"side": "A", "player_id": str(people["ana"]["id"])},
            {"side": "B", "player_id": str(people["bo"]["id"])},
            {"side": "B"},
        ],
    )
    challenge_id = sent.json()["challenge_id"]
    for name, act in (("ana", "accept"), ("bo", "decline")):
        answered = await client.post(
            f"/api/v1/challenges/{challenge_id}/{act}",
            headers=world.auth(people[name]["token"]),
        )
        assert answered.status_code == 200, answered.text

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    assert filled.status_code == 200, filled.text
    seated = _seated(filled.json()["lineup"])
    assert str(people["ana"]["id"]) in seated
    assert str(people["bo"]["id"]) not in seated, "they answered this challenge"


# ---------------------------------------------------------------------------
# Whose act it is
# ---------------------------------------------------------------------------


async def test_any_live_member_may_fill_and_a_member_may_not_withdraw(
    client, session_factory, candidate_source, searcher
):
    """Growing a court and ending one are different acts with different
    permissions (``docs/adr/0150`` §1): the fill is every live member's, and
    removing a court that was never a game is the organiser's alone — and
    nobody's once somebody has joined (``docs/adr/0165`` §4), so the member
    who filled it is told the act is not theirs."""

    # **A full searcher rather than a folded-in candidate**, because this is the
    # one test where somebody who is not the organiser runs a search of their
    # own — and a candidate the index knows carries no declaration for a search
    # to be scored against.
    them = await world.a_searcher(client, name="zoe")
    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, them)

    filled = await world.lineup(
        client, them["token"], completing_challenge_id=challenge_id
    )
    ended = await client.post(
        f"/api/v1/challenges/{challenge_id}/withdrawal",
        headers=world.auth(them["token"]),
    )

    assert filled.status_code == 200, filled.text
    assert str(searcher["id"]) in _seated(filled.json()["lineup"])
    assert ended.status_code == 403, ended.text
    assert ended.json()["code"] == "withdraw_is_the_organisers"


async def test_somebody_who_has_left_the_court_may_not_grow_it(
    client, session_factory, candidate_source, searcher
):
    """A declined invitee still holds a seat and still sees the challenge, so the
    refusal is a `403` rather than a `404` — and it is the fill they are refused,
    not the challenge."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    search_id = await _search_id(client, searcher["token"])
    sent = await _send(
        client,
        searcher["token"],
        search_id,
        [
            {"side": "A", "player_id": str(searcher["id"])},
            {"side": "A", "player_id": str(people["ana"]["id"])},
            {"side": "B", "player_id": str(people["bo"]["id"])},
            {"side": "B"},
        ],
    )
    challenge_id = sent.json()["challenge_id"]
    for name, act in (("ana", "accept"), ("bo", "decline")):
        await client.post(
            f"/api/v1/challenges/{challenge_id}/{act}",
            headers=world.auth(people[name]["token"]),
        )

    refused = await _fill(
        client, people["bo"]["token"], challenge_id, search_id, []
    )

    assert refused.status_code == 403, refused.text
    assert refused.json()["code"] == "fill_is_the_live_members"


async def test_a_challenge_that_is_not_yours_to_fill_is_one_code_for_three_cases(
    client, session_factory, candidate_source, searcher
):
    """No such challenge, no seat of yours on it, nobody arranging it any more —
    and telling them apart would answer *is this id real* about a stranger's
    evening."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])

    invented = await world.lineup(
        client, searcher["token"], completing_challenge_id=uuid4()
    )
    a_strangers = await world.lineup(
        client, people["dee"]["token"], completing_challenge_id=challenge_id
    )
    # The one who joined leaves: the organiser is alone with nobody deciding,
    # and the court is over by itself (``docs/adr/0165`` §3).
    left = await client.post(
        f"/api/v1/challenges/{challenge_id}/departure",
        headers=world.auth(people["ana"]["token"]),
    )
    assert left.status_code == 200, left.text
    assert left.json()["standing"] == "DECLINED"
    ended = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    for refused in (invented, a_strangers, ended):
        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "challenge_not_yours_to_fill"


# ---------------------------------------------------------------------------
# The mode, and the window that is never re-stamped
# ---------------------------------------------------------------------------


async def test_a_challenge_born_with_a_mode_keeps_it(
    client, session_factory, candidate_source, searcher
):
    """A competitive court must not have its last seat filled by a for-fun
    search, and no picker was drawn to ask."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )

    assert filled.status_code == 200, filled.text
    assert filled.json()["search"]["mode"] == "COMPETITIVE"


async def test_a_mutual_born_court_resolves_a_mode_and_is_never_given_a_window(
    client, session_factory, candidate_source, searcher
):
    """The commonest half-built court has no mode, no window and no organiser who
    proposed anything.

    Its mode is resolved from the **filler's** own declared Play intent on the
    deck's own rule — *no preference* inherits *for fun*, and never a third
    vector — and the window stays ``null`` for the challenge's whole life,
    through the fill and after it.
    """

    other = await world.a_searcher(client, name="bea", intent="NO_PREFERENCE")
    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )
    back = await world.a_yes(
        client, session_factory, candidate_source, sender=other, towards=searcher["id"]
    )
    assert back.json()["mutual"] is True
    mine = await client.get(
        "/api/v1/challenges", headers=world.auth(other["token"])
    )
    court = mine.json()["challenges"][0]
    assert court["standing"] == "LINE_UP_INCOMPLETE"
    assert court["mode"] is None and court["window"] is None

    filled = await world.lineup(
        client, other["token"], completing_challenge_id=court["challenge_id"]
    )

    assert filled.status_code == 200, filled.text
    assert filled.json()["search"]["mode"] == "FOR_FUN", "NO_PREFERENCE inherits fun"
    after = await client.get(
        "/api/v1/challenges", headers=world.auth(other["token"])
    )
    assert after.json()["challenges"][0]["window"] is None


# ---------------------------------------------------------------------------
# The send that follows
# ---------------------------------------------------------------------------


async def test_the_seats_route_grows_the_court_without_disturbing_who_is_in(
    client, session_factory, candidate_source, searcher
):
    """One press: the open seats filled, the acceptance untouched, and **each new
    seat on its own clock**.

    It is also the assertion that the pair rule does not refuse a court for the
    pairs it is made of: the organiser and the acceptor are an open pair, and the
    send would be refused for them without the exception.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])
    before = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(searcher["token"])
    )
    theirs = {
        seat["player_id"]: seat for seat in before.json()["seats"]
    }[str(people["ana"]["id"])]
    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    body = filled.json()

    grown = await _fill(
        client,
        searcher["token"],
        challenge_id,
        body["search"]["search_id"],
        _court_of(body["lineup"], searcher["id"]),
    )

    assert grown.status_code == 200, grown.text
    court = grown.json()
    assert court["standing"] == "AWAITING_ANSWERS"
    seats = {seat["player_id"]: seat for seat in court["seats"]}
    assert seats[str(searcher["id"])]["answer"] == "ACCEPTED"
    assert seats[str(searcher["id"])]["answer_by"] is None
    kept = seats[str(people["ana"]["id"])]
    assert kept["answer"] == "ACCEPTED", "an acceptance is to the game"
    assert kept["answer_by"] == theirs["answer_by"], "nobody's deadline moved"
    newly = [
        seat
        for player_id, seat in seats.items()
        if player_id not in {str(searcher["id"]), str(people["ana"]["id"])}
    ]
    assert len(newly) == 2
    assert all(seat["answer"] is None for seat in newly)
    assert all(seat["answer_by"] is not None for seat in newly)
    assert all(seat["answer_by"] >= theirs["answer_by"] for seat in newly)


async def test_the_mutual_born_four_is_completed_by_the_member_who_is_not_organiser(
    client, session_factory, candidate_source, searcher
):
    """**The case ADR-0150 §1 was decided on, filled end to end.**

    Two yeses meet, and a padel court opens with both of them on **side A** —
    `LINE_UP_INCOMPLETE` from birth, no mode, no window, and an "organiser" who
    is only whoever said yes second. The other one presses ⚡ and sends, and both
    of the original seats keep their acceptance while the arrangement is free to
    move them across the net: *an acceptance is to the game, not to the side.*

    Without this the deciding case is exercised only as far as the search, and
    the half of it that runs through `Challenge.invite` — where `_still_in` keeps
    an answered seat and re-sides it — is never reached at all.
    """

    other = await world.a_searcher(client, name="bea")
    await _a_city(client, session_factory, candidate_source, searcher["mu"])
    await world.a_yes(
        client, session_factory, candidate_source, sender=searcher, towards=other["id"]
    )
    # **The second yes mints, and its sender holds seat one** — so `other` is the
    # organiser, in the only sense the aggregate means it, and `searcher` is the
    # member who would otherwise be able to neither complete this court nor leave
    # it. The fill below is therefore pressed by `searcher`.
    back = await world.a_yes(
        client, session_factory, candidate_source, sender=other, towards=searcher["id"]
    )
    assert back.json()["mutual"] is True
    court = (
        await client.get("/api/v1/challenges", headers=world.auth(other["token"]))
    ).json()["challenges"][0]
    challenge_id = court["challenge_id"]
    assert court["organiser_id"] == str(other["id"])
    assert [seat["side"] for seat in court["seats"]] == ["A", "A", "B", "B"]
    assert {
        seat["player_id"] for seat in court["seats"] if seat["player_id"]
    } == {str(searcher["id"]), str(other["id"])}, "both of them on side A"

    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    assert filled.status_code == 200, filled.text
    body = filled.json()
    grown = await _fill(
        client,
        searcher["token"],
        challenge_id,
        body["search"]["search_id"],
        _court_of(body["lineup"], searcher["id"]),
    )

    assert grown.status_code == 200, grown.text
    seats = {
        seat["player_id"]: seat
        for seat in grown.json()["seats"]
        if seat["player_id"]
    }
    assert seats[str(searcher["id"])]["answer"] == "ACCEPTED"
    assert seats[str(other["id"])]["answer"] == "ACCEPTED"
    assert seats[str(searcher["id"])]["answer_by"] is None, "no deadline was minted"
    assert seats[str(other["id"])]["answer_by"] is None
    newly = [
        seat
        for player_id, seat in seats.items()
        if player_id not in {str(searcher["id"]), str(other["id"])}
    ]
    assert len(newly) == 2
    assert all(seat["answer"] is None for seat in newly)
    assert all(seat["answer_by"] is not None for seat in newly)


async def test_the_fill_never_takes_somebody_out_of_a_court_they_are_in(
    client, session_factory, candidate_source, searcher
):
    """The people who already agreed did nothing wrong, and a court that dropped
    one of them is refused rather than silently accepted."""

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])
    search_id = await _search_id(client, searcher["token"])

    refused = await _fill(
        client,
        searcher["token"],
        challenge_id,
        search_id,
        [
            {"side": "A", "player_id": str(searcher["id"])},
            {"side": "A", "player_id": str(people["bo"]["id"])},
            {"side": "B", "player_id": str(people["cy"]["id"])},
            {"side": "B", "player_id": str(people["dee"]["id"])},
        ],
    )

    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "accepted_player_may_not_be_removed"


# ---------------------------------------------------------------------------
# The pool over a fill has somebody to offer
# ---------------------------------------------------------------------------


async def test_the_pool_over_a_fill_has_somebody_to_offer(
    client, session_factory, candidate_source, searcher
):
    """[#407](https://github.com/Raketa02/Raketa/issues/407): a line-up answer
    used to return exactly the people it seated, so the pool over a fill court —
    which this journey mints no shortlist for — offered the one person just
    taken off a seat, or nobody.

    A city of five, one accepted, ⚡ seats two more: the two it did **not** seat
    are still rows on the fill's own record. So the pool over this court can
    offer another seat, a forecast citing the fill can price the swap, and the
    send can seat the pick — all three against the one search the court is
    bound to.
    """

    people = await _a_city(client, session_factory, candidate_source, searcher["mu"])
    challenge_id = await _a_half_built_court(client, searcher, people["ana"])
    filled = await world.lineup(
        client, searcher["token"], completing_challenge_id=challenge_id
    )
    body = filled.json()
    search_id = body["search"]["search_id"]
    accepted = str(people["ana"]["id"])
    seated = _seated(body["lineup"])
    pool = [row["player_id"] for row in body["candidates"]]

    assert accepted in pool, "the accepted seat is not an ordinary row"
    offered = [player_id for player_id in pool if player_id not in seated]
    assert offered, "the fill's record offers nobody it did not seat"
    by_the_engine = sorted(seated - {accepted, str(searcher["id"])})
    assert len(by_the_engine) == 2

    priced = await world.forecast(
        client,
        searcher["token"],
        search_id=search_id,
        players=[accepted, offered[0], by_the_engine[0]],
    )
    assert priced.status_code == 200, priced.text

    grown = await _fill(
        client,
        searcher["token"],
        challenge_id,
        search_id,
        [
            {"side": "A", "player_id": str(searcher["id"])},
            {"side": "A", "player_id": accepted},
            {"side": "B", "player_id": offered[0]},
            {"side": "B", "player_id": by_the_engine[0]},
        ],
    )
    assert grown.status_code == 200, grown.text
    seats = {seat["player_id"] for seat in grown.json()["seats"]}
    assert offered[0] in seats, "the pick off the pool did not reach the court"
