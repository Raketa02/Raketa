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
card's mind later, ``club_account_is`` sets an account's state, and
``unreachable`` makes every call fail as an outage does.

**Every call is recorded**, in order, with its arguments (``calls`` and
``called``), so a test asserts what was asked of the provider without a mock.

**It refuses what Stripe refuses as an invalid request** (``FakeRefusal``): a key
reused with other arguments, capturing what is not held, cancelling what was
taken, refunding what was never taken, cloning a card that was released. Each is
a bug in the caller, and a fake that answered it would hide one.

**A local run holds one for the process** (``build_payment_provider``), which
confirms every setup with ``A_CARD`` as soon as it is read — the phone of a
laptop run has no real provider to confirm against — and completes a club's
onboarding the moment its link is made. A test's fake does neither unless told.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, final
from uuid import UUID, uuid4

from app.kernel import Instant
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    CardBehaviour,
    EnteredCard,
)
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import (
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


#: The fake's card fee: Stripe's for a standard EEA card in Poland, 1.5 % and
#: 1,00 zł (the mechanics Appendix A) — about 1,60 zł on a 40 zł share.
_FEE_PER_MILLE = 15
_FEE_FIXED_GROSZE = 100


def card_fee(amount_grosze: int) -> int:
    """The fee the fake withholds on a refund of ``amount_grosze``."""

    return (amount_grosze * _FEE_PER_MILLE + 500) // 1000 + _FEE_FIXED_GROSZE


class FakeRefusal(Exception):
    """What Stripe would answer as an invalid request — a bug in the caller."""


@final
@dataclass(frozen=True, slots=True)
class RecordedCall:
    """One call made to the fake, and what it was given."""

    name: str
    arguments: Mapping[str, Any]


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


def _id(prefix: str) -> str:
    return f"{prefix}_fake_{uuid4().hex[:24]}"


@final
class FakePayments:
    """``PaymentProvider``, in memory."""

    def __init__(
        self,
        *,
        confirms_every_setup_with: EnteredCard | None = None,
        onboarding_completes: bool = False,
    ) -> None:
        self._auto_card = confirms_every_setup_with
        self._onboarding_completes = onboarding_completes
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
        self._payouts: dict[str, list[Payout]] = {}

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

    def card_behaves(self, method_id: str, behaviour: CardBehaviour) -> None:
        """A saved card changes its mind — a later decline, say."""

        method = self._method(method_id)
        method.card = replace(method.card, behaviour=behaviour)

    def bank_replaces_card(self, method_id: str, *, brand: str, last_four: str) -> None:
        """The card's bank issued a new one under the same saved method — a new
        number, or a new brand — as the account updater does."""

        method = self._method(method_id)
        method.card = replace(method.card, brand=brand, last_four=last_four)

    def club_account_is(self, account_id: str, status: ClubAccountStatus) -> None:
        self._accounts[account_id] = status

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
        if self._onboarding_completes:
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
            lambda: self._paid(account_id, method_id, amount_grosze, capture=False),
        )

    async def capture(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        self._record(
            "capture", account_id=account_id, payment_id=payment_id, key=idempotency_key
        )
        payment = self._payment(payment_id)
        if payment.status is PaymentStatus.AUTHORISED:
            payment.status = PaymentStatus.CAPTURED
        elif payment.status is not PaymentStatus.CAPTURED:
            raise FakeRefusal(f"{payment_id} is {payment.status} and cannot be taken")
        return self._answer(payment)

    async def cancel(
        self, *, account_id: str, payment_id: str, idempotency_key: str
    ) -> Payment:
        self._record(
            "cancel", account_id=account_id, payment_id=payment_id, key=idempotency_key
        )
        payment = self._payment(payment_id)
        if payment.status is PaymentStatus.CAPTURED:
            raise FakeRefusal(f"{payment_id} was taken; refund it instead")
        payment.status = PaymentStatus.CANCELLED
        return self._answer(payment)

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
        self._record(
            "charge_now",
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
            lambda: self._paid(account_id, method_id, amount_grosze, capture=True),
        )

    async def refund(
        self,
        *,
        account_id: str,
        payment_id: str,
        withhold_fee: bool,
        idempotency_key: str,
    ) -> Refund:
        self._record(
            "refund",
            account_id=account_id,
            payment_id=payment_id,
            withhold_fee=withhold_fee,
            key=idempotency_key,
        )

        def refunded() -> Refund:
            payment = self._payment(payment_id)
            if payment.status is not PaymentStatus.CAPTURED:
                raise FakeRefusal(f"{payment_id} was never taken; cancel it instead")
            paid = payment.amount_grosze
            fee = card_fee(paid) if withhold_fee else 0
            return Refund(
                refund_id=_id("re"),
                status=RefundStatus.SUCCEEDED,
                amount_grosze=paid - fee,
                fee_withheld_grosze=fee,
            )

        return self._once(
            idempotency_key,
            {"account": account_id, "payment_id": payment_id, "fee": withhold_fee},
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

    def _paid(
        self, account_id: str, method_id: str, amount_grosze: int, *, capture: bool
    ) -> Payment:
        source = self._clones.get(method_id, method_id)
        behaviour = self._method(source).card.behaviour
        payment_id = _id("pi")
        payment = _Payment(
            payment_id=payment_id,
            account_id=account_id,
            amount_grosze=amount_grosze,
            status=PaymentStatus.CAPTURED if capture else PaymentStatus.AUTHORISED,
            client_secret=f"{payment_id}_secret_{uuid4().hex[:12]}",
        )
        if behaviour is CardBehaviour.DECLINES_PAYMENTS:
            payment.status = PaymentStatus.DECLINED
            payment.decline_code = "generic_decline"
        elif behaviour is CardBehaviour.CHECKED_EVERY_TIME:
            payment.status = PaymentStatus.AUTHENTICATION_REQUIRED
        self._payments[payment_id] = payment
        return self._answer(payment)

    @staticmethod
    def _answer(payment: _Payment) -> Payment:
        return Payment(
            payment_id=payment.payment_id,
            status=payment.status,
            amount_grosze=payment.amount_grosze,
            client_secret=(
                payment.client_secret
                if payment.status is PaymentStatus.AUTHENTICATION_REQUIRED
                else None
            ),
            decline_code=payment.decline_code,
        )
