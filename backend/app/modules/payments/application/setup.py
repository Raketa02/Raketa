"""Saving a payment method: start the setup, accept the terms, confirm the save.

**The order is the rule** (the mechanics §12.5, the screens A7.3): the player
chooses how to pay and types a card into the provider's own fields, **accepts
the terms**, and confirms with their bank — and that last step is the one that
saves. Two things make *the terms are accepted before anything is saved*
structural rather than a promise the app keeps:

- **the setup's secret is handed out only by the acceptance.** Starting a setup
  answers its id and the publishable key the phone opens its fields with; the
  secret that confirms it — the only way a phone can save anything — is the
  answer to accepting the terms for it, and to nothing else;
- **the save refuses a setup without them**, whichever way the save arrives —
  this use case, or the provider's notice that the setup succeeded.

**The provider is asked inline where the answer is the response**, and before
anything is written: a setup that could not be opened records nothing, and a
save reads the setup's outcome before recording it. What happens *after* a
change or a removal — releasing the old card at the provider — is a handler's,
after the commit (``handlers/release_methods.py``), and so is cancelling a setup
a newer one replaced.

**A key is the act and the hour it is asked in.** The customer's names the
player, a setup's counts the setups that player started, and both carry the
hour: a request retried after a timeout within the hour asks for the object the
first try opened, and the next setup asks for a new one. **The hour is the cost
of a stored failure**: Stripe replays the first answer to a key for a day,
errors included, so a key that never changed would keep one passing outage
between a player and their card for a day, where this keeps it to the hour. What
an hour boundary can cost is an orphan — a customer or a setup opened twice, one
of them recorded — and neither can be charged (the mechanics Appendix A:
*Raketa's own records must prevent duplicates*).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant
from app.modules.payments.application.commands import AcceptPaymentTermsCommand
from app.modules.payments.domain.errors import (
    PaymentMethodDeclined,
    PaymentSetupNotFinished,
    PaymentSetupNotStarted,
    PaymentTermsNotAccepted,
)
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.ports import PaymentMethodRepository
from app.modules.payments.domain.provider import (
    PaymentProvider,
    SetupReading,
    SetupStatus,
)
from app.modules.payments.domain.terms import PAYMENT_TERMS_VERSION


@dataclass(frozen=True, slots=True)
class SetupOpened:
    """What the phone needs to show the card fields: the setup's id, the key its
    provider fields open with, and the version of the terms it must show."""

    setup_id: str
    publishable_key: str
    terms_version: str


def key_hour(at: Instant) -> str:
    """The hour a key is asked in (``docs/adr/0190`` §4)."""

    return at.strftime("%Y%m%d%H")


def customer_key(player_id: UUID, *, at: Instant) -> str:
    return f"raketa-customer-{player_id}-{key_hour(at)}"


def setup_key(player_id: UUID, ordinal: int, *, at: Instant) -> str:
    return f"raketa-setup-{player_id}-{ordinal}-{key_hour(at)}"


def club_account_key(club_id: UUID, *, at: Instant) -> str:
    """A club's account at the provider: opened once, so the club and the hour
    are the whole key (#537)."""

    return f"raketa-club-account-{club_id}-{key_hour(at)}"


class StartPaymentSetup:
    """The player opened the payment setup — the first time, or to change the
    method they have, which keeps working until the new one is saved."""

    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        provider: PaymentProvider,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._methods = methods
        self._provider = provider
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID) -> SetupOpened:
        now = self._clock.now()
        payment_method = await self._methods.load(player_id)
        payment_method.refuse_when_setups_exhausted(at=now)
        customer_id = payment_method.customer_id or await self._provider.open_customer(
            player_id=player_id, idempotency_key=customer_key(player_id, at=now)
        )
        started = await self._provider.start_setup(
            customer_id=customer_id,
            player_id=player_id,
            idempotency_key=setup_key(
                player_id, payment_method.setups_counted + 1, at=now
            ),
        )
        payment_method.start_setup(
            setup_id=started.setup_id, customer_id=customer_id, at=now
        )
        await self._methods.save(payment_method)
        await self._uow.commit()
        return SetupOpened(
            setup_id=started.setup_id,
            publishable_key=self._provider.publishable_key(),
            terms_version=PAYMENT_TERMS_VERSION,
        )


class AcceptPaymentTerms:
    """The player accepted the terms — for the open setup, whose secret is then
    handed out, or again for the method already saved, after its bank moved it
    to another brand or the terms in force changed (#637)."""

    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        provider: PaymentProvider,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._methods = methods
        self._provider = provider
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AcceptPaymentTermsCommand) -> str | None:
        """The secret that confirms the setup, or ``None`` when the terms were
        accepted for the method already saved and there is nothing to confirm.

        **Recorded first, and the secret asked for after the commit**, so a
        provider that cannot be reached costs a retry and never an acceptance
        nobody recorded; the retry records nothing twice."""

        payment_method = await self._methods.load(command.player_id)
        setup_id = payment_method.accept_terms(
            terms_version=command.terms_version,
            ip=command.ip,
            at=self._clock.now(),
        )
        await self._methods.save(payment_method)
        await self._uow.commit()
        if setup_id is None:
            return None
        return (await self._provider.read_setup(setup_id)).client_secret


class ConfirmPaymentSetup:
    """The phone says the bank is done: read the setup's outcome from the
    provider, and save the card it saved."""

    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        provider: PaymentProvider,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._methods = methods
        self._provider = provider
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID) -> PaymentMethod:
        payment_method = await self._methods.load(player_id)
        setup = payment_method.setup
        if setup is None:
            if payment_method.method is not None:
                # Confirmed already — by this call retried, or by the
                # provider's notice arriving first.
                return payment_method
            raise PaymentSetupNotStarted()
        if setup.terms is None:
            raise PaymentTermsNotAccepted()
        reading = await self._provider.read_setup(setup.setup_id)
        saved_from(payment_method, reading, at=self._clock.now())
        await self._methods.save(payment_method)
        await self._uow.commit()
        return payment_method


def saved_from(
    payment_method: PaymentMethod, reading: SetupReading, *, at: Instant
) -> None:
    """Record the card a setup saved, or refuse with where the setup stands."""

    match reading.status:
        case SetupStatus.SUCCEEDED:
            assert reading.card is not None
            payment_method.save(setup_id=reading.setup_id, card=reading.card, at=at)
        case SetupStatus.DECLINED:
            raise PaymentMethodDeclined()
        case SetupStatus.CANCELLED:
            raise PaymentSetupNotStarted()
        case (
            SetupStatus.AWAITING_THE_PHONE
            | SetupStatus.AUTHENTICATING
            | SetupStatus.PROCESSING
        ):
            raise PaymentSetupNotFinished(status=reading.status.value)
