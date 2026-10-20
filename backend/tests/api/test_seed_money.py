"""The seed's money across two runs, and on holds that last a week (#712).

``app/seeds/money.py`` moves a run's money through one provider. Three claims
need a database, and none needs Stripe:

- **two fresh stores seeded within the same hour ask the provider no key in
  common.** Stripe answers a key it has seen with what it made the first time,
  and a key is the act and the hour — so a second store's run would be handed
  the first's customers, cards and payments if any id a key carries were the
  seed's own choice. The proof is the whole run, twice, at one instant, through
  one fake that keeps every key it was asked, as Stripe does;
- **on the sandbox's week-long holds the crowd's far-ahead game is still
  checked** (#639), because the run looks a week past the hold, not five days;
- **a sandbox run that is refused writes nothing**.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.bootstrap.composition import build_clock
from app.core.config import PaymentsProvider, get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.domain.seat_charge import HOLDING_LEAD
from app.seeds.bookings import NotEnoughToBook, book_her_games
from app.seeds.club_courts import write_the_club_courts
from app.seeds.clock import FixedClock
from app.seeds.clubs import write_the_clubs
from app.seeds.money import (
    SANDBOX_HOLD_LASTS,
    SEED_STRIPE_CLUB_ACCOUNTS,
    OnTheFake,
    OnTheSandbox,
    Pages,
    Phone,
    SeedMoneyRefused,
)
from app.seeds.payments import write_the_payment_methods
from app.seeds.runner import run, seed
from tests.api.test_seed_proposals import seeded_world

#: The keys that carry the hour they were asked in, which is what makes a
#: second run within it the danger: each must have been asked, or the proof
#: below proves nothing about it.
KEYS_OF_THE_HOUR = (
    "raketa-customer-",
    "raketa-setup-",
    "raketa-club-account-",
    "raketa-seat-",
)


@pytest.fixture
def now():
    return build_clock().now()


@pytest.fixture
async def under_it(session_factory, now):
    """The named accounts, the clubs selling courts, and the cards."""

    async with session_factory() as session:
        await seed(session)
    clubs = await write_the_clubs(session_factory, settings=get_settings(), now=now)
    await write_the_club_courts(
        session_factory, settings=get_settings(), now=now, clubs=clubs
    )
    await write_the_payment_methods(session_factory, now=now, cohort=[])


async def a_fresh_store(tmp_path, name: str):
    """A database on disk with the schema a migration leaves, and the settings
    that write to it."""

    url = f"sqlite+aiosqlite:///{tmp_path / name}.db"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    return url, get_settings().model_copy(update={"WRITER_DB_URL": url})


def keys_asked(provider: PaymentProvider) -> list[str]:
    return [
        call.arguments["key"]
        for call in provider.calls  # type: ignore[attr-defined]
        if "key" in call.arguments
    ]


# ---------------------------------------------------------------------------
# Two runs within the same hour
# ---------------------------------------------------------------------------


async def test_a_fresh_store_s_run_asks_no_key_an_earlier_store_s_asked(
    tmp_path, monkeypatch
):
    """**Every id a key carries is the store's, not the seed's**: a player, a
    club, a game and a charge are minted where they are written. So a store
    reset and seeded again within the hour asks the sandbox nothing it will
    answer with the first store's objects — and the fake, kept across both
    runs as Stripe keeps its keys, would have refused one asked again with
    other arguments and failed the second run."""

    stopped = FixedClock(at=build_clock().now())
    monkeypatch.setattr("app.seeds.runner.build_clock", lambda: stopped)
    money = OnTheFake(one_for_the_run=True)
    provider = money.provider()

    _, first_store = await a_fresh_store(tmp_path, "first")
    await run(first_store, money=money)
    first = keys_asked(provider)
    _, second_store = await a_fresh_store(tmp_path, "second")
    await run(second_store, money=money)
    second = keys_asked(provider)[len(first) :]

    for kind in KEYS_OF_THE_HOUR:
        assert any(key.startswith(kind) for key in first), kind
        assert any(key.startswith(kind) for key in second), kind
    assert set(first).isdisjoint(second)


# ---------------------------------------------------------------------------
# Holds that last a week, as the sandbox's do
# ---------------------------------------------------------------------------


class WeekLongHolds:
    """The sandbox's holds, played by one fake for the run: 7 days on every
    network, where a live Visa's last 4 days 18 hours. ``far_ahead`` is the
    run's look past them — the sandbox's own unless a test says otherwise."""

    where = OnTheSandbox.where

    def __init__(self, *, far_ahead: timedelta = OnTheSandbox.far_ahead) -> None:
        self.far_ahead = far_ahead
        self._fake = OnTheFake(one_for_the_run=True)
        self._fake.provider().hold_windows = {  # type: ignore[attr-defined]
            "visa": SANDBOX_HOLD_LASTS,
            "mastercard": SANDBOX_HOLD_LASTS,
        }

    def provider(self) -> PaymentProvider:
        return self._fake.provider()

    def phone(self) -> Phone:
        return self._fake.phone()

    def pages(self) -> Pages:
        return self._fake.pages()

    async def close(self) -> None:
        return None


async def test_on_week_long_holds_the_crowd_s_far_ahead_game_is_still_checked(
    client, session_factory, payments, now, under_it
):
    _, proposals = await seeded_world(client, session_factory, payments, now)

    seeded = await book_her_games(
        session_factory,
        settings=get_settings(),
        now=now,
        seeded=proposals,
        money=WeekLongHolds(),
    )

    far = seeded.far_ahead
    assert far is not None and far.made
    assert far.checked == 4
    assert far.hold_at is not None
    assert far.hold_at >= now + OnTheSandbox.far_ahead - HOLDING_LEAD


async def test_the_fake_s_five_days_would_hold_a_week_long_hold_unchecked(
    client, session_factory, payments, now, under_it
):
    """Why the sandbox looks further: a week-long hold reaches a cut-off five
    days off, so the game would be held and nothing checked."""

    _, proposals = await seeded_world(client, session_factory, payments, now)

    with pytest.raises(NotEnoughToBook, match="booked far ahead with no seat checked"):
        await book_her_games(
            session_factory,
            settings=get_settings(),
            now=now,
            seeded=proposals,
            money=WeekLongHolds(far_ahead=OnTheFake.far_ahead),
        )


# ---------------------------------------------------------------------------
# Refused before anything is written
# ---------------------------------------------------------------------------


async def test_a_refused_sandbox_run_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv(SEED_STRIPE_CLUB_ACCOUNTS, raising=False)
    url, settings = await a_fresh_store(tmp_path, "refused")
    on_stripe = settings.model_copy(
        update={
            "PAYMENTS_PROVIDER": PaymentsProvider.STRIPE,
            "STRIPE_SECRET_KEY": "sk_test_never_sent",
            "STRIPE_PUBLISHABLE_KEY": "pk_test_never_sent",
        }
    )

    with pytest.raises(
        SeedMoneyRefused, match=f"{SEED_STRIPE_CLUB_ACCOUNTS} is not set"
    ):
        await run(on_stripe)

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        written = await conn.scalar(select(func.count()).select_from(EventStoreORM))
    await engine.dispose()
    assert written == 0
