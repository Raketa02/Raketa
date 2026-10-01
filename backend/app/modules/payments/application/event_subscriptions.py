from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.payments.application.handlers import (
    LogPaymentEvent,
    LogSeatChargeEvent,
    ReleaseMethodAtProvider,
    SettleReplacedSetup,
    SettleSeatCharges,
)
from app.modules.payments.domain.events import (
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
    SeatChargeAuthorised,
    SeatChargeCancelled,
    SeatChargeCaptured,
    SeatChargeConfirmed,
    SeatChargeFailed,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.domain.provider import PaymentProvider

_EVENTS = (
    (PaymentSetupStarted, "payments.setup_started"),
    (PaymentTermsAccepted, "payments.terms_accepted"),
    (PaymentMethodSaved, "payments.method_saved"),
    (PaymentMethodChanged, "payments.method_changed"),
    (PaymentMethodRemoved, "payments.method_removed"),
    (PaymentMethodUpdated, "payments.method_updated"),
    (SeatChargeAuthorised, "payments.seat_charge_authorised"),
    (SeatChargeFailed, "payments.seat_charge_failed"),
    (SeatChargeConfirmed, "payments.seat_charge_confirmed"),
    (SeatChargeTaken, "payments.seat_charge_taken"),
    (SeatChargeReleased, "payments.seat_charge_released"),
    (SeatChargeCaptured, "payments.seat_charge_captured"),
    (SeatChargeCancelled, "payments.seat_charge_cancelled"),
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
    dispatcher.subscribe(SeatChargeAuthorised, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeFailed, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeConfirmed, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeTaken, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeReleased, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeCaptured, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeCancelled, LogSeatChargeEvent())


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


def subscribe_the_seat_charge_settler(
    dispatcher: EventDispatcher, settle: SettleSeatCharges
) -> None:
    """The subscriber that captures a taken hold and cancels a released one at
    the provider (#541) — it **writes** the provider's answer onto the charge,
    so it is added per delivery run over that run's session and provider, as the
    method releaser is."""

    dispatcher.subscribe(SeatChargeTaken, settle)
    dispatcher.subscribe(SeatChargeReleased, settle)
