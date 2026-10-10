"""The in-process payment provider: local runs, seeds and every API test.

**It is held to the same demands as Stripe** (``tests/demands/
test_payments_demands.py``), so what a test learns from it is true of the
provider — and it is the reason no test in this suite needs a network, a key or
a Stripe account.

**Controlled by the card the phone enters.** A card is typed on a player's
phone into the provider's own fields and never reaches the backend, so the fake
is told which card was typed — one of the five in ``domain/entered_cards.py``,
which are Stripe's own test cards down to the last four digits — and behaves as
that card would: saved, refused at the setup, checked by the bank once or every
time, or declining every payment once saved. ``card_behaves`` changes a saved
card's mind later, ``phone_confirms_payment`` is a player confirming a payment
that waited for them in the app, ``club_account_is`` sets an account's state,
``onboarding_completes`` finishes every club's onboarding the moment its link
is made, and ``unreachable`` makes every call fail as an outage does.

**It knows card kinds and hold windows** (ADR-0190's 2026-10-10 amendment).
A card is a personal one issued in the EU unless a test or the console says
otherwise (``card_is``) — a business card, a UK card, one from outside Europe —
and when its money is taken the fake keeps **that kind's real fee**
(``CARD_PRICES``), which is what a late leaver's refund is the share less. A
hold made without its player lasts its network's window on the fake's
``clock`` (``HOLD_WINDOWS``: 4 days 18 hours on a Visa, 7 days on a
Mastercard; 7 days on either once the player confirmed it in the app), and
**lapses** after its last moment: it is read cancelled, and a capture is
refused. A club on its own negotiated pricing (``fees_reported_later``) is
told its fee after the capture — *not yet known* until ``reports_fee``. A fake
with no clock says no last moment and lets nothing lapse.

**It pays a club out only when asked** (#548) — the club's money is held until
after the game, which is what Raketa asks it for — and dates the payout's
arrival two days after its ``clock``'s now; a fake with no clock cannot date
one, and refuses.

**Every call is recorded**, in order, with its arguments (``calls`` and
``called``), so a test asserts what was asked of the provider without a mock.

**It refuses what Stripe refuses as an invalid request** (``FakeRefusal``): a key
reused with other arguments, capturing what is not held, cancelling what was
taken, refunding what was never taken or more than was, cloning a card that was
released. Each is a bug in the caller, and a fake that answered it would hide
one.

**A payment it never made is taken or let go as a hold** (``_on_account``): a
seed run fills games through its own fake, and a laptop's server reloads, so the
outbox that captures a seat may reach a fake that never held it — **or given
back as a payment taken** (#544), since Raketa refunds only a share it recorded
paid. **A fake's payment id carries its amount** (``pi_fake_3000g_…``), so a
fake in another process adopts one for what it was made for.

**A local run holds one for the process** (``build_payment_provider``), which
confirms every setup with ``A_CARD`` as soon as it is read — the phone of a
laptop run has no real provider to confirm against — and completes a club's
onboarding the moment its link is made. A test's fake does neither unless told.

**The games test console steers that one** (#591; ``docs/adr/0194`` §2), and
three more controls are its: ``card_behaviour_of`` reads what ``card_behaves``
set; **every move of a payment records the notice Stripe would have sent**
(``notices``), which the console replays — twice, or out of order — through
the webhook's own handling, since the fake sends none itself; and **refunds can
wait** (``refunds_wait``): a refund asked for then is answered as a provider
that has not given it — ``PaymentsUnavailable``, so the outbox asks again, as it
would of a provider that was down — until ``gives_refund`` lets that payment's
through, or the wait is lifted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import timedelta
from typing import Any, Mapping, final
from uuid import UUID, uuid4

from app.kernel import Clock, Instant, instant
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    CardBehaviour,
    CardKind,
    EnteredCard,
)
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.notices import SeatPaymentChanged
from app.modules.payments.domain.provider import (
    AWAITING_THE_PLAYER,
    CardOnFile,
    ClubAccountReading,
    ClubAccountStatus,
    Payment,
    PaymentStatus,
    Payout,
    PayoutStatus,
    Refund,
    RefundStatus,
    SetupReading,
    SetupStatus,
    StartedSetup,
)

#: How long the fake says a payout takes to reach a club's bank.
PAYOUT_TAKES = timedelta(days=2)

#: What the provider keeps when a card's money is taken, by the kind of card:
#: a rate in hundredths of a per cent, and a fixed part in grosze — Stripe's
#: own prices for a club in Poland (the mechanics Appendix A).
CARD_PRICES: Mapping[CardKind, tuple[int, int]] = {
    CardKind.PERSONAL_EU: (150, 100),  # 1,5 % + 1 zł
    CardKind.BUSINESS: (190, 100),  # 1,9 % + 1 zł
    CardKind.UK: (250, 100),  # 2,5 % + 1 zł
    CardKind.OUTSIDE_EUROPE: (325, 100),  # 3,25 % + 1 zł
}

#: How long a hold made **without its player** lasts, by network — Stripe's
#: merchant-initiated windows. Any other network is given the shortest.
HOLD_WINDOWS: Mapping[str, timedelta] = {
    "visa": timedelta(days=4, hours=18),
    "mastercard": timedelta(days=7),
}

#: How long a hold its player confirmed in the app lasts — customer-initiated,
#: 7 days on every network.
CONFIRMED_HOLD_LASTS = timedelta(days=7)


def fee_on(amount_grosze: int, kind: CardKind) -> int:
    """The fee kept on ``amount_grosze`` taken from a card of ``kind``, half a
    grosz rounding up."""

    rate, fixed = CARD_PRICES[kind]
    return (amount_grosze * rate + 5000) // 10000 + fixed


def _hold_lasts(network: str) -> timedelta:
    return HOLD_WINDOWS.get(network, min(HOLD_WINDOWS.values()))


class FakeRefusal(Exception):
    """What Stripe would answer as an invalid request — a bug in the caller."""


@final
@dataclass(frozen=True, slots=True)
class RecordedCall:
    """One call made to the fake, and what it was given."""

    name: str
    arguments: Mapping[str, Any]


#: The ``payment_intent.*`` kind Stripe sends when a payment arrives at each
#: status — what ``StripeNotices`` reads as ``SeatPaymentChanged``.
NOTICE_KINDS: Mapping[PaymentStatus, str] = {
    PaymentStatus.AUTHORISED: "payment_intent.amount_capturable_updated",
    PaymentStatus.CAPTURED: "payment_intent.succeeded",
    PaymentStatus.CANCELLED: "payment_intent.canceled",
    PaymentStatus.DECLINED: "payment_intent.payment_failed",
    PaymentStatus.AUTHENTICATION_REQUIRED: "payment_intent.requires_action",
}


#: The kind Stripe sends when a captured payment's fee becomes readable — a
#: club on its own negotiated pricing is told it after the take (#641).
FEE_READY_KIND = "charge.updated"


@final
@dataclass(frozen=True, slots=True)
class SentNotice:
    """The notice Stripe would have sent when a payment moved: what Raketa reads
    off the wire, the kind it came as, and the status the move left — which the
    notice itself never carries, since a notice is read as a prompt."""

    notice: SeatPaymentChanged
    kind: str
    status: PaymentStatus


@dataclass
class _Setup:
    setup_id: str
    customer_id: str
    client_secret: str
    card: EnteredCard | None = None
    authenticated: bool = False
    method_id: str | None = None
    cancelled: bool = False


@dataclass
class _Method:
    method_id: str
    card: EnteredCard
    released: bool = False


@dataclass
class _Payment:
    payment_id: str
    account_id: str
    amount_grosze: int
    status: PaymentStatus
    client_secret: str
    decline_code: str | None = None
    #: Made by another process's fake, and answered here as it stands there.
    adopted: bool = False
    #: The kind of card it was made on — which fee is kept when it is taken.
    kind: CardKind = CardKind.PERSONAL_EU
    #: When its hold ends unless it is taken; ``None`` where nothing is held,
    #: or the fake has no clock to say it on.
    last_moment: Instant | None = None
    #: Whether the fee kept on it is known yet — once it is taken.
    fee_known: bool = True
    #: What was given back of it so far.
    refunded_grosze: int = 0


def _id(prefix: str) -> str:
    return f"{prefix}_fake_{uuid4().hex[:24]}"


def _payment_id(amount_grosze: int) -> str:
    """A payment's id, carrying what it was made for — so a fake in another
    process adopts it for its amount."""

    return f"pi_fake_{amount_grosze}g_{uuid4().hex[:20]}"


_AMOUNT_IN_AN_ID = re.compile(r"^pi_fake_(\d+)g_")


def _amount_in(payment_id: str) -> int:
    """What a payment another fake made was for — nought for an id that does
    not say, which no fake of this version makes."""

    found = _AMOUNT_IN_AN_ID.match(payment_id)
    return 0 if found is None else int(found.group(1))


@final
class FakePayments:
    """``PaymentProvider``, in memory."""

    def __init__(
        self,
        *,
        confirms_every_setup_with: EnteredCard | None = None,
        onboarding_completes: bool = False,
        clock: Clock | None = None,
    ) -> None:
        self._auto_card = confirms_every_setup_with
        #: What a payout's arrival, and a hold's last moment, are dated from.
        self.clock = clock
        #: Set to finish a club's onboarding the moment its link is made — the
        #: link then lands where the provider's would, back on the club website.
        self.onboarding_completes = onboarding_completes
        #: Set to make every call fail as an outage does.
        self.unreachable = False
        self.calls: list[RecordedCall] = []
        # Idempotency: key -> the arguments of the first call with it, and the
        # object that call made.
        self._by_key: dict[str, tuple[Mapping[str, Any], Any]] = {}
        self._setups: dict[str, _Setup] = {}
        self._methods: dict[str, _Method] = {}
        # Clone id -> the saved method it was copied from.
        self._clones: dict[str, str] = {}
        self._payments: dict[str, _Payment] = {}
        self._accounts: dict[str, ClubAccountStatus] = {}
        # Club id -> the account opened for it.
        self._club_accounts: dict[UUID, str] = {}
        self._payouts: dict[str, list[Payout]] = {}
        #: Every notice Stripe would have sent, in the order the payments moved.
        self.notices: list[SentNotice] = []
        #: Set to keep every refund asked for until it is let through.
        self.refunds_wait = False
        # Payments whose refund the console let through while refunds wait.
        self._refunds_let_through: set[str] = set()
        #: The club accounts on their own negotiated pricing: the fee on a
        #: payment taken there is not known until ``reports_fee``.
        self.fees_reported_later: set[str] = set()

    # ----------------------------------------------------------------- controls

    def phone_enters(self, setup_id: str, card: EnteredCard) -> None:
        """The player typed ``card`` into the setup's fields and confirmed — which
        saves it at once, as at Stripe, unless its bank refuses it or checks it
        first. A cancelled setup, or one that saved a card, confirms nothing."""

        setup = self._setups[setup_id]
        if setup.cancelled or setup.method_id is not None:
            raise FakeRefusal(f"{setup_id} can no longer be confirmed")
        setup.card = card
        setup.authenticated = False
        self._save_if_confirmed(setup, card)

    def phone_authenticates(self, setup_id: str) -> None:
        """The bank's one-time check was passed on the phone."""

        setup = self._setups[setup_id]
        setup.authenticated = True
        if setup.card is not None:
            self._save_if_confirmed(setup, setup.card)

    def phone_confirms_payment(
        self, payment_id: str, *, with_card: EnteredCard | None = None
    ) -> None:
        """The player confirmed, in the app, a payment that waited for them: the
        bank's check passed — or, for a declined one, ``with_card`` was typed
        instead and its bank agreed. Held, or taken if it was a charge now; a
        payment that waited for nobody confirms nothing."""

        payment = self._payment(payment_id)
        if payment.status not in AWAITING_THE_PLAYER:
            raise FakeRefusal(f"{payment_id} is {payment.status}: nothing to confirm")
        if payment.status is PaymentStatus.DECLINED:
            if with_card is None:
                raise FakeRefusal(f"{payment_id} was declined: confirm another card")
            if with_card.behaviour in (
                CardBehaviour.DECLINED_AT_SETUP,
                CardBehaviour.DECLINES_PAYMENTS,
            ):
                return
            payment.kind = with_card.kind
        payment.status = PaymentStatus.AUTHORISED
        payment.decline_code = None
        if self.clock is not None:
            payment.last_moment = instant(self.clock.now() + CONFIRMED_HOLD_LASTS)
        self._notify(payment)

    def card_behaves(self, method_id: str, behaviour: CardBehaviour) -> None:
        """A saved card changes its mind — a later decline, say."""

        method = self._method(method_id)
        method.card = replace(method.card, behaviour=behaviour)

    def card_behaviour_of(self, method_id: str) -> CardBehaviour:
        """How a saved card answers a payment now — one another process saved
        answers as the card every seed saves, until it is told otherwise."""

        return self._method(method_id).card.behaviour

    def card_is(
        self,
        method_id: str,
        *,
        kind: CardKind | None = None,
        network: str | None = None,
    ) -> None:
        """A saved card is of this kind, on this network, from its next payment
        on — what the console and a test choose (ADR-0190's 2026-10-10
        amendment). Only the fake's own record moves: the player's method is
        not told, as no bank would tell it."""

        method = self._method(method_id)
        method.card = replace(
            method.card,
            kind=method.card.kind if kind is None else kind,
            brand=method.card.brand if network is None else network,
        )

    def card_kind_of(self, method_id: str) -> CardKind:
        return self._method(method_id).card.kind

    def card_network_of(self, method_id: str) -> str:
        return self._method(method_id).card.brand

    def reports_fee(self, payment_id: str) -> None:
        """The provider reports the fee it kept on a payment taken at a club on
        its own negotiated pricing: a reading says it from now on, and the
        notice Stripe sends then — ``charge.updated`` — is recorded (#641)."""

        payment = self._payment(payment_id)
        payment.fee_known = True
        self.notices.append(
            SentNotice(
                notice=SeatPaymentChanged(
                    notice_id=_id("evt"),
                    account_id=payment.account_id,
                    payment_id=payment.payment_id,
                ),
                kind=FEE_READY_KIND,
                status=payment.status,
            )
        )

    def gives_refund(self, payment_id: str) -> None:
        """Let this payment's refund through, while refunds wait: the next time
        it is asked for, it is given."""

        self._refunds_let_through.add(payment_id)

    def bank_replaces_card(self, method_id: str, *, brand: str, last_four: str) -> None:
        """The card's bank issued a new one under the same saved method — a new
        number, or a new brand — as the account updater does."""

        method = self._method(method_id)
        method.card = replace(method.card, brand=brand, last_four=last_four)

    def club_account_is(self, account_id: str, status: ClubAccountStatus) -> None:
        self._accounts[account_id] = status

    def account_opened_for(self, club_id: UUID) -> str:
        """The account opened for this club — the id a notice about it names."""

        return self._club_accounts[club_id]

    def pays_out(
        self,
        account_id: str,
        *,
        amount_grosze: int,
        arrives_at: Instant,
        status: PayoutStatus = PayoutStatus.PAID,
    ) -> Payout:
        payout = Payout(
            payout_id=_id("po"),
            amount_grosze=amount_grosze,
            arrives_at=arrives_at,
            status=status,
        )
        self._payouts.setdefault(account_id, []).insert(0, payout)
        return payout

    def called(self, name: str) -> list[RecordedCall]:
        """Every call of one kind, in order."""

        return [call for call in self.calls if call.name == name]

    def is_released(self, method_id: str) -> bool:
        return self._method(method_id).released

    # -------------------------------------------------------------------- port

    def publishable_key(self) -> str:
        return "pk_fake_raketa"

    async def open_customer(self, *, player_id: UUID, idempotency_key: str) -> str:
        self._record("open_customer", player_id=player_id, key=idempotency_key)
        return self._once(idempotency_key, {"player_id": player_id}, lambda: _id("cus"))

    async def start_setup(
        self, *, customer_id: str, player_id: UUID, idempotency_key: str
    ) -> StartedSetup:
        self._record(
            "start_setup",
            customer_id=customer_id,
            player_id=player_id,
            key=idempotency_key,
        )

        def opened() -> StartedSetup:
            setup_id = _id("seti")
            secret = f"{setup_id}_secret_{uuid4().hex[:12]}"
            self._setups[setup_id] = _Setup(setup_id, customer_id, secret)
            return StartedSetup(setup_id=setup_id, client_secret=secret)

        return self._once(
            idempotency_key,
            {"customer_id": customer_id, "player_id": player_id},
            opened,
        )

    async def read_setup(self, setup_id: str) -> SetupReading:
        self._record("read_setup", setup_id=setup_id)
        setup = self._setups.get(setup_id)
        if setup is None:
            # A local run whose process restarted between the start and the
            # confirmation: the fake of the laptop confirms with its own card.
            if self._auto_card is None:
                raise LookupError(f"no such setup: {setup_id}")
            setup = self._setups[setup_id] = _Setup(setup_id, "", "")
        return self._state_of(setup)

    def _state_of(self, setup: _Setup) -> SetupReading:
        if setup.cancelled:
            return self._reading(setup, SetupStatus.CANCELLED)
        if setup.method_id is None:
            card = setup.card or self._auto_card
            if card is None:
                return self._reading(setup, SetupStatus.AWAITING_THE_PHONE)
            if setup.card is None:
                # A laptop's fake: its phone never confirms, so reading is
                # confirming.
                self._save_if_confirmed(setup, card)
        if setup.method_id is None:
            assert setup.card is not None
            if setup.card.behaviour is CardBehaviour.DECLINED_AT_SETUP:
                return self._reading(setup, SetupStatus.DECLINED)
            return self._reading(setup, SetupStatus.AUTHENTICATING)
        saved = self._methods[setup.method_id]
        return self._reading(
            setup,
            SetupStatus.SUCCEEDED,
            card=CardOnFile(
                method_id=saved.method_id,
                brand=saved.card.brand,
                last_four=saved.card.last_four,
                wallet=saved.card.wallet,
            ),
        )

    async def cancel_setup(
        self, setup_id: str, *, idempotency_key: str
    ) -> SetupReading:
        self._record("cancel_setup", setup_id=setup_id, key=idempotency_key)
        setup = self._setups.get(setup_id)
        if setup is None:
            raise FakeRefusal(f"no such setup: {setup_id}")
        if setup.method_id is None:
            setup.cancelled = True
        return self._state_of(setup)

    async def read_card(self, method_id: str) -> CardOnFile:
        self._record("read_card", method_id=method_id)
        card = self._method(method_id).card
        return CardOnFile(
            method_id=method_id,
            brand=card.brand,
            last_four=card.last_four,
            wallet=card.wallet,
        )

    async def release_method(self, method_id: str, *, idempotency_key: str) -> None:
        self._record("release_method", method_id=method_id, key=idempotency_key)
        self._method(method_id).released = True

    async def open_club_account(
        self, *, club_id: UUID, name: str, email: str, idempotency_key: str
    ) -> str:
        self._record(
            "open_club_account",
            club_id=club_id,
            name=name,
            email=email,
            key=idempotency_key,
        )

        def opened() -> str:
            account_id = _id("acct")
            self._accounts[account_id] = ClubAccountStatus.NOT_STARTED
            self._club_accounts[club_id] = account_id
            return account_id

        return self._once(
            idempotency_key, {"club_id": club_id, "name": name, "email": email}, opened
        )

    async def onboarding_link(
        self, account_id: str, *, refresh_url: str, return_url: str
    ) -> str:
        self._record(
            "onboarding_link",
            account_id=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
        )
        if self.onboarding_completes:
            # A laptop's club has no provider to onboard with: following the
            # link is finishing it, and it lands where the real one would.
            self._accounts[account_id] = ClubAccountStatus.READY
            return return_url
        return f"https://connect.payments.raketa.example/onboarding/{account_id}"

    async def read_club_account(self, account_id: str) -> ClubAccountReading:
        self._record("read_club_account", account_id=account_id)
        status = self._accounts.get(account_id, ClubAccountStatus.NOT_STARTED)
        ready = status is ClubAccountStatus.READY
        return ClubAccountReading(
            account_id=account_id,
            status=status,
            charges_enabled=ready,
            payouts_enabled=ready,
        )

    async def payouts(self, account_id: str, *, limit: int) -> tuple[Payout, ...]:
        self._record("payouts", account_id=account_id, limit=limit)
        return tuple(self._payouts.get(account_id, [])[:limit])

    async def pay_out(
        self,
        account_id: str,
        *,
        amount_grosze: int,
        description: str,
        metadata: Mapping[str, str],
        idempotency_key: str,
    ) -> Payout:
        self._record(
            "pay_out",
            account_id=account_id,
            amount_grosze=amount_grosze,
            description=description,
            metadata=dict(metadata),
            key=idempotency_key,
        )

        def paid_out() -> Payout:
            if amount_grosze <= 0:
                raise FakeRefusal(f"a payout of {amount_grosze} grosze")
            if self.clock is None:
                raise FakeRefusal("a fake with no clock cannot date a payout")
            payout = Payout(
                payout_id=_id("po"),
                amount_grosze=amount_grosze,
                arrives_at=instant(self.clock.now() + PAYOUT_TAKES),
                status=PayoutStatus.IN_TRANSIT,
            )
            self._payouts.setdefault(account_id, []).insert(0, payout)
            return payout

        return self._once(
            idempotency_key,
            {"account": account_id, "amount": amount_grosze},
            paid_out,
        )

    async def clone_method(
        self,
        *,
        customer_id: str,
        method_id: str,
        account_id: str,
        idempotency_key: str,
    ) -> str:
        self._record(
            "clone_method",
            customer_id=customer_id,
            method_id=method_id,
            account_id=account_id,
            key=idempotency_key,
        )

        def cloned() -> str:
            if self._method(method_id).released:
                raise FakeRefusal(f"{method_id} was released and cannot be cloned")
            clone_id = _id("pm")
            self._clones[clone_id] = method_id
            return clone_id

        return self._once(
            idempotency_key,
            {"customer_id": customer_id, "method_id": method_id, "account": account_id},
            cloned,
        )

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
        self._record(
            "authorise",
            account_id=account_id,
            method_id=method_id,
            amount_grosze=amount_grosze,
            description=description,
            metadata=dict(metadata),
            key=idempotency_key,
        )
        return self._once(
            idempotency_key,
            {"account": account_id, "method_id": method_id, "amount": amount_grosze},
            lambda: self._held(account_id, method_id, amount_grosze),
        )

    async def read_payment(self, *, account_id: str, payment_id: str) -> Payment:
        self._record("read_payment", account_id=account_id, payment_id=payment_id)
        return self._answer(self._on_account(payment_id, account_id))

    async def capture(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        self._record(
            "capture", account_id=account_id, payment_id=payment_id, key=idempotency_key
        )
        payment = self._on_account(payment_id, account_id)
        if payment.status is PaymentStatus.AUTHORISED:
            payment.status = PaymentStatus.CAPTURED
            payment.fee_known = account_id not in self.fees_reported_later
            self._notify(payment)
        elif payment.status is not PaymentStatus.CAPTURED:
            raise FakeRefusal(f"{payment_id} is {payment.status} and cannot be taken")
        return self._answer(payment)

    async def cancel(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        self._record(
            "cancel", account_id=account_id, payment_id=payment_id, key=idempotency_key
        )
        payment = self._on_account(payment_id, account_id)
        if payment.status is PaymentStatus.CAPTURED:
            raise FakeRefusal(f"{payment_id} was taken; refund it instead")
        if payment.status is not PaymentStatus.CANCELLED:
            payment.status = PaymentStatus.CANCELLED
            self._notify(payment)
        return self._answer(payment)

    async def refund(
        self,
        *,
        account_id: str,
        payment_id: str,
        amount_grosze: int,
        idempotency_key: str,
    ) -> Refund:
        self._record(
            "refund",
            account_id=account_id,
            payment_id=payment_id,
            amount_grosze=amount_grosze,
            key=idempotency_key,
        )
        if (
            self.refunds_wait
            and idempotency_key not in self._by_key
            and payment_id not in self._refunds_let_through
        ):
            # Not given yet: the outbox asks again, as of a provider that is
            # down, until the console lets it through (#591).
            raise PaymentsUnavailable()

        def refunded() -> Refund:
            self._refunds_let_through.discard(payment_id)
            payment = self._on_account(payment_id, account_id)
            if payment.adopted and payment.status is PaymentStatus.AUTHORISED:
                # Raketa gives back only a share it recorded paid: the process
                # that held this one took it, too.
                payment.status = PaymentStatus.CAPTURED
            if payment.status is not PaymentStatus.CAPTURED:
                raise FakeRefusal(f"{payment_id} was never taken; cancel it instead")
            left = payment.amount_grosze - payment.refunded_grosze
            if not 0 < amount_grosze <= left:
                raise FakeRefusal(
                    f"a refund of {amount_grosze} grosze of {payment_id}, "
                    f"which has {left} left to give back"
                )
            payment.refunded_grosze += amount_grosze
            return Refund(
                refund_id=_id("re"),
                status=RefundStatus.SUCCEEDED,
                amount_grosze=amount_grosze,
            )

        return self._once(
            idempotency_key,
            {"account": account_id, "payment_id": payment_id, "amount": amount_grosze},
            refunded,
        )

    # -------------------------------------------------------------- internals

    def _record(self, call: str, /, **arguments: Any) -> None:
        self.calls.append(RecordedCall(name=call, arguments=arguments))
        if self.unreachable:
            raise PaymentsUnavailable()

    def _once(self, key: str, arguments: Mapping[str, Any], make: Any) -> Any:
        """The first answer given under ``key``, as Stripe replays it — and a
        refusal for the key reused with different arguments."""

        if key in self._by_key:
            first, answer = self._by_key[key]
            if first != arguments:
                raise FakeRefusal(f"idempotency key {key} reused with other arguments")
            return answer
        answer = make()
        self._by_key[key] = (dict(arguments), answer)
        return answer

    def _payment(self, payment_id: str) -> _Payment:
        payment = self._payments.get(payment_id)
        if payment is None:
            raise FakeRefusal(f"no such payment: {payment_id}")
        return payment

    def _on_account(self, payment_id: str, account_id: str) -> _Payment:
        """A payment on this club's account. **One held by another process** —
        a seed run's fill, or this laptop's before its server reloaded — is one
        this fake never saw, and it answers as a hold it can take or let go,
        for the amount its id carries, as ``_method`` answers a card it never
        saved."""

        payment = self._payments.get(payment_id)
        if payment is None:
            payment = self._payments[payment_id] = _Payment(
                payment_id=payment_id,
                account_id=account_id,
                amount_grosze=_amount_in(payment_id),
                status=PaymentStatus.AUTHORISED,
                client_secret=f"{payment_id}_secret_adopted",
                adopted=True,
            )
        if payment.account_id != account_id:
            raise FakeRefusal(f"{payment_id} is not on {account_id}")
        self._lapse_if_due(payment)
        return payment

    def _lapse_if_due(self, payment: _Payment) -> None:
        """A hold past its last moment on the fake's clock has lapsed: Stripe
        cancels it, untaken, and says so."""

        if (
            payment.status is PaymentStatus.AUTHORISED
            and payment.last_moment is not None
            and self.clock is not None
            and self.clock.now() > payment.last_moment
        ):
            payment.status = PaymentStatus.CANCELLED
            self._notify(payment)

    @staticmethod
    def _saves(card: EnteredCard, *, authenticated: bool) -> bool:
        if card.behaviour is CardBehaviour.DECLINED_AT_SETUP:
            return False
        checked = card.behaviour in (
            CardBehaviour.CHECKED_AT_SETUP,
            CardBehaviour.CHECKED_EVERY_TIME,
        )
        return authenticated or not checked

    def _save_if_confirmed(self, setup: _Setup, card: EnteredCard) -> None:
        if setup.method_id is None and self._saves(
            card, authenticated=setup.authenticated
        ):
            setup.method_id = _id("pm")
            self._methods[setup.method_id] = _Method(setup.method_id, card)

    def _method(self, method_id: str) -> _Method:
        # A method saved by another process — a seed run, say — is one this
        # fake has never seen, and it answers as the card every seed saves.
        return self._methods.setdefault(method_id, _Method(method_id, A_CARD))

    def _reading(
        self, setup: _Setup, status: SetupStatus, *, card: CardOnFile | None = None
    ) -> SetupReading:
        return SetupReading(
            setup_id=setup.setup_id,
            customer_id=setup.customer_id,
            status=status,
            client_secret=setup.client_secret,
            card=card,
        )

    def _held(self, account_id: str, method_id: str, amount_grosze: int) -> Payment:
        card = self._method(self._clones.get(method_id, method_id)).card
        payment_id = _payment_id(amount_grosze)
        payment = _Payment(
            payment_id=payment_id,
            account_id=account_id,
            amount_grosze=amount_grosze,
            status=PaymentStatus.AUTHORISED,
            client_secret=f"{payment_id}_secret_{uuid4().hex[:12]}",
            kind=card.kind,
        )
        if card.behaviour is CardBehaviour.DECLINES_PAYMENTS:
            payment.status = PaymentStatus.DECLINED
            payment.decline_code = "generic_decline"
        elif card.behaviour is CardBehaviour.CHECKED_EVERY_TIME:
            payment.status = PaymentStatus.AUTHENTICATION_REQUIRED
        elif self.clock is not None:
            payment.last_moment = instant(self.clock.now() + _hold_lasts(card.brand))
        self._payments[payment_id] = payment
        self._notify(payment)
        return self._answer(payment)

    def _notify(self, payment: _Payment) -> None:
        """Record the notice Stripe sends when a payment arrives where this one
        just did — on the Connected accounts endpoint, naming the payment and
        its account and carrying nothing of it."""

        self.notices.append(
            SentNotice(
                notice=SeatPaymentChanged(
                    notice_id=_id("evt"),
                    account_id=payment.account_id,
                    payment_id=payment.payment_id,
                ),
                kind=NOTICE_KINDS[payment.status],
                status=payment.status,
            )
        )

    @staticmethod
    def _answer(payment: _Payment) -> Payment:
        return Payment(
            payment_id=payment.payment_id,
            status=payment.status,
            amount_grosze=payment.amount_grosze,
            client_secret=(
                payment.client_secret
                if payment.status in AWAITING_THE_PLAYER
                else None
            ),
            decline_code=payment.decline_code,
            fee_grosze=(
                fee_on(payment.amount_grosze, payment.kind)
                if payment.status is PaymentStatus.CAPTURED and payment.fee_known
                else None
            ),
            last_moment=(
                payment.last_moment
                if payment.status is PaymentStatus.AUTHORISED
                else None
            ),
        )
