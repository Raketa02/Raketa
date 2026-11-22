"""**For-fun tables are built by shared tags** — the proposer run as the job
runs it, and read as the phone reads it (``docs/adr/0207`` §1, §3; #831).

Every member is made the way the platform makes one — their Social tags
committed through the profile, so the player directory hears them through the
outbox — and joins over HTTP; a friendship is asked and accepted over HTTP. The
proposer runs through the composition root over the test's database and clock,
and every claim is read back off a player's For-fun deck.

- **The best company first**: among the fours the gates let through, the one
  that shares the most is dealt the first Saturday, though another is evener —
  and the evener one is dealt the next.
- **New faces break a tie**: two friends are not seated together while a four
  of strangers shares as much.
- **The gates hold**: the level window and the newcomer's tightening of it
  keep out somebody who shares everything, and the sides are still the
  evenest way round.
- **Competitive is today's**: the same people and tags, wanting competitive,
  are dealt the evenest four first.
- **A For-fun rescue's Seat open card goes to the best company** for the
  players still on the game, never the first evenly matched member to join.

The club sells one padel court on Saturdays at 17:00, at 30 zł a seat; the
clock stands on **Monday 5 October 2026, 08:00 in Kraków**, so the engine's
fourteen days hold two Saturdays.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.engines.matchfit.core import SearchMode
from app.modules.proposals.application.propose_games import Proposed
from tests.api.proposals_world import (
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
#: Kuba's, which nobody else holds.
KUBA_S = ("QUIET_AND_FOCUSED", "STRAIGHT_HOME_AFTER")
NEXT_SATURDAY = warsaw(17, 17)


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    return await a_club_selling(client, hours=[(6, 17)])


async def proposes(session_factory, clock, pool: UUID) -> Proposed:
    async with session_factory() as session:
        return await build_propose_games(session, clock=clock).execute(pool)


async def deck_of(client, player: dict, group: UUID, *, kind: str) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": kind},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


def names_on(card: dict) -> set[str]:
    return {
        tile["nickname"] for tile in (*card["sides"]["yours"], *card["sides"]["theirs"])
    }


def dealt(cards: list[dict]) -> list[tuple[datetime, set[str]]]:
    return [
        (datetime.fromisoformat(card["starts_at"]), names_on(card)) for card in cards
    ]


async def five(
    client, session_factory, payments, mailbox, *, intent: str, kuba: tuple[str, ...]
) -> dict[str, dict]:
    """Ola, Ania and Marek at 2,5 and Zofia at 3,0, who share a drink, the
    laughs and meeting players; and Kuba at 2,5, holding ``kuba``. Joined in
    that order, Ola's group."""

    def member(name: str, tags: tuple[str, ...], mu: float = 2.5):
        return a_member(
            client, session_factory, payments, name, intent=intent, tags=tags, mu=mu
        )

    people = {
        "ola": await member("ola", (DRINK, LAUGHS, MEET)),
        "ania": await member("ania", (DRINK, LAUGHS, MEET)),
        "marek": await member("marek", (DRINK, LAUGHS, MEET)),
        "zofia": await member("zofia", (DRINK, LAUGHS, MEET), mu=3.0),
        "kuba": await member("kuba", kuba),
    }
    await mailbox.drain()
    return people


async def test_the_for_fun_deck_is_dealt_the_highest_vibe_four(
    client, session_factory, payments, clock, club, mailbox
):
    people = await five(
        client, session_factory, payments, mailbox, intent="FOR_FUN", kuba=KUBA_S
    )
    group = await a_group(
        client, people["ola"], club, *(p for n, p in people.items() if n != "ola")
    )

    proposed = await proposes(session_factory, clock, group)

    assert proposed == Proposed(pools=1, made=2)
    # The four who share everything, though Kuba's four is evener; Kuba's
    # the next Saturday.
    assert dealt(await deck_of(client, people["ola"], group, kind="FOR_FUN")) == [
        (SATURDAY_FIVE, {"ola", "ania", "marek", "zofia"}),
        (NEXT_SATURDAY, {"ola", "ania", "marek", "kuba"}),
    ]
    (zofia_s,) = await deck_of(client, people["zofia"], group, kind="FOR_FUN")
    assert zofia_s["vibe"] == {"pct": 100}
    # The court hour, the club, the share and the book-by — its release, a
    # day ahead — are the club's, as ever.
    assert zofia_s["club"]["id"] == club
    assert zofia_s["share_grosze"] == 30_00
    assert datetime.fromisoformat(zofia_s["deadline"]) == SATURDAY_FIVE - timedelta(
        days=1
    )
    assert zofia_s["type"] == "PICKED_FOR_YOU"


async def test_the_best_company_keeps_the_newcomer_s_window_and_stands_evenest(
    client, session_factory, payments, clock, club, mailbox
):
    """Everybody shares everything. Kuba at 3,2 is inside For fun's window
    of each of them — but they are all new to Raketa, and a pair holding a
    newcomer takes the competitive window, which Ola at 2,5 and Ania at 2,6
    are outside of him. So there is one four, and it is not his."""

    shared = (DRINK, LAUGHS, MEET)

    def member(name: str, mu: float):
        return a_member(
            client,
            session_factory,
            payments,
            name,
            intent="FOR_FUN",
            tags=shared,
            mu=mu,
        )

    ola = await member("ola", 2.5)
    rest = [
        await member(name, mu)
        for name, mu in (("ania", 2.6), ("marek", 2.9), ("zofia", 3.0), ("kuba", 3.2))
    ]
    await mailbox.drain()
    group = await a_group(client, ola, club, *rest)

    await proposes(session_factory, clock, group)

    cards = await deck_of(client, ola, group, kind="FOR_FUN")
    assert [names for _, names in dealt(cards)] == [
        {"ola", "ania", "marek", "zofia"}
    ] * len(cards)
    assert cards
    assert await deck_of(client, rest[-1], group, kind="FOR_FUN") == []
    # The sides are still the evenest way round: Ola beside Zofia, 5,5 a side.
    sides = cards[0]["sides"]
    assert [{tile["nickname"] for tile in sides[side]} for side in sides] == [
        {"ola", "zofia"},
        {"ania", "marek"},
    ]


async def test_two_friends_lose_a_tie_to_a_four_of_new_faces(
    client, session_factory, payments, clock, club, mailbox
):
    shared = (DRINK, LAUGHS, MEET)
    people = await five(
        client, session_factory, payments, mailbox, intent="FOR_FUN", kuba=shared
    )
    ola, ania = people["ola"], people["ania"]
    group = await a_group(
        client, ola, club, *(p for n, p in people.items() if n != "ola")
    )
    asked = await client.post(
        "/api/v1/friends/requests",
        json={"player_id": str(ania["id"]), "made_from": "MEMBERS"},
        headers=ola["headers"],
    )
    assert asked.status_code == 200, asked.text
    accepted = await client.post(
        f"/api/v1/friends/requests/{ola['id']}/acceptance", headers=ania["headers"]
    )
    assert accepted.status_code == 200, accepted.text

    await proposes(session_factory, clock, group)

    # Everybody shares everything; only Ola and Ania know each other — so
    # the first Saturday's four holds one of them, and Kuba for the other.
    first, _ = dealt(await deck_of(client, people["marek"], group, kind="FOR_FUN"))
    assert first == (SATURDAY_FIVE, {"ola", "marek", "zofia", "kuba"})


async def test_the_same_people_wanting_competitive_are_dealt_the_evenest_first(
    client, session_factory, payments, clock, club, mailbox
):
    people = await five(
        client, session_factory, payments, mailbox, intent="COMPETITIVE", kuba=KUBA_S
    )
    group = await a_group(
        client, people["ola"], club, *(p for n, p in people.items() if n != "ola")
    )

    await proposes(session_factory, clock, group)

    assert dealt(await deck_of(client, people["ola"], group, kind="COMPETITIVE")) == [
        (SATURDAY_FIVE, {"ola", "ania", "marek", "kuba"}),
        (NEXT_SATURDAY, {"ola", "ania", "marek", "zofia"}),
    ]


async def test_a_for_fun_seat_open_card_goes_to_the_best_company_for_the_three_left(
    client, session_factory, payments, clock, club, mailbox, statements
):
    """Wiktor, Wanda and Witek share a drink, the laughs and meeting players;
    Wera leaves. Of the four free for her seat, Kuba is as even as the rest,
    and first to have joined — and shares nothing with the three, so he is
    the one not dealt it."""

    shared = (DRINK, LAUGHS, MEET)

    def member(name: str, tags: tuple[str, ...]):
        return a_member(
            client, session_factory, payments, name, intent="FOR_FUN", tags=tags
        )

    four = [await member(name, shared) for name in ("wiktor", "wanda", "witek")]
    four.append(await member("wera", shared))
    kuba = await member("kuba", KUBA_S)
    others = [await member(name, shared) for name in ("ola", "ania", "marek")]
    await mailbox.drain()
    group = await a_group(client, four[0], club, kuba, *four[1:], *others)
    game = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
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

    for player in others:
        (card,) = await deck_of(client, player, group, kind="FOR_FUN")
        assert (card["type"], card["proposal_id"]) == ("SEAT_OPEN", booking)
        assert card["vibe"] == {"pct": 100}
    assert await deck_of(client, kuba, group, kind="FOR_FUN") == []

    # What the best company costs a deck read (``docs/adr/0207`` §11): the
    # tags of everybody offered, beside the card's own; and whether each of
    # the three left is friends with any of them, from their own side —
    # beside the reader's own friends, the faces' tag.
    with statements.counting() as sent:
        await deck_of(client, others[0], group, kind="FOR_FUN")
    assert len(sent.naming("discovery_player_tags")) == 2
    assert len(sent.naming("friend_relations")) == 1 + 3
