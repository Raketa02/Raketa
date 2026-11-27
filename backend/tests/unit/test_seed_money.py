"""Where a seed run moves its money, and what it refuses before writing (#712).

``app/seeds/money.py`` puts the seed on the fake or on the Stripe sandbox. What
can be asked without a network or a database is asked here: the phone's test
cards are the demand suite's, the mapping of clubs to onboarded accounts is
read and refused by name, a key that is not a test key is refused, an account
that cannot take a share is refused, and a club a person onboarded opens that
account without asking Stripe for another. The sandbox itself is asked in
``tests/api/test_seed_on_the_sandbox.py``, where a person placed test keys.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.bootstrap.composition import build_payments_accounts
from app.core.config import get_settings
from app.kernel import instant
from app.modules.clubs.domain.payments_account import OnboardingPages, PaymentsStatus
from app.modules.payments.domain.entered_cards import CardBehaviour
from app.modules.payments.domain.provider import ClubAccountStatus
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.seeds.club_courts import SEED_CLUB_COURTS, declared_ready
from app.seeds.money import (
    SANDBOX_METHODS,
    SEED_STRIPE_CLUB_ACCOUNTS,
    THE_FAKE,
    OnboardedAccounts,
    SeedMoneyRefused,
    onboarded_accounts,
    refuse_an_account_not_ready,
    seed_money,
)
from tests.demands.test_payments_demands import STRIPE_TEST_METHODS

ROOT = Path(__file__).resolve().parents[2]

READY = ("Ogrody 33", "Prądnik Tennis", "Zabłocie Sport")

PAGES = OnboardingPages("https://club.rakieta.example")

NOW = instant(datetime(2026, 10, 20, 9, tzinfo=timezone.utc))


def on_stripe(key: str):
    """The settings with Stripe selected over ``key``, unvalidated: a live
    key is refused by ``Settings`` itself off production, and the seed's own
    refusal is what is asked here."""

    return get_settings().model_copy(
        update={
            "PAYMENTS_PROVIDER": "stripe",
            "STRIPE_SECRET_KEY": key,
            "STRIPE_PUBLISHABLE_KEY": "pk_test_seed",
        }
    )


# ---------------------------------------------------------------------------
# The phone types the demand suite's test cards
# ---------------------------------------------------------------------------


def test_the_seed_confirms_each_card_with_the_demand_suite_s_test_method():
    """**The two copies are one mapping**: the demand suite's, keyed by card,
    is the seed's keyed by what the card does — one card per behaviour."""

    by_behaviour = {
        card.behaviour: method for card, method in STRIPE_TEST_METHODS.items()
    }

    assert len(by_behaviour) == len(STRIPE_TEST_METHODS)
    assert set(by_behaviour) == set(CardBehaviour)
    assert dict(SANDBOX_METHODS) == by_behaviour


# ---------------------------------------------------------------------------
# The mapping, read and refused by name
# ---------------------------------------------------------------------------


def test_the_ready_clubs_are_the_seven_the_ticket_names():
    assert declared_ready() == (
        "Ogrody 33",
        "Centrum Ruchu",
        "Kazimierz Padel",
        "Bonarka Arena",
        "Zabłocie Sport",
        "Prądnik Tennis",
        "Nowa Huta Squash",
    )
    assert {entry.club for entry in SEED_CLUB_COURTS} - set(declared_ready()) == {
        "Wisła Park"
    }


def test_each_ready_club_is_read_with_its_own_account():
    environ = {
        SEED_STRIPE_CLUB_ACCOUNTS: (
            " Ogrody 33=acct_1Ogrody , Prądnik Tennis = acct_1Pradnik,"
            "Zabłocie Sport=acct_1Zablocie,"
        )
    }

    assert onboarded_accounts(environ, ready=READY) == {
        "Ogrody 33": "acct_1Ogrody",
        "Prądnik Tennis": "acct_1Pradnik",
        "Zabłocie Sport": "acct_1Zablocie",
    }


@pytest.mark.parametrize("raw", [None, "", "  "])
def test_stripe_without_the_mapping_is_refused_naming_every_ready_club(raw):
    environ = {} if raw is None else {SEED_STRIPE_CLUB_ACCOUNTS: raw}

    with pytest.raises(SeedMoneyRefused) as refused:
        onboarded_accounts(environ, ready=READY)

    assert SEED_STRIPE_CLUB_ACCOUNTS in str(refused.value)
    assert "Ogrody 33, Prądnik Tennis, Zabłocie Sport" in str(refused.value)


@pytest.mark.parametrize(
    "raw", ["Ogrody 33", "Ogrody 33=", "=acct_1Ogrody", "Ogrody 33=1Ogrody"]
)
def test_a_pair_that_is_not_a_club_and_an_account_is_refused(raw):
    with pytest.raises(SeedMoneyRefused, match="'Club name=acct_…' pairs"):
        onboarded_accounts({SEED_STRIPE_CLUB_ACCOUNTS: raw}, ready=READY)


def test_a_ready_club_with_no_account_is_refused_by_name():
    environ = {
        SEED_STRIPE_CLUB_ACCOUNTS: "Ogrody 33=acct_1Ogrody,Zabłocie Sport=acct_1Z"
    }

    with pytest.raises(SeedMoneyRefused) as refused:
        onboarded_accounts(environ, ready=READY)

    assert str(refused.value).startswith(
        "The seed declares Prądnik Tennis ready, and SEED_STRIPE_CLUB_ACCOUNTS "
        "names no sandbox account for it."
    )


def test_a_club_not_declared_ready_is_refused_rather_than_connected():
    """Wisła Park is declared unfinished, and a typo is a club nobody seeds:
    either way an account named for it would be connected to nothing, or to
    the wrong club."""

    environ = {
        SEED_STRIPE_CLUB_ACCOUNTS: (
            "Ogrody 33=acct_1O,Prądnik Tennis=acct_1P,Zabłocie Sport=acct_1Z,"
            "Wisła Park=acct_1W"
        )
    }

    with pytest.raises(SeedMoneyRefused, match="names Wisła Park, which the seed"):
        onboarded_accounts(environ, ready=READY)


def test_two_clubs_on_one_account_are_refused():
    """**A store holds one club per provider account**: the account is the
    primary key of ``club_payments_accounts``, so the second club's connect
    would fail half way through the run."""

    environ = {
        SEED_STRIPE_CLUB_ACCOUNTS: (
            "Ogrody 33=acct_1Shared,Prądnik Tennis=acct_1P,Zabłocie Sport=acct_1Shared"
        )
    }

    with pytest.raises(SeedMoneyRefused) as refused:
        onboarded_accounts(environ, ready=READY)

    assert str(refused.value).startswith(
        "Ogrody 33 and Zabłocie Sport share acct_1Shared."
    )


def test_a_club_named_twice_is_refused():
    environ = {SEED_STRIPE_CLUB_ACCOUNTS: "Ogrody 33=acct_1A,Ogrody 33=acct_1B"}

    with pytest.raises(SeedMoneyRefused, match="names Ogrody 33 twice"):
        onboarded_accounts(environ, ready=READY)


# ---------------------------------------------------------------------------
# Which money, refused before anything is written
# ---------------------------------------------------------------------------


async def test_on_the_fake_the_seed_reads_no_mapping():
    settings = get_settings().model_copy(update={"PAYMENTS_PROVIDER": "fake"})

    assert await seed_money(settings, {}, ready=READY) is THE_FAKE


@pytest.mark.parametrize("key", ["sk_live_abcdef", "rk_live_abcdef", "", "nonsense"])
async def test_a_key_that_is_not_a_test_key_is_refused_and_never_printed(key):
    with pytest.raises(SeedMoneyRefused) as refused:
        await seed_money(on_stripe(key), {}, ready=READY)

    assert "STRIPE_SECRET_KEY is not a test key" in str(refused.value)
    assert not key or key not in str(refused.value)


async def test_stripe_without_the_mapping_is_refused_before_stripe_is_asked():
    """The mapping is read first, so a missing one costs no request."""

    with pytest.raises(
        SeedMoneyRefused, match=f"{SEED_STRIPE_CLUB_ACCOUNTS} is not set"
    ):
        await seed_money(on_stripe("sk_test_never_sent"), {}, ready=READY)


async def test_an_account_that_cannot_take_a_share_is_refused():
    fake = FakePayments()
    ready = await fake.open_club_account(
        club_id=uuid4(),
        name="Ogrody 33",
        email="desk@rakieta.example",
        idempotency_key="a",
    )
    fake.club_account_is(ready, ClubAccountStatus.READY)
    unfinished = await fake.open_club_account(
        club_id=uuid4(),
        name="Prądnik Tennis",
        email="desk@rakieta.example",
        idempotency_key="b",
    )
    fake.club_account_is(unfinished, ClubAccountStatus.NEEDS_DETAILS)

    await refuse_an_account_not_ready(fake, {"Ogrody 33": ready})
    with pytest.raises(SeedMoneyRefused) as refused:
        await refuse_an_account_not_ready(
            fake, {"Ogrody 33": ready, "Prądnik Tennis": unfinished}
        )

    assert str(refused.value).startswith(
        f"Prądnik Tennis's account {unfinished} is not ready on the sandbox: its "
        f"charges and payouts are not enabled."
    )


# ---------------------------------------------------------------------------
# The provider's onboarding pages, walked by a person before the run
# ---------------------------------------------------------------------------


async def test_a_club_a_person_onboarded_opens_that_account_and_asks_for_no_other():
    fake = FakePayments()
    accounts = OnboardedAccounts(
        build_payments_accounts(fake), {"Ogrody 33": "acct_1O"}
    )

    opened = await accounts.open(
        club_id=uuid4(), name="Ogrody 33", email="desk@rakieta.example", asked_at=NOW
    )
    link = await accounts.onboarding_link(opened, pages=PAGES)

    assert opened == "acct_1O"
    assert link == PAGES.return_url
    assert fake.calls == []


async def test_any_other_club_opens_its_own_and_every_account_is_read_as_it_stands():
    fake = FakePayments()
    accounts = OnboardedAccounts(
        build_payments_accounts(fake), {"Ogrody 33": "acct_1O"}
    )
    club_id = uuid4()

    opened = await accounts.open(
        club_id=club_id, name="Wisła Park", email="desk@rakieta.example", asked_at=NOW
    )
    link = await accounts.onboarding_link(opened, pages=PAGES)

    assert opened == fake.account_opened_for(club_id)
    assert link != PAGES.return_url
    assert await accounts.status_of(opened) is PaymentsStatus.NOT_STARTED
    fake.club_account_is(opened, ClubAccountStatus.READY)
    assert await accounts.status_of(opened) is PaymentsStatus.READY


# ---------------------------------------------------------------------------
# Every layer moves its money through the run's
# ---------------------------------------------------------------------------


def test_no_layer_builds_a_provider_of_its_own():
    """**One place says which provider**: a layer that built its own fake
    would seed fake ids into a store on the sandbox, which Stripe refuses for
    ever after. Only ``money.py`` names a builder."""

    builders = {
        "build_fake_payments",
        "build_stripe_payments",
        "build_payment_provider",
    }
    naming = {
        path.name
        for path in (ROOT / "app" / "seeds").glob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Name | ast.alias)
        and (node.id if isinstance(node, ast.Name) else node.name) in builders
    }

    assert naming == {"money.py"}


def falls_back_to_the_fake(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    """The parameters of ``function`` whose default is ``THE_FAKE``."""

    arguments = function.args
    defaulted = [
        *zip(
            arguments.args[len(arguments.args) - len(arguments.defaults) :],
            arguments.defaults,
            strict=True,
        ),
        *zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True),
    ]
    return {
        argument.arg
        for argument, default in defaulted
        if isinstance(default, ast.Name) and default.id == "THE_FAKE"
    }


def test_every_layer_is_handed_the_run_s_money():
    """**A layer not handed the run's money falls back to the fake** — the
    default is there so a test can call one layer alone — and on the sandbox
    that layer would seed fake ids into a store Stripe then refuses. So inside
    the package every call to a function whose ``money`` defaults to the fake
    passes it. (``run`` is not one: unhanded, it chooses from the settings.)"""

    trees = {
        path.name: ast.parse(path.read_text(encoding="utf-8"))
        for path in (ROOT / "app" / "seeds").glob("*.py")
    }
    takes_money = {
        node.name
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and "money" in falls_back_to_the_fake(node)
    }
    forgetting = [
        f"{name}:{node.lineno} {node.func.id}"
        for name, tree in trees.items()
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in takes_money
        and not any(keyword.arg == "money" for keyword in node.keywords)
        and not any(
            isinstance(arg, ast.Name) and arg.id == "money" for arg in node.args
        )
    ]

    assert takes_money >= {
        "write_the_payment_methods",
        "write_the_club_courts",
        "write_the_played_history",
        "write_the_proposals",
        "book_her_games",
        "seed_the_rescues",
        "open_the_rooms",
        "deliver_everything_told",
    }
    assert forgetting == []
