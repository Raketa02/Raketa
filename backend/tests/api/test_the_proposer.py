"""The proposer, run as the job runs it and read as the phone reads it (#540;
the mechanics §4.3, §5, §6.2–§6.3, §7, §19; the screens C3).

Every member is made the way the platform makes one — signed up, a week of
hours, rated, an intent declared, a card saved — and a group is joined over
HTTP. **The proposer runs as the job runs it**, through the composition root
over the test's database and clock, and **every claim is read back as a player
reads it**: their group deck, a yes over HTTP.

The claims, one family each:

- a court hour is dealt **the most even four** of the members free for it, at
  their best hour, and a second run deals nothing new;
- **after a no** the seat goes to the next best fits, and **at half In** a pick
  goes out in new versions;
- a card whose **last court at its club and hour went** is over, and the people
  who were In are dealt a new card first;
- a group plays at **its home club, then the clubs within 10 km**, never further;
- a **change** — somebody joining — makes the pool due, and the short tick deals
  from it without waiting for the sweep.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**; the tenth is a
Saturday.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import build_propose_games
from app.modules.proposals.application.propose_games import (
    DueForProposing,
    Proposed,
)
from tests.api import players_world as players
from tests.api.club_courts_world import EXCEPTIONS, confirms_settings
from tests.api.proposals_world import (
    GROUPS,
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    a_club_selling,
    a_group,
    a_member,
    live_ids,
    says_no,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock

#: Saturday evenings, 17:00–19:00.
SATURDAY_EVENINGS = [{"day": 6, "hour": hour} for hour in (17, 18)]


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


async def proposes(session_factory, clock, *pools: UUID) -> Proposed:
    """One run over these pools, as the job runs one."""

    done = Proposed()
    async with session_factory() as session:
        proposer = build_propose_games(session, clock=clock)
        for pool_id in pools:
            done += await proposer.execute(pool_id)
    return done


async def deck_of(client, player: dict, group: UUID) -> list[dict]:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": "COMPETITIVE"},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()["cards"]


def names_on(card: dict) -> set[str]:
    return {
        tile["name"] for tile in (*card["sides"]["yours"], *card["sides"]["theirs"])
    }


def ids_of(cards: list[dict]) -> list[str]:
    return [card["proposal_id"] for card in cards]


def starts(cards: list[dict]) -> list[datetime]:
    return [datetime.fromisoformat(card["starts_at"]) for card in cards]


async def members(client, session_factory, payments, *named: str, **overrides):
    return [
        await a_member(client, session_factory, payments, name, **overrides)
        for name in named
    ]


# --------------------------------------------------------------------------- #
# The most even four
# --------------------------------------------------------------------------- #


async def test_a_court_hour_is_dealt_the_most_even_four_at_their_best_hour(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    ola, kuba, ewa, tomek = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek"
    )
    (ania,) = await members(client, session_factory, payments, "ania", mu=2.8)
    group = await a_group(client, ola, club, kuba, ewa, tomek, ania)

    proposed = await proposes(session_factory, clock, group)

    assert proposed == Proposed(pools=1, made=2)
    # The four at one Level on the first Saturday; the next Saturday, the next
    # evenest — Ania with the first three to join.
    [card] = await deck_of(client, tomek, group)
    assert starts([card]) == [SATURDAY_FIVE]
    assert card["type"] == "PICKED_FOR_YOU"
    assert names_on(card) == {"ola", "kuba", "ewa", "tomek"}
    [card] = await deck_of(client, ania, group)
    assert starts([card]) == [warsaw(17, 17)]
    assert names_on(card) == {"ola", "kuba", "ewa", "ania"}
    assert starts(await deck_of(client, ola, group)) == [SATURDAY_FIVE, warsaw(17, 17)]


async def test_running_again_deals_nothing_new(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17), (6, 18)])
    crowd = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek", "ania"
    )
    group = await a_group(client, crowd[0], club, *crowd[1:])
    first = await proposes(session_factory, clock, group)
    deck = await deck_of(client, crowd[0], group)

    again = await proposes(session_factory, clock, group)

    assert first.made > 0
    assert again == Proposed(pools=1)
    assert await deck_of(client, crowd[0], group) == deck


async def test_somebody_who_does_not_want_the_kind_or_is_not_free_is_not_dealt(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    four = await members(
        client, session_factory, payments, "ola", "kuba", "ewa", "tomek"
    )
    (fun,) = await members(client, session_factory, payments, "ania", intent="FOR_FUN")
    (busy,) = await members(
        client, session_factory, payments, "marek", week=[{"day": 1, "hour": 9}]
    )
    group = await a_group(client, four[0], club, *four[1:], fun, busy)

    await proposes(session_factory, clock, group)

    assert await deck_of(client, fun, group) == []
    assert await deck_of(client, busy, group) == []


# --------------------------------------------------------------------------- #
# Dealing a game still filling
# --------------------------------------------------------------------------- #


async def test_after_a_no_the_seat_goes_to_the_next_best_fits(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        "ania",
        week=SATURDAY_EVENINGS,
    )
    ola, kuba, ewa, tomek, ania = crowd
    group = await a_group(client, ola, club, kuba, ewa, tomek, ania)
    await proposes(session_factory, clock, group)
    [card] = [
        c for c in await deck_of(client, kuba, group) if starts([c]) == [SATURDAY_FIVE]
    ]
    assert names_on(card) == {"ola", "kuba", "ewa", "tomek"}
    assert card["proposal_id"] not in ids_of(await deck_of(client, ania, group))

    assert (await says_no(client, kuba, UUID(card["proposal_id"]))).status_code == 204
    proposed = await proposes(session_factory, clock, group)

    assert proposed.dealt == 1
    dealt_to_ania = {c["proposal_id"]: c for c in await deck_of(client, ania, group)}
    assert names_on(dealt_to_ania[card["proposal_id"]]) == {
        "ola",
        "ewa",
        "tomek",
        "ania",
    }
    # A no is final: the card never comes back to Kuba.
    assert card["proposal_id"] not in ids_of(await deck_of(client, kuba, group))


async def test_at_half_in_a_pick_goes_out_in_new_versions(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        "ania",
        "marek",
        "zofia",
        "piotr",
        week=SATURDAY_EVENINGS,
    )
    ola, kuba = crowd[:2]
    group = await a_group(client, ola, club, *crowd[1:])
    await proposes(session_factory, clock, group)
    [card] = [
        c for c in await deck_of(client, ola, group) if starts([c]) == [SATURDAY_FIVE]
    ]
    for player in (ola, kuba):
        assert (
            await says_yes(client, player, UUID(card["proposal_id"]))
        ).status_code == 200

    proposed = await proposes(session_factory, clock, group)

    assert proposed.dealt == 2
    for newcomer in crowd[4:]:
        seen = {c["proposal_id"]: c for c in await deck_of(client, newcomer, group)}
        widened = seen[card["proposal_id"]]
        assert widened["in_count"] == 2
        assert widened["version_count"] == 3
        assert {"ola", "kuba", newcomer["name"]} <= names_on(widened)


# --------------------------------------------------------------------------- #
# A lost court hour
# --------------------------------------------------------------------------- #


async def test_when_the_last_court_goes_the_people_in_get_a_new_card_first(
    client, session_factory, payments, clock
):
    club, desk = await a_club_and_its_desk(client, hours=[(6, 17), (6, 18)])
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        week=SATURDAY_EVENINGS,
    )
    ola, kuba, ewa, tomek = crowd
    group = await a_group(client, ola, club, kuba, ewa, tomek)
    await proposes(session_factory, clock, group)
    [card] = await deck_of(client, tomek, group)
    lost = UUID(card["proposal_id"])
    for player in (ola, kuba, ewa):
        assert (await says_yes(client, player, lost)).status_code == 200

    closed = await client.post(
        EXCEPTIONS,
        json={
            "court_ids": None,
            "first_day": "2026-10-10",
            "last_day": "2026-10-10",
            "from_hour": 17,
            "until_hour": 18,
            "reason": "Repair",
        },
        headers=desk,
    )
    assert closed.status_code == 201, closed.text
    proposed = await proposes(session_factory, clock, group)

    assert (proposed.lost, proposed.made) == (1, 1)
    refused = await says_yes(client, tomek, lost)
    assert refused.status_code == 409
    assert refused.json()["code"] == "proposal_is_over"
    assert refused.json()["details"] == {"standing": "COURT_HOUR_LOST"}
    # Nobody's yes carries over: a yes was to a court at an hour.
    [again] = await deck_of(client, ola, group)
    assert starts([again]) == [warsaw(10, 18)]
    assert names_on(again) == {"ola", "kuba", "ewa", "tomek"}
    assert again["in_count"] == 0
    assert await live_ids(client, ola) == []


async def test_a_club_lengthening_its_release_lead_takes_no_card_s_court(
    client, session_factory, payments, clock
):
    club, desk = await a_club_and_its_desk(client, hours=[(6, 17)], release_lead_days=1)
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        week=SATURDAY_EVENINGS,
    )
    group = await a_group(client, crowd[0], club, *crowd[1:])
    await proposes(session_factory, clock, group)
    [card] = [
        c
        for c in await deck_of(client, crowd[0], group)
        if starts([c]) == [SATURDAY_FIVE]
    ]

    # Five days' lead from now on: on Thursday morning Saturday 17:00 is no
    # longer for sale — but the card was made with a day's, and its court is
    # still there.
    await confirms_settings(client, desk, release_lead_days=5)
    clock.move(timedelta(days=3, hours=1))
    proposed = await proposes(session_factory, clock, group)

    assert proposed.lost == 0
    assert card["proposal_id"] in ids_of(await deck_of(client, crowd[1], group))


async def test_a_card_at_a_three_day_club_is_never_dealt_for_the_day_after_tomorrow(
    client, session_factory, payments, clock
):
    """Only Raketa is the one way (#670; ``docs/adr/0196`` §1), so a game's
    book-by is always its release time: three days before it, at a club that
    keeps the default. On Monday morning, Tuesday's and Wednesday's 18:00 have
    gone back to the club, and the first card is Thursday's, open until Monday
    18:00."""

    club = await a_club_selling(
        client, hours=[(2, 18), (3, 18), (4, 18)], release_lead_days=3
    )
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        week=[{"day": day, "hour": 18} for day in (2, 3, 4)],
    )
    group = await a_group(client, crowd[0], club, *crowd[1:])

    await proposes(session_factory, clock, group)

    [card] = await deck_of(client, crowd[0], group)
    assert starts([card]) == [warsaw(8, 18)]
    assert datetime.fromisoformat(card["deadline"]) == warsaw(5, 18)


# --------------------------------------------------------------------------- #
# Where
# --------------------------------------------------------------------------- #


async def test_a_group_plays_at_its_home_club_then_the_clubs_within_ten_km(
    client, session_factory, payments, clock
):
    home = await a_club_selling(client, hours=[(6, 17)])
    # Two kilometres south, and forty north.
    near = await a_club_selling(
        client, name="Hala Zabłocie", hours=[(6, 18)], point=(50.042, 19.95)
    )
    far = await a_club_selling(
        client, name="Tenis Katowice", hours=[(6, 19)], point=(50.42, 19.95)
    )
    crowd = await members(
        client,
        session_factory,
        payments,
        "ola",
        "kuba",
        "ewa",
        "tomek",
        "ania",
        "marek",
        "zofia",
        "piotr",
        week=[{"day": 6, "hour": hour} for hour in (17, 18, 19)],
    )
    group = await a_group(client, crowd[0], home, *crowd[1:])

    await proposes(session_factory, clock, group)

    clubs = {
        card["club"]["id"]
        for player in crowd
        for card in await deck_of(client, player, group)
    }
    assert clubs == {home, near}
    assert far not in clubs


# --------------------------------------------------------------------------- #
# On changes
# --------------------------------------------------------------------------- #


async def test_somebody_joining_makes_the_pool_due_and_the_tick_deals_to_it(
    client, session_factory, payments, clock
):
    club = await a_club_selling(client, hours=[(6, 17)])
    three = await members(client, session_factory, payments, "ola", "kuba", "ewa")
    (tomek,) = await members(client, session_factory, payments, "tomek")
    group = await a_group(client, three[0], club, *three[1:])
    assert await proposes(session_factory, clock, group) == Proposed(pools=1)
    due = DueForProposing()
    await players.deliver_the_outbox(session_factory, proposer_due=due)
    due.take()

    joined = await client.post(f"{GROUPS}/{group}/membership", headers=tomek["headers"])
    assert joined.status_code in (200, 201), joined.text
    await players.deliver_the_outbox(session_factory, proposer_due=due)
    async with session_factory() as session:
        proposer = build_propose_games(session, clock=clock)
        pools = await proposer.pools_due(due.take())
        proposed = Proposed()
        for pool_id in pools:
            proposed += await proposer.execute(pool_id)

    assert pools == [group]
    assert proposed.made == 1
    [card] = await deck_of(client, tomek, group)
    assert names_on(card) == {"ola", "kuba", "ewa", "tomek"}
