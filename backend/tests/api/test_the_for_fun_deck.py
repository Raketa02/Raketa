"""A group's **For-fun** deck, read as the phone reads it (#830;
``docs/adr/0207`` §2, §4, §5).

**Every For-fun card carries its Social vibe** — how much the people on the
reader's version share, worked out from their tags now — and **no forecast**,
though the forecast still arranged the sides. **The deck opens on the best
company**: the card owed to the reader after a club's cancel, then a rescue
they fit, then every other card by the vibe it shows, a tie going to the fewest
seats open after the reader's yes. **The competitive deck is unchanged**: its
cards carry a forecast and no vibe, in §8.2's order.

Every player is made the way the platform makes one, their tags committed
through the profile, and the player directory hears them through the outbox —
so a read follows a delivery, as the worker would have made it. Every card is
made the way the proposer makes one (``MakeProposal``), and answered over HTTP.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.engines.matchfit.core import SearchMode
from tests.api.proposals_world import (
    EVERY_HOUR,
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

DRINK, LAUGHS, MEET = "STAYS_FOR_A_DRINK", "LAUGHS_OFF_MISTAKES", "HERE_TO_MEET_PLAYERS"
#: 💘 — held, shown, and never counted.
SOMEONE = "OPEN_TO_MEET_SOMEONE"
PLAYS, IMPROVES = "PLAYS_TO_WIN", "HERE_TO_IMPROVE"

#: Every hour but Saturday 17:00, the rescue's: only Ola is free for its seat.
BUT_THE_RESCUE_S_HOUR = [
    cell for cell in EVERY_HOUR if (cell["day"], cell["hour"]) != (6, 17)
]

#: Who holds which tags. Ola and Ania hold 💘 beside the three the whole of
#: pick A holds, so counted it would take A's 100% down to 90%.
TAGS = {
    "ola": (DRINK, LAUGHS, MEET, SOMEONE),
    "ania": (DRINK, LAUGHS, MEET, SOMEONE),
    "marek": (DRINK, LAUGHS, MEET),
    "zofia": (DRINK, LAUGHS, MEET),
    "piotr": (DRINK, LAUGHS),
    "kuba": ("QUIET_AND_FOCUSED", "STRAIGHT_HOME_AFTER"),
    "ewa": ("SETTLES_UP_ON_THE_SPOT", "BOOKS_THE_NEXT_ONE"),
    "tomek": ("SHARES_A_LIFT", "WARMS_UP_PROPERLY"),
    # The rescue's four; Wera is the one who leaves.
    "wiktor": (DRINK, PLAYS),
    "wanda": (PLAYS, IMPROVES),
    "witek": (PLAYS, IMPROVES),
    "wera": (PLAYS, IMPROVES),
}


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client)


async def a_crowd(client, session_factory, payments, *, intent: str) -> dict:
    """Everybody in ``TAGS``, rated alike at padel 2,5, of one Play intent."""

    return {
        name: await a_member(
            client,
            session_factory,
            payments,
            name,
            intent=intent,
            tags=tags,
            week=EVERY_HOUR
            if name == "ola" or name.startswith("w")
            else BUT_THE_RESCUE_S_HOUR,
        )
        for name, tags in TAGS.items()
    }


async def deck_of(client, player: dict, group: UUID, *, kind: str) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": kind},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


async def a_seat_left(client, session_factory, clock, club, group, four) -> UUID:
    """The four's game on Saturday at 17:00, booked by the last yes, and the
    last of them leaving it before the cut-off — a seat on the board."""

    game = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=SATURDAY_FIVE,
        kind=SearchMode.FOR_FUN,
        versions=(tuple(four),),
    )
    for player in four:
        said = await says_yes(client, player, game)
        assert said.status_code == 200, said.text
    booking = said.json()["booked"]["booking_id"]
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=four[-1]["headers"]
    )
    assert left.status_code == 200, left.text
    return UUID(booking)


@pytest.fixture
async def friendlies(client, session_factory, payments, clock, club, mailbox) -> dict:
    """Ola's For-fun deck: a card owed to her, a rescue she fits, and four
    picks — each table a different set of people."""

    crowd = await a_crowd(client, session_factory, payments, intent="FOR_FUN")
    ola = crowd["ola"]
    group = await a_group(
        client, ola, club, *(p for n, p in crowd.items() if n != "ola")
    )

    async def a_friendly(start, *named: str, owed: bool = False) -> UUID:
        return await makes(
            session_factory,
            clock,
            pool_id=group,
            club_id=club,
            start=start,
            kind=SearchMode.FOR_FUN,
            versions=(tuple(crowd[name] for name in named),),
            owed_card_for=(ola,) if owed else (),
        )

    cards = {
        # Ola shares nothing with them, nor they with each other: 0%.
        "owed": await a_friendly(
            warsaw(11, 18), "ola", "kuba", "ewa", "tomek", owed=True
        ),
        # All four hold the same three, 💘 aside: 100%.
        "a": await a_friendly(warsaw(6, 19), "ola", "ania", "marek", "zofia"),
        # Ola and Piotr share two; Kuba nothing: (1 + 1 + 0) ÷ 7 is 29%.
        "b": await a_friendly(warsaw(7, 19), "ola", "piotr", "kuba"),
        # The same table's shape, Ewa In: 29%, one seat nearer filling.
        "c": await a_friendly(warsaw(8, 19), "ola", "piotr", "ewa"),
        # Nothing shared, Kuba In: 0% — nearer filling than b, and after it.
        "d": await a_friendly(warsaw(9, 19), "ola", "tomek", "kuba"),
    }
    assert (await says_yes(client, crowd["ewa"], cards["c"])).status_code == 200
    assert (await says_yes(client, crowd["kuba"], cards["d"])).status_code == 200
    # Ola with Wiktor, Wanda and Witek, Wera's seat empty: (⅓ + 1 + 1 + 1) ÷ 9
    # carryings — Ola's drink shared with Wiktor, the rest of hers with
    # nobody, the three sharing what they play for — is 37%.
    cards["rescue"] = await a_seat_left(
        client,
        session_factory,
        clock,
        club,
        group,
        [crowd[name] for name in ("wiktor", "wanda", "witek", "wera")],
    )
    await mailbox.drain()
    return {"crowd": crowd, "group": group, "cards": cards}


def the_ids(cards: dict, *names: str) -> list[str]:
    return [str(cards[name]) for name in names]


async def test_the_for_fun_deck_opens_on_the_best_company(client, friendlies):
    """Owed first, then the rescue she fits, then by the vibe each card shows —
    the two at 29% by how near each is to filling — and the 0% table last,
    though it is nearer filling than one before it."""

    deck = await deck_of(
        client, friendlies["crowd"]["ola"], friendlies["group"], kind="FOR_FUN"
    )

    dealt = deck["cards"]
    assert [card["proposal_id"] for card in dealt] == the_ids(
        friendlies["cards"], "owed", "rescue", "a", "c", "b", "d"
    )
    assert [card["vibe"] for card in dealt] == [
        {"pct": 0},
        {"pct": 37},
        {"pct": 100},
        {"pct": 29},
        {"pct": 29},
        {"pct": 0},
    ]
    assert dealt[1]["type"] == "SEAT_OPEN"
    assert [card["open_seats_after_your_yes"] for card in dealt[3:5]] == [2, 3]


async def test_a_for_fun_card_shows_no_forecast_and_its_sides_stay_evenest(
    client, friendlies
):
    deck = await deck_of(
        client, friendlies["crowd"]["ola"], friendlies["group"], kind="FOR_FUN"
    )

    assert deck["cards"] and all(card["forecast"] is None for card in deck["cards"])
    # Everybody is still seated: a four's sides are two and two.
    four = next(
        card
        for card in deck["cards"]
        if card["proposal_id"] == str(friendlies["cards"]["a"])
    )
    assert [len(four["sides"]["yours"]), len(four["sides"]["theirs"])] == [2, 2]


async def test_the_vibe_follows_the_tags_on_the_next_read(client, friendlies, mailbox):
    """Stored nowhere: Kuba picks up Ola's drink and laughs, and pick b's 29%
    is worked out again from the tags as they stand."""

    crowd = friendlies["crowd"]
    changed = await client.put(
        "/api/v1/players/me/social-tags",
        json={"social_tags": [DRINK, LAUGHS]},
        headers=crowd["kuba"]["headers"],
    )
    assert changed.status_code == 200, changed.text
    await mailbox.drain()

    deck = await deck_of(client, crowd["ola"], friendlies["group"], kind="FOR_FUN")
    vibes = {card["proposal_id"]: card["vibe"]["pct"] for card in deck["cards"]}

    # Ola, Piotr and Kuba now share the drink and the laughs: (2 + 2 + 2) ÷ 7.
    assert vibes[str(friendlies["cards"]["b"])] == 86


async def test_the_competitive_deck_shows_a_forecast_and_no_vibe_in_its_own_order(
    client, session_factory, payments, clock, club, mailbox
):
    """The same tables dealt competitive: momentum first, as ever — the table
    that shares nothing, with Kuba In, ahead of the one that shares
    everything."""

    crowd = await a_crowd(client, session_factory, payments, intent="COMPETITIVE")
    ola = crowd["ola"]
    group = await a_group(
        client, ola, club, *(p for n, p in crowd.items() if n != "ola")
    )
    shares_everything = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(6, 19),
        versions=(tuple(crowd[n] for n in ("ola", "ania", "marek", "zofia")),),
    )
    shares_nothing = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(9, 19),
        versions=(tuple(crowd[n] for n in ("ola", "tomek", "kuba")),),
    )
    assert (await says_yes(client, crowd["kuba"], shares_nothing)).status_code == 200
    await mailbox.drain()

    deck = await deck_of(client, ola, group, kind="COMPETITIVE")

    assert [card["proposal_id"] for card in deck["cards"]] == [
        str(shares_nothing),
        str(shares_everything),
    ]
    assert all(card["vibe"] is None for card in deck["cards"])
    assert all(card["forecast"] is not None for card in deck["cards"])


async def test_the_for_fun_deck_reads_every_table_s_tags_in_one_statement(
    client, friendlies, statements
):
    """**The deck read's cost, held** (``docs/adr/0207`` §11): six cards and
    fourteen people at their tables, and the tags are one question."""

    with statements.counting() as sent:
        await deck_of(
            client, friendlies["crowd"]["ola"], friendlies["group"], kind="FOR_FUN"
        )

    assert len(sent.naming("discovery_player_tags")) == 1
    assert len(sent) == STATEMENTS_IN_THE_FOR_FUN_DECK_READ, len(sent)


#: Everything the read above sends, measured on 2026-11-22 (#830): its pool,
#: its cards' streams, the pair rule, the forecasts, the people, the rescue's
#: offer — and the one read of the tags, the vibe's whole cost. **Unmoved by
#: #831**: Ola is the one member offered the rescue's seat, so she is its best
#: fit whatever the rule, and the best company — the tags, who played together
#: and who is friends with whom — is read only for a For-fun seat offered to
#: more members than it is dealt to (``test_the_for_fun_proposer.py`` holds
#: that read). A statement more than this is a change to argue here; a
#: projection of everybody's tags is argued in an ADR (``docs/adr/0207`` §11),
#: never added to make it fit.
STATEMENTS_IN_THE_FOR_FUN_DECK_READ = 91


async def test_a_reader_dealt_no_friendly_asks_nobody_s_tags(
    client, session_factory, payments, clock, club, mailbox, statements
):
    crowd = await a_crowd(client, session_factory, payments, intent="COMPETITIVE")
    ola = crowd["ola"]
    group = await a_group(
        client, ola, club, *(p for n, p in crowd.items() if n != "ola")
    )
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(6, 19),
        versions=(tuple(crowd[n] for n in ("ola", "ania", "marek", "zofia")),),
    )
    await mailbox.drain()

    with statements.counting() as sent:
        deck = await deck_of(client, ola, group, kind="COMPETITIVE")

    assert len(deck["cards"]) == 1
    assert sent.naming("discovery_player_tags") == []
