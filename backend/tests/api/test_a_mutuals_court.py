"""A mutual's court, end to end over HTTP (``docs/adr/0169`` §8).

Two yeses meet, and one thing follows that no other route decides.

**A mutual's game is counted unless either declared *for fun*.** The deck reads
no declaration and moves nobody for one; the game a mutual opens honours a wish
somebody stated for the sport. One *for fun* among the pair opens a friendly;
two competitive declarers, or one competitive and one who never declared, open a
counted game — *a friendly is a thing people choose*.

Driven through the interest route so the declarations are the ones ADR-0094's
own route wrote and the mint is the one ``express_interest`` calls inline.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport
from tests.api import matchmaking_world as world


async def _a_player(client, name: str, *, sport: Sport, intent: str | None) -> dict:
    """One player rated in ``sport``, declared — or, with ``None``, not."""

    player_id, token = await world.register(client, name)
    await world.commit_profile(client, token)
    mu = await world.rate(client, token, sport=sport)
    if intent is not None:
        await world.declare_intent(client, token, intent=intent, sport=sport)
    return {"id": player_id, "token": token, "mu": mu}


async def _a_yes(client, sender: dict, *, towards: UUID, sport: Sport):
    """One *Let's play*, citing the deal it was said on.

    The deck rather than a shortlist, because the deck reads no declaration
    (``docs/adr/0169`` §2) — so a player who never declared can say yes here,
    which is exactly the case the rule has to be asserted on.
    """

    dealt = await world.deck(client, sender["token"], sport)
    assert dealt.status_code == 200, dealt.text
    assert str(towards) in {row["player_id"] for row in dealt.json()["candidates"]}
    said = await world.express_interest(
        client,
        sender["token"],
        player_id=towards,
        search_id=dealt.json()["search"]["search_id"],
        sport=sport,
    )
    assert said.status_code in (200, 201), said.text
    return said.json()


async def _a_mutual(
    client, session_factory, candidate_source, one: dict, other: dict, *, sport: Sport
) -> dict:
    await world.fold_the_log(session_factory, candidate_source)
    await _a_yes(client, one, towards=other["id"], sport=sport)
    closed = await _a_yes(client, other, towards=one["id"], sport=sport)
    assert closed["mutual"] is True, "the second yes was not told it landed"
    return closed


async def _the_challenge(client, token: str, challenge_id: str) -> dict:
    read = await client.get(
        f"/api/v1/challenges/{challenge_id}", headers=world.auth(token)
    )
    assert read.status_code == 200, read.text
    return read.json()


async def _the_only_game(client, token: str) -> dict:
    listed = await client.get("/api/v1/games", headers=world.auth(token))
    assert listed.status_code == 200, listed.text
    (game,) = listed.json()["games"]
    return game


# -- counted unless either declared for fun -----------------------------------


async def test_one_for_fun_among_the_pair_opens_a_friendly(
    client, session_factory, candidate_source
):
    """Marek declared padel *for fun*; Ania *competitive*. The challenge is
    ``FOR_FUN`` and the tennis game it opens in the same act is a friendly —
    the existing derivation, read off a mode that is now there to be read."""

    ania = await _a_player(client, "ania", sport=Sport.TENNIS, intent="COMPETITIVE")
    marek = await _a_player(client, "marek", sport=Sport.TENNIS, intent="FOR_FUN")
    closed = await _a_mutual(
        client, session_factory, candidate_source, ania, marek, sport=Sport.TENNIS
    )

    challenge = await _the_challenge(client, ania["token"], closed["challenge_id"])
    assert challenge["mode"] == "FOR_FUN"
    assert (await _the_only_game(client, ania["token"]))["kind"] == "FRIENDLY"


async def test_two_competitive_declarers_open_a_counted_game(
    client, session_factory, candidate_source
):
    ania = await _a_player(client, "ania", sport=Sport.TENNIS, intent="COMPETITIVE")
    marek = await _a_player(client, "marek", sport=Sport.TENNIS, intent="COMPETITIVE")
    closed = await _a_mutual(
        client, session_factory, candidate_source, ania, marek, sport=Sport.TENNIS
    )

    challenge = await _the_challenge(client, ania["token"], closed["challenge_id"])
    assert challenge["mode"] is None, (
        "two competitive declarers get a counted game by the absence, not a stamp"
    )
    assert (await _the_only_game(client, marek["token"]))["kind"] == "COUNTED"


async def test_one_competitive_and_one_undeclared_open_a_counted_game(
    client, session_factory, candidate_source
):
    """*Never declared* is an absence like *no preference*: the deck let the
    undeclared player say yes (it reads no declaration), and the game they get
    is counted, because nobody chose a friendly."""

    ania = await _a_player(client, "ania", sport=Sport.TENNIS, intent="COMPETITIVE")
    marek = await _a_player(client, "marek", sport=Sport.TENNIS, intent=None)
    closed = await _a_mutual(
        client, session_factory, candidate_source, ania, marek, sport=Sport.TENNIS
    )

    challenge = await _the_challenge(client, marek["token"], closed["challenge_id"])
    assert challenge["mode"] is None
    assert (await _the_only_game(client, marek["token"]))["kind"] == "COUNTED"
