"""The seeded payment methods, read back the way You › Payments reads them.

``app/seeds/payments.py`` saves a card for every seeded player but one **through
the setup a phone runs**, so each is asserted by signing in as the account and
reading its method — never a stream or a table.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.bootstrap.composition import build_clock
from app.seeds.catalog import (
    ACCOUNTS,
    BRAND_NEW_PLAYER,
    RATED_IN_EVERY_SPORT,
    SEED_PASSWORD,
    THE_NEWCOMER,
    THE_POPULATED_PLAYER,
    SeedAccount,
)
from app.seeds.payments import write_the_payment_methods
from app.seeds.runner import seed

A_COHORT_MEMBER = {
    "email": "cohort-member@raketa.example",
    "password1": SEED_PASSWORD,
    "password2": SEED_PASSWORD,
    "adult_attested": True,
}


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def member(client) -> str:
    signed_up = await client.post("/api/v1/users", json=A_COHORT_MEMBER)
    assert signed_up.status_code == 201, signed_up.text
    return signed_up.json()["id"]


@pytest.fixture
async def seeded(session_factory, now, member):
    async with session_factory() as session:
        await seed(session)
    return await write_the_payment_methods(
        session_factory, now=now, cohort=[("a-member", UUID(member))]
    )


async def method_of(client, email: str) -> dict | None:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200, login.text
    read = await client.get(
        "/api/v1/players/me/payment-methods/current",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert read.status_code == 200, read.text
    assert read.json()["terms_needed"] is False
    return read.json()["method"]


async def test_the_protagonist_has_the_mock_s_card_and_the_wallets_are_drawn(
    client, seeded
):
    assert await method_of(client, THE_POPULATED_PLAYER.email) == {
        "brand": "visa",
        "last_four": "4312",
        "wallet": None,
    }
    assert await method_of(client, RATED_IN_EVERY_SPORT.email) == {
        "brand": "mastercard",
        "last_four": "5454",
        "wallet": "GOOGLE_PAY",
    }
    assert await method_of(client, THE_NEWCOMER.email) == {
        "brand": "visa",
        "last_four": "1881",
        "wallet": "APPLE_PAY",
    }


async def test_everybody_else_can_say_yes_and_one_has_nothing_set_up(client, seeded):
    others: list[SeedAccount] = [
        account
        for account in ACCOUNTS
        if account not in (THE_POPULATED_PLAYER, RATED_IN_EVERY_SPORT, THE_NEWCOMER)
    ]

    assert await method_of(client, BRAND_NEW_PLAYER.email) is None
    for account in others:
        if account is not BRAND_NEW_PLAYER:
            method = await method_of(client, account.email)
            assert method is not None, account.slug
            assert method["last_four"] == "4242", account.slug
    assert (await method_of(client, A_COHORT_MEMBER["email"]))["last_four"] == "4242"


async def test_a_second_run_saves_nobody_s_twice(session_factory, now, member, seeded):
    again = await write_the_payment_methods(
        session_factory, now=now, cohort=[("a-member", UUID(member))]
    )

    assert not [method.who for method in again.methods if method.saved]
    assert [method.who for method in seeded.methods if not method.saved] == [
        BRAND_NEW_PLAYER.slug
    ]
