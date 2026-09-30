"""The seeded games still filling, read back the way a player reads them
(#538, #540).

``app/seeds/proposals.py`` **runs the proposer for its pools** and answers four
of the protagonist's picks through the use case the swipe runs, so each is
asserted by signing in as the people on it: those it says are In find it among
their live yeses, and the protagonist's own yes on the pick three are In on
leaves it with no seat open — *Book it now*.

The layers under it are run as the runner runs them — the named accounts, the
clubs and their courts, the cards — with a small crowd standing in for the
cohort: players at the protagonist's own padel Level, free on her evenings, who
want competitive padel as she does.
"""

from __future__ import annotations

import re
from uuid import UUID

import pytest

from app.bootstrap.composition import build_clock, build_rated_player_query
from app.core.config import get_settings
from app.kernel import Sport
from app.seeds.catalog import SEED_PASSWORD, THE_POPULATED_PLAYER
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.payments import write_the_payment_methods
from app.seeds.proposals import IN_ON_EACH, NotEnoughToDeal, write_the_proposals
from app.seeds.runner import seed
from app.seeds.screens import ScreenIsEmpty, assert_the_group_deck
from tests.api import matchmaking_world as world
from tests.api.proposals_world import live_ids, saves_a_card, says_yes

#: Her evenings and her Saturday, which is when the picks are.
HER_WEEK = [
    {"day": day, "hour": hour} for day in (2, 3, 4, 5) for hour in (18, 19, 20)
] + [{"day": 6, "hour": hour} for hour in (9, 10, 11, 12, 14, 15)]


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def under_it(session_factory, now):
    """Everything the layer reads: the named accounts, the clubs selling
    courts, and the cards."""

    async with session_factory() as session:
        await seed(session)
    clubs = await write_the_clubs(session_factory, settings=get_settings(), now=now)
    await write_the_club_courts(
        session_factory, settings=get_settings(), now=now, clubs=clubs
    )
    await write_the_payment_methods(session_factory, now=now, cohort=[])


async def her_padel_level(session_factory, player_id: UUID) -> float:
    async with session_factory() as session:
        levels = await build_rated_player_query(session).estimates_for(
            [player_id], sport=Sport.PADEL
        )
    return levels[player_id].mu


async def a_crowd(client, session_factory, payments, size: int, *, mu: float):
    """``size`` players at padel Level ``mu``, free on her week, each with a
    card. Their handles and ids, and their headers by id."""

    crowd, headers = [], {}
    for index in range(size):
        name = f"crowd{index:02d}"
        player_id, token = await world.register(client, name)
        await world.commit_profile(client, token, weekly_hours=HER_WEEK)
        await world.rate_in(session_factory, player_id, Sport.PADEL, mu=mu)
        await world.declare_intent(
            client, token, intent="COMPETITIVE", sport=Sport.PADEL
        )
        headers[player_id] = world.auth(token)
        await saves_a_card(client, payments, headers[player_id])
        crowd.append((name, player_id))
    return crowd, headers


async def signed_in_as_her(client) -> dict:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": THE_POPULATED_PLAYER.email, "password": SEED_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return {"headers": world.auth(login.json()["access_token"])}


async def test_the_protagonist_is_dealt_picks_with_nought_to_three_in(
    client, session_factory, payments, now, under_it
):
    her = await signed_in_as_her(client)
    her_id = UUID(
        (await client.get("/api/v1/users/me", headers=her["headers"])).json()["id"]
    )
    crowd, headers = await a_crowd(
        client,
        session_factory,
        payments,
        12,
        mu=await her_padel_level(session_factory, her_id),
    )

    seeded = await write_the_proposals(
        session_factory, settings=get_settings(), now=now, cohort=crowd
    )

    assert [pick.in_count for pick in seeded.picks] == list(IN_ON_EACH)
    assert seeded.crowd == 12
    for pick in seeded.picks:
        for index, player in enumerate(pick.named):
            said = str(pick.proposal_id) in await live_ids(
                client, {"headers": headers[player]}
            )
            assert said is (index < pick.in_count)
    # The proposer deals the same people once in a batch: four picks, four
    # different fours.
    assert len({frozenset(pick.named) for pick in seeded.picks}) == len(IN_ON_EACH)
    assert seeded.proposed.made >= len(IN_ON_EACH)
    three_in = seeded.picks[-1]
    completed = await says_yes(client, her, three_in.proposal_id)
    assert completed.status_code == 200, completed.text
    assert completed.json()["open_seats"] == 0


async def test_her_group_deck_deals_every_pick_and_an_empty_one_fails_the_run(
    client, session_factory, payments, now, under_it
):
    """The screens' claim about the Games tab (#539): read through the tab's own
    read, as her, her deck holds the four picks — and a deck that would deal
    nothing is refused by name rather than handed to a developer."""

    her = await signed_in_as_her(client)
    her_id = UUID(
        (await client.get("/api/v1/users/me", headers=her["headers"])).json()["id"]
    )
    crowd, _ = await a_crowd(
        client,
        session_factory,
        payments,
        12,
        mu=await her_padel_level(session_factory, her_id),
    )
    await write_the_proposals(
        session_factory, settings=get_settings(), now=now, cohort=crowd
    )

    line = await assert_the_group_deck(
        session_factory, settings=get_settings(), now=now
    )

    # Every pick the proposer dealt her, three of them with somebody In.
    assert re.search(
        r"Padel po pracy · padel competitive: \d+ card\(s\), 3 with ", line
    )
    assert line.endswith("the first 0 seat(s) from filling")

    # Her padel intent moves to *for fun*: the competitive segment is not hers.
    moved = await client.put(
        "/api/v1/play-intents/PADEL",
        json={"intent": "FOR_FUN", "surface": "RATING_TAIL"},
        headers=her["headers"],
    )
    assert moved.status_code == 200, moved.text
    with pytest.raises(ScreenIsEmpty, match="deals nothing"):
        await assert_the_group_deck(session_factory, settings=get_settings(), now=now)


async def test_a_second_run_makes_no_pick_twice(
    client, session_factory, payments, now, under_it
):
    her = await signed_in_as_her(client)
    her_id = UUID(
        (await client.get("/api/v1/users/me", headers=her["headers"])).json()["id"]
    )
    crowd, _ = await a_crowd(
        client,
        session_factory,
        payments,
        6,
        mu=await her_padel_level(session_factory, her_id),
    )
    first = await write_the_proposals(
        session_factory, settings=get_settings(), now=now, cohort=crowd
    )

    again = await write_the_proposals(
        session_factory, settings=get_settings(), now=now, cohort=crowd
    )

    assert [pick.made for pick in first.picks] == [True] * len(IN_ON_EACH)
    assert [pick.made for pick in again.picks] == [False] * len(IN_ON_EACH)
    assert [pick.proposal_id for pick in again.picks] == [
        pick.proposal_id for pick in first.picks
    ]
    assert (again.group_id, again.created_group) == (first.group_id, False)
    assert [pick.in_count for pick in again.picks] == list(IN_ON_EACH)


async def test_a_crowd_that_does_not_fit_her_fails_the_run_by_name(
    client, session_factory, payments, now, under_it
):
    crowd, _ = await a_crowd(client, session_factory, payments, 3, mu=6.5)

    with pytest.raises(NotEnoughToDeal, match="0 of the cohort want competitive"):
        await write_the_proposals(
            session_factory, settings=get_settings(), now=now, cohort=crowd
        )


async def test_the_cohort_seats_every_pick_the_way_make_seed_runs_it(session_factory):
    """**The real crowd, in the runner's order**: the named accounts and the
    cohort, their cards, the clubs and their courts, the played history and the
    relationships — whose blocks the fit reads live — and then this layer. The
    tests above stand a small crowd in for the cohort; this one is the claim
    that the cohort ``make seed`` writes can seat four picks at all."""

    from app.seeds.clock import FixedClock
    from app.seeds.games import write_the_played_history
    from app.seeds.pairs import write_the_relationships
    from app.seeds.runner import seed_the_cohort
    from tests.unit.fake_photo_storage import InMemoryPhotoStorage

    settings = get_settings()
    now = build_clock().now()
    photos = InMemoryPhotoStorage()
    async with session_factory() as session:
        await seed(session, clock=FixedClock(at=now), settings=settings, photos=photos)
        members = await seed_the_cohort(
            session, clock=FixedClock(at=now), settings=settings, photos=photos
        )
    cohort = [(member.member.handle, member.player_id) for member in members]
    await write_the_payment_methods(session_factory, now=now, cohort=cohort)
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )
    await write_the_played_history(
        session_factory, settings=settings, now=now, photos=photos
    )
    await write_the_relationships(
        session_factory, settings=settings, now=now, photos=photos
    )

    seeded = await write_the_proposals(
        session_factory, settings=settings, now=now, cohort=cohort
    )

    assert [pick.in_count for pick in seeded.picks] == list(IN_ON_EACH)
    assert all(len(pick.named) == 3 for pick in seeded.picks)
