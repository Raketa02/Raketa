from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.payments.application.handlers import (
    LogPaymentEvent,
    ReleaseMethodAtProvider,
    SettleReplacedSetup,
)
from app.modules.payments.domain.events import (
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
)
from app.modules.payments.domain.provider import PaymentProvider

_EVENTS = (
    (PaymentSetupStarted, "payments.setup_started"),
    (PaymentTermsAccepted, "payments.terms_accepted"),
    (PaymentMethodSaved, "payments.method_saved"),
    (PaymentMethodChanged, "payments.method_changed"),
    (PaymentMethodRemoved, "payments.method_removed"),
    (PaymentMethodUpdated, "payments.method_updated"),
)


def register_payment_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_payment_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(PaymentSetupStarted, LogPaymentEvent())
    dispatcher.subscribe(PaymentTermsAccepted, LogPaymentEvent())
    dispatcher.subscribe(PaymentMethodSaved, LogPaymentEvent())
    dispatcher.subscribe(PaymentMethodChanged, LogPaymentEvent())
    dispatcher.subscribe(PaymentMethodRemoved, LogPaymentEvent())
    dispatcher.subscribe(PaymentMethodUpdated, LogPaymentEvent())


def subscribe_the_method_releaser(
    dispatcher: EventDispatcher, provider: PaymentProvider
) -> None:
    """The payments subscribers that need the provider, so they are added per
    delivery run over the provider **that run** holds — the API's, or a seed
    run's fake — exactly as the room teller is added over its session
    (``app/bootstrap/events.py``)."""

    releaser = ReleaseMethodAtProvider(provider)
    dispatcher.subscribe(PaymentMethodChanged, releaser)
    dispatcher.subscribe(PaymentMethodRemoved, releaser)
    dispatcher.subscribe(PaymentSetupStarted, SettleReplacedSetup(provider))
