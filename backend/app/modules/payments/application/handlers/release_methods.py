"""What a replaced or removed card, and a replaced setup, leave at the provider.

**After the commit, from the outbox, and never inline** — releasing is the
consequence of a change the stream already records, so it is a subscriber's,
retried until it lands: a provider that cannot be reached leaves the delivery to
be tried again, and a release the provider already made answers success
(``PaymentProvider.release_method``). Until it lands the card is still saved at
the provider and **nothing here will charge it**, because nothing reads a card
the stream no longer names.

The key is the card's own, so every retry is the same request.
"""

from __future__ import annotations

from app.application.events import DeliveryContext
from app.modules.payments.domain.events import (
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentSetupStarted,
)
from app.modules.payments.domain.provider import PaymentProvider, SetupStatus


def release_key(method_id: str) -> str:
    return f"raketa-release-{method_id}"


def cancel_key(setup_id: str) -> str:
    return f"raketa-cancel-{setup_id}"


class ReleaseMethodAtProvider:
    def __init__(self, provider: PaymentProvider) -> None:
        self._provider = provider

    async def __call__(
        self,
        event: PaymentMethodChanged | PaymentMethodRemoved,
        context: DeliveryContext,
    ) -> None:
        released = (
            event.previous_method_id
            if isinstance(event, PaymentMethodChanged)
            else event.method_id
        )
        await self._provider.release_method(
            released, idempotency_key=release_key(released)
        )


class SettleReplacedSetup:
    """A setup a newer one replaced is closed at the provider, so a phone still
    holding its secret cannot save a card with it that nobody records — and
    where one already did, that card is released. Either way it is the same
    retried, keyed request until it lands."""

    def __init__(self, provider: PaymentProvider) -> None:
        self._provider = provider

    async def __call__(
        self, event: PaymentSetupStarted, context: DeliveryContext
    ) -> None:
        replaced = event.replaced_setup_id
        if replaced is None:
            return
        reading = await self._provider.cancel_setup(
            replaced, idempotency_key=cancel_key(replaced)
        )
        if reading.status is SetupStatus.SUCCEEDED and reading.card is not None:
            await self._provider.release_method(
                reading.card.method_id,
                idempotency_key=release_key(reading.card.method_id),
            )
