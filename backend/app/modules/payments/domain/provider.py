"""The payment provider: the one port money moves through (``docs/adr/0189`` §4).

**Two adapters and no third**: Stripe (test mode now, live later) and an
in-process fake that local runs, seeds and tests use. Which one a process holds
is configuration, chosen once in the composition root, and nothing that calls
this port can tell them apart — which is why the **demands** in
``tests/demands/test_payments_demands.py`` run against both.

**It speaks in Raketa's words, never in Stripe's objects.** A saved card is a
``CardOnFile``, a hold is an ``AUTHORISED`` payment and a SetupIntent is a
*setup*; the Stripe adapter translates at its own edge. Money is **integer
grosze** in and out (``docs/value-formatting.md``) and always złoty, so no
currency crosses.

**Three parties, three kinds of call** (the mechanics Appendix A):

- a **player** is a customer on the platform, and saves a method there once, in a
  setup for off-session use — the terms were accepted before the setup's secret
  was released (``application/setup.py``);
- a **club** is a connected account, onboarded on the provider's own hosted
  pages, whose status and payouts are read back;
- a **payment** is made on the club's account — the club is the seller — out of a
  copy of the player's method cloned onto it for that one charge.

**Every write takes an idempotency key**, and the caller derives it from its own
record, because a provider forgets a key after a day (the mechanics Appendix A:
*Raketa's own records must prevent duplicates*). The same key twice answers the
first call's result and does nothing again; the same key with different
arguments is a bug, and refused. **One write takes none**: an onboarding link is
single use, and a key would hand back a link already spent.

**An outcome is not an error.** A declined card, a bank that wants the player
present and a setup still waiting for the phone are answers, returned as
statuses; only a provider that could not be reached — or that refused the call
for being malformed, which is a bug here — raises. ``PaymentsUnavailable`` is the
one raise a caller is expected to meet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant


class Wallet(StrEnum):
    """The phone's own wallet a card was saved through. Only the two the setup
    offers (the mechanics §12.4): Apple Pay on an iPhone, Google Pay on Android.
    A card saved through any other wallet is recorded as a plain card."""

    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"


@final
@dataclass(frozen=True, slots=True)
class CardOnFile:
    """A method saved at the provider, as far as Raketa needs to know it.

    ``brand`` is the card network **as the provider names it**, lower case —
    ``visa``, ``mastercard`` — an open set a client draws a badge from, so a new
    network never fails a read. The number itself never reaches Raketa: only the
    last four digits, which every receipt prints."""

    method_id: str
    brand: str
    last_four: str
    wallet: Wallet | None = None


class SetupStatus(StrEnum):
    """Where a setup stands, in the words the player's screen needs."""

    #: Nothing entered yet, or entered and not confirmed on the phone.
    AWAITING_THE_PHONE = "AWAITING_THE_PHONE"
    #: The bank wants its one-time check (3-D Secure), and the phone has not
    #: finished it.
    AUTHENTICATING = "AUTHENTICATING"
    #: The provider is still deciding.
    PROCESSING = "PROCESSING"
    #: The bank refused the card. The same setup can be tried again with
    #: another one.
    DECLINED = "DECLINED"
    #: The setup was cancelled and can never save anything.
    CANCELLED = "CANCELLED"
    #: The method is saved.
    SUCCEEDED = "SUCCEEDED"


@final
@dataclass(frozen=True, slots=True)
class StartedSetup:
    """A setup the provider opened: its id, which Raketa records, and the
    secret the phone confirms it with, which it never does."""

    setup_id: str
    client_secret: str


@final
@dataclass(frozen=True, slots=True)
class SetupReading:
    """A setup as it stands now. ``card`` is present exactly when it
    ``SUCCEEDED``; ``client_secret`` is what the phone confirms it with."""

    setup_id: str
    customer_id: str
    status: SetupStatus
    client_secret: str
    card: CardOnFile | None = None


class PaymentStatus(StrEnum):
    """Where one payment on a club's account stands."""

    #: Held on the card and not yet taken — a manual-capture authorisation.
    AUTHORISED = "AUTHORISED"
    #: Taken.
    CAPTURED = "CAPTURED"
    #: Released without being taken, which costs nothing.
    CANCELLED = "CANCELLED"
    #: The bank wants the player present — even with permission on file, which
    #: is rare and allowed. The player confirms **this same payment** in the app,
    #: with ``client_secret`` on the club's account.
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    #: The bank refused. ``decline_code`` says why, when it said. The player can
    #: still confirm **this same payment** in the app with another card, with
    #: ``client_secret`` on the club's account (the mechanics Appendix A).
    DECLINED = "DECLINED"
    #: The provider is still deciding.
    PROCESSING = "PROCESSING"


#: The two states a payment waits for its player in: the phone confirms it on
#: the club's account, with the payment's ``client_secret``.
AWAITING_THE_PLAYER = frozenset(
    {PaymentStatus.AUTHENTICATION_REQUIRED, PaymentStatus.DECLINED}
)


@final
@dataclass(frozen=True, slots=True)
class Payment:
    """One payment on a club's account. ``client_secret`` is present exactly
    while the payment waits for its player (``AWAITING_THE_PLAYER``) — a secret,
    asked of the provider when it is handed out and never recorded
    (``docs/adr/0184`` §4). ``fee_grosze`` is the card fee the provider took on
    it, which the club pays (#548) — once it is ``CAPTURED``, and ``None``
    before, or where the provider has not settled it yet."""

    payment_id: str
    status: PaymentStatus
    amount_grosze: int
    client_secret: str | None = None
    decline_code: str | None = None
    fee_grosze: int | None = None


class RefundStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@final
@dataclass(frozen=True, slots=True)
class Refund:
    """Money given back out of a captured payment. ``fee_withheld_grosze`` is
    the card fee kept back — the processing fee the provider never returns —
    and nought on a refund in full (the mechanics §12.3)."""

    refund_id: str
    status: RefundStatus
    amount_grosze: int
    fee_withheld_grosze: int


class ClubAccountStatus(StrEnum):
    """A club's connected account, in the three states the setup checklist
    draws (the screens B2)."""

    NOT_STARTED = "NOT_STARTED"
    NEEDS_DETAILS = "NEEDS_DETAILS"
    READY = "READY"


@final
@dataclass(frozen=True, slots=True)
class ClubAccountReading:
    account_id: str
    status: ClubAccountStatus
    charges_enabled: bool
    payouts_enabled: bool


class PayoutStatus(StrEnum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@final
@dataclass(frozen=True, slots=True)
class Payout:
    """Money on its way from a club's account to its bank."""

    payout_id: str
    amount_grosze: int
    arrives_at: Instant
    status: PayoutStatus


@runtime_checkable
class PaymentProvider(Protocol):
    """Everything money needs from the outside world, in one port."""

    def publishable_key(self) -> str:
        """The key a phone initialises the provider's own fields with. Not a
        secret: it can only collect details, never charge."""
        ...

    # ------------------------------------------------------ players, on the platform

    async def open_customer(self, *, player_id: UUID, idempotency_key: str) -> str:
        """Open the player's customer on the platform, and answer its id."""
        ...

    async def start_setup(
        self, *, customer_id: str, player_id: UUID, idempotency_key: str
    ) -> StartedSetup:
        """Open a setup that saves a card for **off-session** use — charged
        later without the player present."""
        ...

    async def read_setup(self, setup_id: str) -> SetupReading:
        """The setup as it stands now, with the card once it is saved."""
        ...

    async def cancel_setup(
        self, setup_id: str, *, idempotency_key: str
    ) -> SetupReading:
        """Close a setup so that nothing can be saved out of it — or, where the
        phone already saved a card with it, answer that: a saved setup cannot be
        cancelled, and its card is the caller's to release."""
        ...

    async def read_card(self, method_id: str) -> CardOnFile:
        """A saved card as it stands now — after its bank updated it, say. A
        notice that one was updated is a prompt to read it, never the reading:
        notices arrive out of order."""
        ...

    async def release_method(self, method_id: str, *, idempotency_key: str) -> None:
        """Forget a saved card: it can never be charged again. Releasing one
        already released does nothing."""
        ...

    # ------------------------------------------------ clubs, as connected accounts

    async def open_club_account(
        self, *, club_id: UUID, name: str, email: str, idempotency_key: str
    ) -> str:
        """Open the club's connected account, and answer its id. The club pays
        the provider's fees and the provider covers its losses."""
        ...

    async def onboarding_link(
        self, account_id: str, *, refresh_url: str, return_url: str
    ) -> str:
        """A link to the provider's hosted onboarding for this account — the
        first visit's, or the one that continues it while details are missing.
        Single use and short-lived, so a fresh one every time and no key."""
        ...

    async def read_club_account(self, account_id: str) -> ClubAccountReading: ...

    async def payouts(self, account_id: str, *, limit: int) -> tuple[Payout, ...]:
        """The account's most recent payouts, newest first."""
        ...

    async def pay_out(
        self,
        account_id: str,
        *,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payout:
        """Send ``amount_grosze`` of the club's money on its account to its
        bank, now (#548). **The club is paid after the game is played**
        (the mechanics §12.6): until then its money waits on its account, where
        a refund before the start can come out of it — so it is Raketa that
        releases a payout, never the provider's own schedule. *How* the
        provider is kept from paying out on its own is open item O2; the fake
        pays out nothing it is not asked to. A balance that cannot cover it
        yet is ``PaymentsUnavailable``: asked again later."""
        ...

    # ------------------------------------------------ money, on the club's account

    async def clone_method(
        self,
        *,
        customer_id: str,
        method_id: str,
        account_id: str,
        idempotency_key: str,
    ) -> str:
        """Copy a player's saved card onto a club's account for **one** charge,
        and answer the copy's id. The permission to share it is the player's
        acceptance of the terms."""
        ...

    async def authorise(
        self,
        *,
        account_id: str,
        method_id: str,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payment:
        """Hold ``amount_grosze`` on a cloned card, off-session, to be captured
        or cancelled — the first half of the all-or-nothing fill."""
        ...

    async def read_payment(self, *, account_id: str, payment_id: str) -> Payment:
        """A payment on a club's account **as it stands now** — after its player
        confirmed it in the app, say. A notice that one moved is a prompt to
        read it, never the reading: notices arrive out of order (#541)."""
        ...

    async def capture(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment: ...

    async def cancel(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment: ...

    async def charge_now(
        self,
        *,
        account_id: str,
        method_id: str,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payment:
        """Take ``amount_grosze`` at once, off-session. **No caller yet**: a
        rescue (#545) holds its one share and takes the hold in its own
        transaction, as the fill does, so a crash between the provider and the
        record leaves a hold that lapses rather than money taken for no seat."""
        ...

    async def refund(
        self,
        *,
        account_id: str,
        payment_id: str,
        withhold_fee: bool,
        idempotency_key: str,
    ) -> Refund:
        """Give a captured payment back — all of it, or all of it but the card
        fee, which the provider never returns (the mechanics §12.3)."""
        ...
