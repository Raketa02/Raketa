"""You › Account › **Games & money** over HTTP (#539; the mechanics §6.6, §17.1;
the screens A7.1).

Read by the screen, saved as the player taps — both values in one write — and
read back where the deck reads it. A player who never opened it is at two games
a week with every card shown, and has written nothing; a value the form does not
offer is refused with a code naming what it does.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.infrastructure.events.event_store_model import EventStoreORM
from tests.api import players_world as players

GAMES_AND_MONEY = "/api/v1/players/me/games-and-money"


@pytest.fixture
async def player(client) -> dict:
    _, token = await players.register(client, "ola")
    return players.auth(token)


async def events_filed(session_factory) -> int:
    async with session_factory() as session:
        return int(
            await session.scalar(
                select(func.count())
                .select_from(EventStoreORM)
                .where(EventStoreORM.aggregate_type == "games_and_money")
            )
            or 0
        )


async def test_a_player_who_never_chose_is_at_two_games_and_every_card(
    client, session_factory, player
):
    read = await client.get(GAMES_AND_MONEY, headers=player)

    assert read.status_code == 200, read.text
    assert read.json() == {
        "games_per_week": 2,
        "most_ill_pay_grosze": None,
        "games_per_week_range": {"least": 1, "most": 7},
        "most_ill_pay_choices_grosze": [35_00, 45_00, 60_00],
    }
    assert await events_filed(session_factory) == 0


async def test_a_change_is_saved_and_read_back(client, player):
    saved = await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 4, "most_ill_pay_grosze": 45_00},
        headers=player,
    )

    assert saved.status_code == 200, saved.text
    assert saved.json()["games_per_week"] == 4
    assert saved.json()["most_ill_pay_grosze"] == 45_00
    read = await client.get(GAMES_AND_MONEY, headers=player)
    assert (read.json()["games_per_week"], read.json()["most_ill_pay_grosze"]) == (
        4,
        45_00,
    )


async def test_switching_the_ceiling_off_is_a_null(client, player):
    await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 2, "most_ill_pay_grosze": 35_00},
        headers=player,
    )

    saved = await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 2, "most_ill_pay_grosze": None},
        headers=player,
    )

    assert saved.json()["most_ill_pay_grosze"] is None


async def test_the_same_answer_twice_records_one_event(client, session_factory, player):
    body = {"games_per_week": 3, "most_ill_pay_grosze": 60_00}

    await client.put(GAMES_AND_MONEY, json=body, headers=player)
    again = await client.put(GAMES_AND_MONEY, json=body, headers=player)

    assert again.status_code == 200
    assert await events_filed(session_factory) == 1


@pytest.mark.parametrize("games", [0, 8])
async def test_a_week_outside_one_to_seven_is_refused(
    client, session_factory, player, games
):
    refused = await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": games, "most_ill_pay_grosze": None},
        headers=player,
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "games_per_week_out_of_range"
    assert refused.json()["details"] == {"least": 1, "most": 7}
    assert await events_filed(session_factory) == 0


async def test_a_ceiling_that_is_not_a_chip_is_refused(client, session_factory, player):
    refused = await client.put(
        GAMES_AND_MONEY,
        json={"games_per_week": 2, "most_ill_pay_grosze": 50_00},
        headers=player,
    )

    assert refused.status_code == 400
    assert refused.json()["code"] == "most_ill_pay_not_offered"
    assert refused.json()["details"] == {"choices": [35_00, 45_00, 60_00]}
    assert await events_filed(session_factory) == 0


async def test_both_values_are_required(client, player):
    refused = await client.put(
        GAMES_AND_MONEY, json={"games_per_week": 3}, headers=player
    )

    assert refused.status_code == 422


async def test_it_is_the_reader_s_own(client):
    assert (await client.get(GAMES_AND_MONEY)).status_code == 401
