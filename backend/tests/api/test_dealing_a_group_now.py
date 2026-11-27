"""Dealing one group now, at a player's request (#739; ``docs/adr/0201`` §5,
Q127; the screens A2.1's *Finding* state).

Right after an intent answer on the Games tab, the phone asks Rakieta to deal
that group's games now — ``POST /pools/{id}/deal`` — and waits for the answer,
so *Finding for-fun games for you…* lasts exactly as long as the dealing. **The
route never makes a card itself**: it runs the proposer's own batch for the
pool, the one the jobs run, so it is safe beside them and beside itself.

Every player is made the way the platform makes one and every claim is read
back as the phone reads it — the deck, over HTTP. **No job runs here**: the
deal route is the only thing that deals, and the one run of the proposer
outside it is a check that the route left the job nothing to deal.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the tenth is a
Saturday.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.modules.proposals.application.propose_games import Proposed
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_selling,
    a_group,
    a_member,
    changes_intent,
    deal_path,
    deals_now,
)
from tests.unit.fake_clock import MovableClock


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def deck_of(client, player: dict, group: UUID, *, kind: str) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": kind},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


def names_on(card: dict) -> set[str]:
    return {
        tile["nickname"] for tile in (*card["sides"]["yours"], *card["sides"]["theirs"])
    }


async def anias_group(client, session_factory, payments):
    """*Padel po pracy* at a club selling padel on Saturday at 17:00. Ola,
    Kuba and Ewa play for fun; Ania plays competitively, so no four of either
    kind can be dealt. The group, and Ania with the three."""

    club = await a_club_selling(client, hours=[(6, 17)])
    three = [
        await a_member(client, session_factory, payments, name, intent="FOR_FUN")
        for name in ("ola", "kuba", "ewa")
    ]
    ania = await a_member(client, session_factory, payments, "ania")
    group = await a_group(client, three[0], club, *three[1:], ania)
    return group, ania, three


async def test_right_after_the_deal_her_for_fun_segment_holds_cards(
    client, session_factory, payments, clock
):
    group, ania, _ = await anias_group(client, session_factory, payments)
    await changes_intent(client, ania, "FOR_FUN")
    # Nothing has dealt since her answer: her For fun segment is empty.
    assert (await deck_of(client, ania, group, kind="FOR_FUN"))["cards"] == []

    dealt = await deals_now(client, ania, group)

    assert dealt.status_code == 204, dealt.text
    deck = await deck_of(client, ania, group, kind="FOR_FUN")
    [card] = deck["cards"]
    assert datetime.fromisoformat(card["starts_at"]) == SATURDAY_FIVE
    assert names_on(card) == {"ania", "ola", "kuba", "ewa"}
    assert deck["segments"] == [{"kind": "FOR_FUN", "count": 1}]


async def test_a_repeat_deals_nothing_new(client, session_factory, payments, clock):
    group, ania, three = await anias_group(client, session_factory, payments)
    await changes_intent(client, ania, "FOR_FUN")
    assert (await deals_now(client, ania, group)).status_code == 204
    deck = await deck_of(client, three[0], group, kind="FOR_FUN")

    again = await deals_now(client, three[0], group)

    assert again.status_code == 204, again.text
    assert await deck_of(client, three[0], group, kind="FOR_FUN") == deck
    # Nor is anything left for the job: the route ran its batch.
    async with session_factory() as session:
        proposer = build_propose_games(session, clock=clock)
        assert await proposer.execute(group) == Proposed(pools=1)


async def test_a_stranger_or_a_group_that_does_not_exist_is_refused_alike(
    client, session_factory, payments, clock
):
    group, ania, _ = await anias_group(client, session_factory, payments)
    await changes_intent(client, ania, "FOR_FUN")
    stranger = await a_member(
        client, session_factory, payments, "marek", intent="FOR_FUN"
    )

    for refused in (
        await deals_now(client, stranger, group),
        await deals_now(client, ania, uuid4()),
    ):
        assert (refused.status_code, refused.json()["code"]) == (
            404,
            "pool_not_found",
        )
    # Nothing was dealt for the stranger's press.
    assert (await deck_of(client, ania, group, kind="FOR_FUN"))["cards"] == []


async def test_the_deal_needs_a_player(client, session_factory, payments, clock):
    group, _, _ = await anias_group(client, session_factory, payments)

    assert (await client.post(deal_path(group))).status_code == 401
