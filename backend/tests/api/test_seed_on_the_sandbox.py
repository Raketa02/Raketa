"""The seed on the Stripe sandbox, asked of Stripe itself (#712).

**Covered like the payments demand suite**: nothing here runs unless a person
placed Stripe **test** keys (#533) **and** ``SEED_STRIPE_CLUB_ACCOUNTS`` —
skipped by name otherwise, so a ``make test`` with keys in ``.env`` leaves the
sandbox to the demand suite. The keys are read from the settings, as the
demand suite reads them; the mapping from the shell, as ``make seed-host``
reads it, and only the tests that seed the clubs need it to name seven
onboarded accounts::

    SEED_STRIPE_CLUB_ACCOUNTS='Ogrody 33=acct_…,…' \\
        poetry run pytest tests/api/test_seed_on_the_sandbox.py

**Every run leaves objects in the sandbox**, as the demand suite's does: a
customer and a card per seeded player, an account for a club the run opens,
and — the whole seed, twice — every seeded share on its club's account.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_payment_method_repository,
    build_seat_charge_repository,
)
from app.core.config import (
    STRIPE_TEST_KEY_PREFIXES,
    PaymentsProvider,
    Settings,
    get_settings,
)
from app.infrastructure.database.base import Base
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    A_CARD_THAT_DECLINES_LATER,
    A_CARD_THE_BANK_DECLINES,
)
from app.modules.payments.domain.provider import (
    AWAITING_THE_PLAYER,
    PaymentProvider,
    PaymentStatus,
    SetupStatus,
)
from app.modules.payments.domain.seat_charge import SeatCharge, SeatChargeStatus
from app.modules.payments.infrastructure.event_sourced_seat_charge_repository import (  # noqa: E501
    SEAT_CHARGE_AGGREGATE,
)
from app.modules.payments.presentation.dependencies import get_payment_provider
from app.seeds.catalog import ACCOUNTS, BRAND_NEW_PLAYER, SEED_PASSWORD
from app.seeds.club_courts import (
    SEED_CLUB_COURTS,
    declared_ready,
    write_the_club_courts,
)
from app.seeds.clubs import SEED_CLUBS, desk_email, write_the_clubs
from app.seeds.money import (
    SEED_STRIPE_CLUB_ACCOUNTS,
    OnTheSandbox,
    SeedMoneyRefused,
    onboarded_accounts,
    refuse_an_account_not_ready,
    seed_money,
)
from app.seeds.payments import write_the_payment_methods
from app.seeds.runner import seed
from app.shared.ids import new_uuid
from tests.api.proposals_world import PAYMENT_METHODS, TERMS_IN_FORCE
from tests.api.club_courts_world import SETUP
from tests.api.test_clubs import SIGN_IN, bearer

ROOT = Path(__file__).resolve().parents[2]


def _with_test_keys() -> Settings:
    settings = get_settings()
    if not (settings.STRIPE_SECRET_KEY or "").startswith(STRIPE_TEST_KEY_PREFIXES):
        pytest.skip(
            "no Stripe test key is placed — STRIPE_SECRET_KEY must start with "
            f"{' or '.join(STRIPE_TEST_KEY_PREFIXES)} (#533)"
        )
    return settings.model_copy(update={"PAYMENTS_PROVIDER": PaymentsProvider.STRIPE})


def _the_mapping() -> str:
    mapping = os.environ.get(SEED_STRIPE_CLUB_ACCOUNTS, "")
    if not mapping.strip():
        pytest.skip(
            f"{SEED_STRIPE_CLUB_ACCOUNTS} names no onboarded sandbox account per "
            "ready club (#712)"
        )
    return mapping


@pytest.fixture
def on_stripe() -> Settings:
    settings = _with_test_keys()
    _the_mapping()
    return settings


@pytest.fixture
async def sandbox(on_stripe):
    """The run's money on the sandbox, with no club onboarded."""

    money = OnTheSandbox(on_stripe, onboarded={})
    yield money
    await money.close()


@pytest.fixture
async def onboarded(on_stripe):
    """The run's money on the sandbox, every ready club on the account a
    person onboarded for it — refused as ``make seed`` refuses."""

    money = await seed_money(on_stripe, os.environ, ready=declared_ready())
    yield money
    await money.close()


# ---------------------------------------------------------------------------
# The phone, and every seeded player's card (test keys)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("card", "status", "last_four"),
    [
        (A_CARD, SetupStatus.SUCCEEDED, "4242"),
        (A_CARD_THAT_DECLINES_LATER, SetupStatus.SUCCEEDED, "0341"),
        (A_CARD_THE_BANK_DECLINES, SetupStatus.DECLINED, None),
    ],
    ids=["pays", "declines-later", "declined"],
)
async def test_the_phone_types_stripe_s_test_card_for_what_the_card_does(
    sandbox, card, status, last_four
):
    provider = sandbox.provider()
    player = new_uuid()
    customer = await provider.open_customer(
        player_id=player, idempotency_key=f"rakieta-seed-test-{new_uuid()}"
    )
    setup = await provider.start_setup(
        customer_id=customer,
        player_id=player,
        idempotency_key=f"rakieta-seed-test-{new_uuid()}",
    )

    await sandbox.phone().enters(setup.setup_id, card)
    reading = await provider.read_setup(setup.setup_id)

    assert reading.status is status
    assert (reading.card.last_four if reading.card else None) == last_four


async def test_every_seeded_player_saves_a_card_stripe_knows(sandbox, session_factory):
    async with session_factory() as session:
        await seed(session)

    seeded = await write_the_payment_methods(
        session_factory, now=build_clock().now(), cohort=[], money=sandbox
    )

    assert seeded.where == "Stripe sandbox"
    with_one = [method for method in seeded.methods if method.card is not None]
    assert {method.who for method in seeded.methods} - {
        method.who for method in with_one
    } == {BRAND_NEW_PLAYER.slug}
    async with session_factory() as session:
        methods = build_payment_method_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        )
        for method in with_one:
            saved = await methods.load(method.player_id)
            assert saved.customer_id and saved.customer_id.startswith("cus_")
            assert saved.method is not None
            assert "_fake_" not in saved.method.method_id
            card = await sandbox.provider().read_card(saved.method.method_id)
            assert (card.brand, card.last_four) == ("visa", "4242"), method.who


async def test_a_seeded_player_changes_and_removes_their_card_on_stripe(
    app, client, sandbox, session_factory
):
    """**Change and Remove work after the seed**, which a store seeded on the
    fake never could: its customer was the fake's, which Stripe refuses."""

    async with session_factory() as session:
        await seed(session)
    await write_the_payment_methods(
        session_factory, now=build_clock().now(), cohort=[], money=sandbox
    )
    app.dependency_overrides[get_payment_provider] = sandbox.provider
    them = next(account for account in ACCOUNTS if account is not BRAND_NEW_PLAYER)
    login = await client.post(
        "/api/v1/auth/login", json={"email": them.email, "password": SEED_PASSWORD}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    started = await client.post(f"{PAYMENT_METHODS}/setup", headers=headers)
    assert started.status_code == 201, started.text
    await sandbox.phone().enters(started.json()["setup_id"], A_CARD_THAT_DECLINES_LATER)
    accepted = await client.post(
        f"{PAYMENT_METHODS}/terms",
        json={"terms_version": TERMS_IN_FORCE},
        headers=headers,
    )
    assert accepted.status_code == 200, accepted.text
    confirmed = await client.post(f"{PAYMENT_METHODS}/confirmation", headers=headers)
    assert confirmed.status_code == 200, confirmed.text
    changed = await client.get(f"{PAYMENT_METHODS}/current", headers=headers)
    removed = await client.delete(f"{PAYMENT_METHODS}/current", headers=headers)
    after = await client.get(f"{PAYMENT_METHODS}/current", headers=headers)

    assert changed.json()["method"]["last_four"] == "0341"
    assert removed.status_code in (200, 204), removed.text
    assert after.json()["method"] is None


# ---------------------------------------------------------------------------
# An account the sandbox has not enabled (test keys)
# ---------------------------------------------------------------------------


async def test_an_account_nobody_onboarded_is_refused_by_name(sandbox):
    provider = sandbox.provider()
    unfinished = await provider.open_club_account(
        club_id=new_uuid(),
        name="Ogrody 33",
        email="desk@rakieta.example",
        idempotency_key=f"rakieta-seed-test-{new_uuid()}",
    )

    with pytest.raises(SeedMoneyRefused) as refused:
        await refuse_an_account_not_ready(provider, {"Ogrody 33": unfinished})

    assert str(refused.value).startswith(
        f"Ogrody 33's account {unfinished} is not ready on the sandbox: its charges"
    )


async def test_an_account_of_no_platform_is_refused_by_name(sandbox):
    with pytest.raises(SeedMoneyRefused, match="could not be read on the sandbox"):
        await refuse_an_account_not_ready(
            sandbox.provider(), {"Ogrody 33": "acct_1NoSuchAccount000000"}
        )


# ---------------------------------------------------------------------------
# The ready clubs, and the whole seed (test keys and the mapping)
# ---------------------------------------------------------------------------


async def test_every_ready_club_reads_ready_from_its_own_sandbox_account(
    client, onboarded, session_factory
):
    """A ready club's desk reads *ready* on its Overview because Stripe says
    its onboarded account is; Wisła Park's new account is *not started*."""

    now = build_clock().now()
    clubs = await write_the_clubs(session_factory, settings=get_settings(), now=now)

    await write_the_club_courts(
        session_factory, settings=get_settings(), now=now, clubs=clubs, money=onboarded
    )

    read = {}
    for club in SEED_CLUBS:
        signed_in = await client.post(
            SIGN_IN, json={"email": desk_email(club), "password": SEED_PASSWORD}
        )
        assert signed_in.status_code == 200, signed_in.text
        setup = await client.get(SETUP, headers=bearer(signed_in.json()))
        read[club.name] = setup.json()["payments"]
    assert read == {
        entry.club: ("READY" if entry.club in declared_ready() else "NOT_STARTED")
        for entry in SEED_CLUB_COURTS
    }


#: What Stripe says of a share's payment, by where its stream leaves it once
#: the seed's outbox is drained: a share held is a hold, one taken is captured
#: — a refund leaves its payment captured — and one let go, or checked and let
#: go, is cancelled.
ON_STRIPE = {
    SeatChargeStatus.AUTHORISED: {PaymentStatus.AUTHORISED},
    SeatChargeStatus.HELD: {PaymentStatus.AUTHORISED},
    SeatChargeStatus.TAKING: {PaymentStatus.CAPTURED},
    SeatChargeStatus.CAPTURED: {PaymentStatus.CAPTURED},
    SeatChargeStatus.RELEASING: {PaymentStatus.CANCELLED},
    SeatChargeStatus.CANCELLED: {PaymentStatus.CANCELLED},
    SeatChargeStatus.CHECKED: {PaymentStatus.CANCELLED},
    SeatChargeStatus.FAILED: set(AWAITING_THE_PLAYER),
}


async def the_store_s_money(url: str) -> tuple[list[str], list[SeatCharge]]:
    """Every event's payload, as text, and every seat charge as its stream
    leaves it."""

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with factory() as session:
            rows = (
                await session.execute(
                    select(
                        EventStoreORM.aggregate_type,
                        EventStoreORM.aggregate_id,
                        EventStoreORM.payload,
                    )
                )
            ).all()
            charges = build_seat_charge_repository(
                session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            )
            loaded = [
                await charges.load(charge_id)
                for charge_id in sorted(
                    {
                        row.aggregate_id
                        for row in rows
                        if row.aggregate_type == SEAT_CHARGE_AGGREGATE
                    }
                )
            ]
    finally:
        await engine.dispose()
    return [str(row.payload) for row in rows], [c for c in loaded if c is not None]


async def assert_the_store_s_money_is_stripe_s(
    url: str, provider: PaymentProvider, accounts: set[str]
) -> list[SeatCharge]:
    """**No id in the store is the fake's**, and every seeded share is a
    payment on its club's account that Stripe holds, took or let go as the
    store says."""

    payloads, charges = await the_store_s_money(url)
    assert not [payload for payload in payloads if "_fake_" in payload]
    assert charges
    for charge in charges:
        assert charge.account_id in accounts, charge.charge_id
        assert charge.payment_id is not None, charge.charge_id
        payment = await provider.read_payment(
            account_id=charge.account_id, payment_id=charge.payment_id
        )
        assert payment.status in ON_STRIPE[charge.status], (
            charge.charge_id,
            charge.status,
            payment.status,
        )
    return charges


async def a_fresh_store(tmp_path: Path, name: str) -> str:
    url = f"sqlite+aiosqlite:///{tmp_path / name}.db"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    return url


async def test_make_seed_on_the_sandbox_twice_within_the_hour(
    tmp_path, onboarded, on_stripe
):
    """``python -m app.seeds`` on Stripe, into two fresh stores, one after the
    other — ``make down-v``, ``make up``, ``make seed``, twice. Both runs
    finish, and each store's money is Stripe's: no customer, card, payment or
    account of the fake's, and every share held, taken or let go on its club's
    own account as the store says — and the second store holds none of the
    first's payments. Minutes, not seconds."""

    def environment(url: str) -> dict[str, str]:
        return {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "PYTHONPATH": str(ROOT),
            "APP_ENV": "local",
            "JWT_SECRET_KEY": "test-secret-do-not-use-in-prod",
            "WRITER_DB_URL": url,
            "DB_SSL_MODE": "disable",
            "BCRYPT_ROUNDS": "4",
            "PAYMENTS_PROVIDER": "stripe",
            "STRIPE_SECRET_KEY": on_stripe.STRIPE_SECRET_KEY or "",
            "STRIPE_PUBLISHABLE_KEY": on_stripe.STRIPE_PUBLISHABLE_KEY or "",
            SEED_STRIPE_CLUB_ACCOUNTS: _the_mapping(),
        }

    accounts = set(onboarded_accounts(os.environ, ready=declared_ready()).values())
    payments: list[set[str | None]] = []
    for name in ("first", "second"):
        url = await a_fresh_store(tmp_path, name)
        seeded = subprocess.run(
            [sys.executable, "-m", "app.seeds"],
            cwd=ROOT,
            env=environment(url),
            capture_output=True,
            text=True,
            timeout=1800,
        )
        assert seeded.returncode == 0, seeded.stderr[-4000:]
        assert "Payment methods (Stripe sandbox)" in seeded.stdout
        charges = await assert_the_store_s_money_is_stripe_s(
            url, onboarded.provider(), accounts
        )
        payments.append({charge.payment_id for charge in charges})
    assert payments[0].isdisjoint(payments[1])
