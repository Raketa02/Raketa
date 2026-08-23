"""Emphasis over HTTP: one loud card on a screen, drawn from real scores.

`tests/unit/test_now_composition.py` asserts the pass against hand-built screens,
where a score is whatever a case says it is. What this file adds is the half that
cannot be reached from there: that a **real** roster, scored by the shipped
engines and rendered by the real schema, clears ADR-0037's three gates and
arrives on the wire as `emphasis: true` — and that a second one does not.

That is worth its own file rather than a case in `test_now_ranked_shelves.py`
because the failure it exists for is invisible to the unit suite. `emphasis` is a
`bool` with a `False` default on both the domain card and the response model, so
a `MatchCardResponse.from_domain` that dropped the field renders every card
`false`, passes every unit test in the map, and ships a screen with nothing loud
on it — which looks exactly like an ordinary screen. It is the same defect the
enrolled strip's counting had, found the same way.

The composition itself is written through the real repositories, exactly as
`test_now_ranked_shelves.py` does and for the same reason: neither a match nor a
club has a player-facing route to create one through.
"""

from __future__ import annotations

from uuid import UUID

from tests.api.test_now_ranked_shelves import (
    ALICE,
    _blocks,
    _join,
    _ranked,
    _rate_as_beginner,
    _shelf,
    _soon,
    _write_club,
    _write_match,
)

#: How many paid seats it takes to clear all three gates on a real screen. Three
#: of four is *one seat from a game happening*, which is what the viability term
#: reads and what makes a suggestion worth shouting about: an emphatic card
#: points at a seat, so a match that needs three more people is exactly the one
#: that must not be loud.
ALMOST_FULL = 3


def _player(n: int) -> dict[str, str]:
    return {
        "email": f"player{n}@example.com",
        "password1": "hunter22!",
        "password2": "hunter22!",
        "nickname": f"player{n}",
    }


async def _a_crowd(client, how_many: int = ALMOST_FULL) -> tuple[UUID, ...]:
    """Rated players to seat, because an unrated seat is a hole in the score.

    Every one of them answers *never played*, which is the shortest honest path
    to a stored rating and puts them in the same band as the viewer — so skill
    overlap, the largest term, is not what keeps the screen quiet.
    """

    crowd = []
    for n in range(how_many):
        who, headers = await _join(client, _player(n))
        await _rate_as_beginner(client, headers)
        crowd.append(UUID(who))
    return tuple(crowd)


def _emphatic(body) -> list[str]:
    """Every card on the whole screen the server flagged, in composed order."""

    return [
        card["match_id"]
        for block in _blocks(body)
        if block["block_type"] == "shelf"
        for card in block["cards"]
        if card.get("emphasis")
    ]


async def test_a_match_clearing_all_three_gates_arrives_emphasised(
    client, session_factory
) -> None:
    """The whole path: a real roster, the real engines, and the flag on the wire.

    Nothing between the score and the phone invents this. The card's own badge is
    beside it, so a reader can see *why that one* from the same document.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    crowd = await _a_crowd(client)
    club = await _write_club(session_factory)
    match = await _write_match(session_factory, club, seated=crowd, paid=crowd)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    card = _ranked(body)["cards"][0]

    assert card["match_id"] == str(match.id)
    assert card["emphasis"] is True
    assert card["fit"]["score"] >= 90


async def test_at_most_one_card_on_the_whole_screen_is_emphasised(
    client, session_factory
) -> None:
    """Two matches that both qualify, one flag between them (ADR-0037).

    The cap is the guarantee the screen's one loud colour rests on, and it is a
    property of the *screen* — so a second qualifying match is the case that
    proves it, and it is the case a per-shelf pass would fail.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    crowd = await _a_crowd(client)
    club = await _write_club(session_factory)
    await _write_match(session_factory, club, seated=crowd, paid=crowd)
    await _write_match(
        session_factory, club, start=_soon(days=6), seated=crowd, paid=crowd
    )

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()

    assert len(_ranked(body)["cards"]) == 2
    assert len(_emphatic(body)) == 1


async def test_an_ordinary_screen_shouts_about_nothing(
    client, session_factory
) -> None:
    """The common case, and the one the flag means something because of.

    An empty match a fortnight out is a perfectly good suggestion and not an
    urgent one: it is on the shelf, it carries a badge, and nothing about it is
    loud.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    club = await _write_club(session_factory)
    await _write_match(session_factory, club, start=_soon(days=14))

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    card = _ranked(body)["cards"][0]

    assert card["emphasis"] is False
    assert card["fit"] is not None
    assert _emphatic(body) == []


async def test_a_full_match_is_never_the_loud_one(
    client, session_factory
) -> None:
    """The third gate, which is the one that is about the player rather than us.

    The highest scores on the screen live on the waitlist shelf — a full match
    outranks the joinable version of itself — and a card shouting about a match
    with no seat in it is the app being excited on its own behalf.
    """

    _, alice = await _join(client, ALICE)
    await _rate_as_beginner(client, alice)
    crowd = await _a_crowd(client, how_many=4)
    club = await _write_club(session_factory)
    await _write_match(session_factory, club, seated=crowd, paid=crowd)

    body = (await client.get("/api/v1/now?sport=PADEL", headers=alice)).json()
    waiting = _shelf(body, "fullWorthWaiting")

    # Asserted present and scoring *above* the fit gate, or the case would be
    # vacuous: a screen with nothing on it also has nothing emphatic on it.
    assert waiting is not None
    assert waiting["cards"][0]["fit"]["score"] >= 90
    assert _emphatic(body) == []
