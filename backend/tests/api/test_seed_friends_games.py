"""The seeded friends games, read back the way the player app reads them (#751).

``app/seeds/friends_games.py`` sends a **Split** game waiting on the protagonist
alone and a **Whole court** game waiting on all three **through the use cases a
phone runs**, so each is asserted by signing in and reading Home — never a
table. A second run sends nothing twice.
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import build_clock
from app.core.config import get_settings
from app.seeds.catalog import (
    RATING_WELL_ESTABLISHED,
    THE_ONE_SPORT_PLAYER,
    THE_POPULATED_PLAYER,
)
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clubs import write_the_clubs
from app.seeds.friends import write_the_friends
from app.seeds.friends_games import write_the_friends_games
from app.seeds.groups import write_the_groups
from app.seeds.payments import write_the_payment_methods
from app.seeds.runner import seed
from tests.api.test_seed_groups import signed_in


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def seeded(session_factory, now):
    async with session_factory() as session:
        await seed(session)
    settings = get_settings()
    await write_the_payment_methods(session_factory, now=now, cohort=[])
    clubs = await write_the_clubs(session_factory, settings=settings, now=now)
    await write_the_club_courts(
        session_factory, settings=settings, now=now, clubs=clubs
    )
    await write_the_groups(session_factory, settings=settings, now=now)
    await write_the_friends(session_factory, settings=settings, now=now)
    return await write_the_friends_games(session_factory, settings=settings, now=now)


async def test_her_home_has_a_split_game_waiting_on_her_and_a_whole_court_one(
    client, seeded
):
    her = await signed_in(client, THE_POPULATED_PLAYER)

    home = (await client.get("/api/v1/home", headers=her)).json()

    cards = {card["friends_game"]["pay_mode"]: card for card in home["friends_games"]}
    assert set(cards) == {"SPLIT_THE_COST", "WHOLE_COURT"}
    split = cards["SPLIT_THE_COST"]["friends_game"]
    assert split["sender_nickname"] is not None
    assert split["friends_in"] == 2
    assert split["your_invitation_until"] is not None
    whole = cards["WHOLE_COURT"]["friends_game"]
    assert whole["friends_in"] == 0
    assert cards["SPLIT_THE_COST"]["starts_at"] != cards["WHOLE_COURT"]["starts_at"]
    assert {game.sender for game in seeded.games} == {
        RATING_WELL_ESTABLISHED.slug,
        THE_ONE_SPORT_PLAYER.slug,
    }


async def test_the_senders_read_their_game_in_your_games(client, seeded):
    sender = await signed_in(client, RATING_WELL_ESTABLISHED)

    home = (await client.get("/api/v1/home", headers=sender)).json()

    [game] = [card for card in home["games"] if card["friends_game"] is not None]
    assert game["friends_game"]["you_are_the_sender"] is True
    assert game["friends_game"]["pay_mode"] == "SPLIT_THE_COST"
    states = sorted(seat["state"] for seat in game["friends_game"]["seats"])
    assert states == ["IN", "IN", "IN", "WAITING"]


async def test_a_second_run_sends_nothing_twice(session_factory, now, seeded):
    again = await write_the_friends_games(
        session_factory, settings=get_settings(), now=now
    )

    assert {game.booking_id for game in again.games} == {
        game.booking_id for game in seeded.games
    }
