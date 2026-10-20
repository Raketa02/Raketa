"""Where a seed run moves its money: the fake, or the Stripe sandbox (#712).

**On the fake, nothing is new.** Each layer asks for a fake of its own from the
composition root, as it always did, and the run tells it what each phone typed
and how far each desk got on the provider's pages.

**On the sandbox, every place the seed moves money goes through the real Stripe
adapter** — ``build_stripe_payments``, one for the run and closed with it — so
the store it seeds holds customers, cards, payments and accounts Stripe knows,
and a walker sees every share held, taken or given back on its club's own
account, as in production. What a person does on a provider's own pages, the
run plays as Stripe test mode would:

- **the phone.** A card is typed into Stripe's fields on a phone and never
  reaches the backend, so the run confirms the setup server-side with the test
  PaymentMethod standing for the card it declares — the payments demand suite's
  phone, chosen by what the card does (``SANDBOX_METHODS``), so a seeded card
  pays, or declines later, as declared. Its brand, last four and wallet are the
  test card's: the sandbox has no •••• 4312;
- **the provider's onboarding pages.** A club the seed declares ready is
  connected to a sandbox account **a person has already onboarded**, named in
  ``SEED_STRIPE_CLUB_ACCOUNTS`` (``OnboardedAccounts``), and reads ready because
  Stripe says so. A club declared unfinished — Wisła Park — opens a new account
  through *Connect with Stripe* and stays as Stripe opened it.

**Refused before anything is written** (``seed_money``), naming what is
missing: a key that is not a test key; a mapping that is unset, names a club
not declared ready, leaves out one that is, or gives two clubs one account —
the store holds one club per provider account (``club_payments_accounts``);
and an account the sandbox has not enabled to take a share and pay it out.

**Two runs within the same hour stay correct.** A provider key is the act and
the hour, and Stripe answers a key it has seen with the object it made the
first time. But every id a key carries — a player, a club, a game, a charge —
is minted by the store it is written to, never chosen by the seed, so a fresh
store's run asks Stripe no key an earlier store's asked
(``tests/api/test_seed_money.py`` proves it, key by key). A re-run on the same
store asks a key again only for the same act, which is what the key is for.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Mapping
from datetime import timedelta
from types import MappingProxyType
from typing import Final, Protocol, final
from uuid import UUID

import stripe

from app.bootstrap.composition import (
    build_fake_payments,
    build_payments_accounts,
    build_stripe_payments,
)
from app.core.config import STRIPE_TEST_KEY_PREFIXES, PaymentsProvider, Settings
from app.kernel import Instant
from app.modules.clubs.domain.payments_account import OnboardingPages, PaymentsStatus
from app.modules.clubs.domain.ports import PaymentsAccounts
from app.modules.payments.domain.entered_cards import CardBehaviour, EnteredCard
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import ClubAccountStatus, PaymentProvider
from app.modules.payments.domain.seat_charge import HOLDING_LEAD

#: The variable naming the sandbox account a person onboarded for each club the
#: seed declares ready: ``Club name=acct_…`` pairs, separated by commas. Read
#: from the process environment rather than ``Settings``, like ``SEED_CENTRE``,
#: because it is the seed command's argument and never the application's
#: configuration: ``.env.docker`` supplies it to ``make seed``, and a shell
#: export to ``make seed-host``.
SEED_STRIPE_CLUB_ACCOUNTS: Final = "SEED_STRIPE_CLUB_ACCOUNTS"

#: Stripe's test PaymentMethods, by what the card does — the payments demand
#: suite's ``STRIPE_TEST_METHODS``, keyed by behaviour rather than by card,
#: because a seeded card is declared by what it does and not by Stripe's number
#: (``tests/unit/test_seed_money.py`` holds the two equal).
SANDBOX_METHODS: Final[Mapping[CardBehaviour, str]] = MappingProxyType(
    {
        CardBehaviour.SUCCEEDS: "pm_card_visa",
        CardBehaviour.DECLINED_AT_SETUP: "pm_card_visa_chargeDeclined",
        CardBehaviour.DECLINES_PAYMENTS: "pm_card_chargeCustomerFail",
        CardBehaviour.CHECKED_AT_SETUP: "pm_card_authenticationRequiredOnSetup",
        CardBehaviour.CHECKED_EVERY_TIME: "pm_card_authenticationRequired",
    }
)

#: How long a hold made without its player lasts on the sandbox: **7 days** —
#: measured on its Visa (2026-10-19), where a live Visa's lasts 4 days 18 hours,
#: which is what the fake models; a Mastercard's is 7 days live as well.
SANDBOX_HOLD_LASTS: Final = timedelta(days=7)

#: Where the bank's check would send a phone back to. Never followed: a check
#: needs a browser, so a card the bank checks cannot be seeded on either path.
_RETURN_URL: Final = "https://raketa.example/return"


class SeedMoneyRefused(RuntimeError):
    """The run cannot move its money where the settings point it — said
    before anything is written, naming what is missing. Never the key."""


class Phone(Protocol):
    """A player's phone: the provider its setups are opened on, and the card
    typed into one."""

    provider: PaymentProvider

    async def enters(self, setup_id: str, card: EnteredCard) -> None: ...


class Pages(Protocol):
    """The provider's hosted onboarding pages, as far as each seeded desk
    walks them."""

    #: The Club context's port onto the provider, as *Connect with Stripe*
    #: asks it.
    accounts: PaymentsAccounts

    async def walk(
        self,
        club_id: UUID,
        *,
        as_far_as: ClubAccountStatus,
        connect: Callable[[], Awaitable[object]],
    ) -> str | None:
        """The desk asks for the link (``connect``) and goes through the pages
        as far as declared. The account the provider's notice then names,
        where the pages left it somewhere the read after the link did not see
        — ``None`` where that read saw it all."""
        ...


class SeedMoney(Protocol):
    """Where a seed run moves its money, and the provider's two stand-ins."""

    #: The report's words for it.
    where: str
    #: How far ahead of the run the crowd's far-ahead game's cut-off is, at
    #: least: past the Holding time and past every hold this provider makes,
    #: so each of its seats is checked at the fill (#639).
    far_ahead: timedelta

    def provider(self) -> PaymentProvider:
        """What a layer moves money through."""
        ...

    def phone(self) -> Phone:
        """The phone a layer's players type their cards into."""
        ...

    def pages(self) -> Pages:
        """The onboarding pages a layer's desks walk."""
        ...

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# The fake
# ---------------------------------------------------------------------------


class _TheFake(PaymentProvider, Protocol):
    """What the run tells the fake — a phone's card and a desk's pages — and
    nothing else of it."""

    onboarding_completes: bool

    def phone_enters(self, setup_id: str, card: EnteredCard) -> None: ...

    def account_opened_for(self, club_id: UUID) -> str: ...

    def club_account_is(self, account_id: str, status: ClubAccountStatus) -> None: ...


@final
class OnTheFake:
    """The fake, as every seed run has had it: a fake of its own from the
    composition root at every ask — or, for a test, **one for the whole run**,
    which answers a key it has seen with what it made the first time, as Stripe
    does."""

    where = "fake provider"
    #: Past the Holding time by a day, so a Visa's hold on the fake — 4 days
    #: 18 hours — cannot reach it.
    far_ahead = HOLDING_LEAD + timedelta(days=1)

    def __init__(self, *, one_for_the_run: bool = False) -> None:
        self._one: _TheFake | None = build_fake_payments() if one_for_the_run else None

    def _fake(self) -> _TheFake:
        return self._one if self._one is not None else build_fake_payments()

    def provider(self) -> PaymentProvider:
        return self._fake()

    def phone(self) -> Phone:
        return _FakePhone(self._fake())

    def pages(self) -> Pages:
        return _FakePages(self._fake())

    async def close(self) -> None:
        return None


#: The fake every seed run is on unless its settings select Stripe.
THE_FAKE: Final = OnTheFake()


@final
class _FakePhone:
    """The fake is told which of its cards the phone typed."""

    def __init__(self, fake: _TheFake) -> None:
        self.provider: PaymentProvider = fake
        self._fake = fake

    async def enters(self, setup_id: str, card: EnteredCard) -> None:
        self._fake.phone_enters(setup_id, card)


@final
class _FakePages:
    """Finished in one visit for a club that is ready — the fake completes
    onboarding on the link, so the read that follows finds it ready — and left
    where declared for one that is not, which the provider's notice then
    says."""

    def __init__(self, fake: _TheFake) -> None:
        self._fake = fake
        self.accounts = build_payments_accounts(fake)

    async def walk(
        self,
        club_id: UUID,
        *,
        as_far_as: ClubAccountStatus,
        connect: Callable[[], Awaitable[object]],
    ) -> str | None:
        ready = as_far_as is ClubAccountStatus.READY
        self._fake.onboarding_completes = ready
        await connect()
        if ready:
            return None
        account = self._fake.account_opened_for(club_id)
        self._fake.club_account_is(account, as_far_as)
        return account


# ---------------------------------------------------------------------------
# The sandbox
# ---------------------------------------------------------------------------


@final
class OnTheSandbox:
    """Stripe in test mode: one adapter from the composition root for the run,
    the phone confirming setups server-side, and the ready clubs on accounts a
    person onboarded. Built by ``seed_money``, which refuses first."""

    where = "Stripe sandbox"
    #: Past the sandbox's hold by a day: a week-long hold reaches the fake's
    #: five days, and a seat whose hold reaches its cut-off is held, not
    #: checked.
    far_ahead = SANDBOX_HOLD_LASTS + timedelta(days=1)

    def __init__(self, settings: Settings, *, onboarded: Mapping[str, str]) -> None:
        self._stripe = build_stripe_payments(settings)
        self._phone = SandboxPhone(
            self._stripe,
            secret_key=settings.STRIPE_SECRET_KEY or "",
            timeout_seconds=settings.STRIPE_TIMEOUT_SECONDS,
        )
        self._onboarded = dict(onboarded)

    def provider(self) -> PaymentProvider:
        return self._stripe

    def phone(self) -> Phone:
        return self._phone

    def pages(self) -> Pages:
        return _SandboxPages(self._stripe, self._onboarded)

    async def close(self) -> None:
        await self._phone.close()
        await self._stripe.close()


@final
class SandboxPhone:
    """A phone in Stripe test mode, as the payments demand suite's: the setup
    is confirmed server-side with the test PaymentMethod standing for what the
    typed card does."""

    def __init__(
        self, provider: PaymentProvider, *, secret_key: str, timeout_seconds: float
    ) -> None:
        self.provider = provider
        self._http = stripe.AIOHTTPClient(timeout=timeout_seconds)
        self._client = stripe.StripeClient(secret_key, http_client=self._http)

    async def close(self) -> None:
        await self._http.close_async()

    async def enters(self, setup_id: str, card: EnteredCard) -> None:
        try:
            await self._client.v1.setup_intents.confirm_async(
                setup_id,
                params={
                    "payment_method": SANDBOX_METHODS[card.behaviour],
                    "return_url": _RETURN_URL,
                },
            )
        except stripe.CardError:
            # A card its bank refuses: the setup says so, and the save that
            # reads it next is refused, as a phone's is.
            pass


@final
class _SandboxPages:
    """A ready club's desk walked the pages before the run — its account is
    the one a person onboarded — and an unfinished club's desk never went, so
    Stripe says where its new account stands. Nothing to tell either way."""

    def __init__(self, provider: PaymentProvider, onboarded: Mapping[str, str]) -> None:
        self.accounts: PaymentsAccounts = OnboardedAccounts(
            build_payments_accounts(provider), onboarded
        )

    async def walk(
        self,
        club_id: UUID,
        *,
        as_far_as: ClubAccountStatus,
        connect: Callable[[], Awaitable[object]],
    ) -> str | None:
        await connect()
        return None


@final
class OnboardedAccounts:
    """The Club context's ``PaymentsAccounts`` with the provider's pages
    already walked: a club a person onboarded opens **that** account, and its
    link lands back on the club website, where Stripe's would once the pages
    are done. Any other club opens its own, and every account is read from the
    provider as it stands."""

    def __init__(
        self, accounts: PaymentsAccounts, onboarded: Mapping[str, str]
    ) -> None:
        self._accounts = accounts
        self._onboarded = dict(onboarded)

    async def open(
        self, *, club_id: UUID, name: str, email: str, asked_at: Instant
    ) -> str:
        onboarded = self._onboarded.get(name)
        if onboarded is not None:
            return onboarded
        return await self._accounts.open(
            club_id=club_id, name=name, email=email, asked_at=asked_at
        )

    async def onboarding_link(self, account_id: str, *, pages: OnboardingPages) -> str:
        if account_id in self._onboarded.values():
            return pages.return_url
        return await self._accounts.onboarding_link(account_id, pages=pages)

    async def status_of(self, account_id: str) -> PaymentsStatus:
        return await self._accounts.status_of(account_id)


# ---------------------------------------------------------------------------
# Which, refused before anything is written
# ---------------------------------------------------------------------------


async def seed_money(
    settings: Settings, environ: Mapping[str, str], *, ready: Collection[str]
) -> SeedMoney:
    """Where this run moves its money: the fake, unless the settings select
    Stripe — and then the sandbox, once every club in ``ready`` (the clubs the
    seed declares ready) has an account a person onboarded there."""

    if settings.PAYMENTS_PROVIDER == PaymentsProvider.FAKE:
        return THE_FAKE
    if not (settings.STRIPE_SECRET_KEY or "").startswith(STRIPE_TEST_KEY_PREFIXES):
        raise SeedMoneyRefused(
            "PAYMENTS_PROVIDER selects stripe, and STRIPE_SECRET_KEY is not a "
            "test key. The seed moves money only on the sandbox: a live key "
            "would charge real cards for fabricated games — place a test key "
            "(sk_test_…)."
        )
    onboarded = onboarded_accounts(environ, ready=ready)
    money = OnTheSandbox(settings, onboarded=onboarded)
    try:
        await refuse_an_account_not_ready(money.provider(), onboarded)
    except BaseException:
        await money.close()
        raise
    return money


def onboarded_accounts(
    environ: Mapping[str, str], *, ready: Collection[str]
) -> dict[str, str]:
    """Each club in ``ready`` and the sandbox account a person onboarded for
    it, read from ``SEED_STRIPE_CLUB_ACCOUNTS``. A pure function of the
    environment, refused by name."""

    raw = environ.get(SEED_STRIPE_CLUB_ACCOUNTS, "")
    if not raw.strip():
        raise SeedMoneyRefused(
            f"PAYMENTS_PROVIDER selects stripe, and {SEED_STRIPE_CLUB_ACCOUNTS} is "
            f"not set. Every club the seed declares ready is connected to a "
            f"sandbox account a person has onboarded, one each: "
            f"{', '.join(ready)}. Onboard them in Stripe's hosted pages and name "
            f"them as 'Club name=acct_…' pairs separated by commas "
            f"(backend/.env.example)."
        )
    onboarded: dict[str, str] = {}
    for pair in raw.split(","):
        if not pair.strip():
            continue
        name, equals, account = (part.strip() for part in pair.partition("="))
        if not equals or not name or not account.startswith("acct_"):
            raise SeedMoneyRefused(
                f"{SEED_STRIPE_CLUB_ACCOUNTS} must be 'Club name=acct_…' pairs "
                f"separated by commas; got {pair.strip()!r}"
            )
        if name in onboarded:
            raise SeedMoneyRefused(f"{SEED_STRIPE_CLUB_ACCOUNTS} names {name} twice")
        onboarded[name] = account
    unknown = [name for name in onboarded if name not in ready]
    if unknown:
        raise SeedMoneyRefused(
            f"{SEED_STRIPE_CLUB_ACCOUNTS} names {', '.join(unknown)}, which the "
            f"seed does not declare ready. The clubs it does: {', '.join(ready)}."
        )
    missing = [name for name in ready if name not in onboarded]
    if missing:
        raise SeedMoneyRefused(
            f"The seed declares {', '.join(missing)} ready, and "
            f"{SEED_STRIPE_CLUB_ACCOUNTS} names no sandbox account for "
            f"{'it' if len(missing) == 1 else 'them'}. Onboard one per club in "
            f"Stripe's hosted pages and add it."
        )
    clubs_of: dict[str, list[str]] = {}
    for name, account in onboarded.items():
        clubs_of.setdefault(account, []).append(name)
    for account, clubs in clubs_of.items():
        if len(clubs) > 1:
            raise SeedMoneyRefused(
                f"{', '.join(clubs[:-1])} and {clubs[-1]} share {account}. The "
                f"store holds one club "
                f"per provider account (club_payments_accounts), so every ready "
                f"club needs a sandbox account of its own."
            )
    return onboarded


async def refuse_an_account_not_ready(
    provider: PaymentProvider, onboarded: Mapping[str, str]
) -> None:
    """Refuse an onboarded account the provider says cannot take a share and
    pay it out — a club on it would never read ready."""

    for club, account in onboarded.items():
        try:
            reading = await provider.read_club_account(account)
        except (PaymentsUnavailable, stripe.StripeError) as unread:
            raise SeedMoneyRefused(
                f"{club}'s account {account} could not be read on the sandbox "
                f"({type(unread.__cause__ or unread).__name__}): is it an "
                f"account of this platform, in test mode?"
            ) from unread
        not_enabled = [
            what
            for what, enabled in (
                ("charges", reading.charges_enabled),
                ("payouts", reading.payouts_enabled),
            )
            if not enabled
        ]
        if not_enabled:
            raise SeedMoneyRefused(
                f"{club}'s account {account} is not ready on the sandbox: its "
                f"{' and '.join(not_enabled)} are not enabled. Finish its "
                f"onboarding in Stripe's hosted pages, or name an account that "
                f"has."
            )
