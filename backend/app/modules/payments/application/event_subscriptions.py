from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.payments.application.handlers import (
    LogClubPayoutEvent,
    LogPaymentEvent,
    SendClubPayout,
    LogSeatChargeEvent,
    ReleaseMethodAtProvider,
    SettleReplacedSetup,
    SettleSeatCharges,
)
from app.modules.payments.domain.events import (
    ClubPayoutDecided,
    ClubPayoutSent,
    MaximumAgreed,
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
    SeatChargeAuthorised,
    SeatChargeCancelled,
    SeatChargeCaptured,
    SeatChargeChecked,
    SeatChargeConfirmed,
    SeatChargeFailed,
    SeatChargeFeeReported,
    SeatChargeHeldAgain,
    SeatChargeHoldingRefused,
    SeatChargeKept,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
)
from app.modules.payments.application.refunds import EmailTheSeatTakenRefund
from app.modules.payments.domain.provider import PaymentProvider

_EVENTS = (
    (PaymentSetupStarted, "payments.setup_started"),
    (PaymentTermsAccepted, "payments.terms_accepted"),
    (PaymentMethodSaved, "payments.method_saved"),
    (PaymentMethodChanged, "payments.method_changed"),
    (PaymentMethodRemoved, "payments.method_removed"),
    (PaymentMethodUpdated, "payments.method_updated"),
    (MaximumAgreed, "payments.maximum_agreed"),
    (SeatChargeAuthorised, "payments.seat_charge_authorised"),
    (SeatChargeFailed, "payments.seat_charge_failed"),
    (SeatChargeConfirmed, "payments.seat_charge_confirmed"),
    (SeatChargeKept, "payments.seat_charge_kept"),
    (SeatChargeChecked, "payments.seat_charge_checked"),
    (SeatChargeHeldAgain, "payments.seat_charge_held_again"),
    (SeatChargeHoldingRefused, "payments.seat_charge_holding_refused"),
    (SeatChargeTaken, "payments.seat_charge_taken"),
    (SeatChargeReleased, "payments.seat_charge_released"),
    (SeatChargeCaptured, "payments.seat_charge_captured"),
    (SeatChargeCancelled, "payments.seat_charge_cancelled"),
    (SeatChargeFeeReported, "payments.seat_charge_fee_reported"),
    (SeatChargeRefundDecided, "payments.seat_charge_refund_decided"),
    (SeatChargeRefunded, "payments.seat_charge_refunded"),
    (ClubPayoutDecided, "payments.club_payout_decided"),
    (ClubPayoutSent, "payments.club_payout_sent"),
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
    dispatcher.subscribe(MaximumAgreed, LogPaymentEvent())
    dispatcher.subscribe(SeatChargeAuthorised, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeFailed, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeConfirmed, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeKept, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeChecked, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeHeldAgain, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeHoldingRefused, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeTaken, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeReleased, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeCaptured, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeCancelled, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeFeeReported, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeRefundDecided, LogSeatChargeEvent())
    dispatcher.subscribe(SeatChargeRefunded, LogSeatChargeEvent())
    dispatcher.subscribe(ClubPayoutDecided, LogClubPayoutEvent())
    dispatcher.subscribe(ClubPayoutSent, LogClubPayoutEvent())


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
    the provider (#541), and gives a paid share back (#544) — it **writes** the
    provider's answer onto the charge, so it is added per delivery run over that
    run's session and provider, as the method releaser is."""

    dispatcher.subscribe(SeatChargeTaken, settle)
    dispatcher.subscribe(SeatChargeReleased, settle)
    dispatcher.subscribe(SeatChargeRefundDecided, settle)
    # A Card check's hold is let go at once (#639).
    dispatcher.subscribe(SeatChargeChecked, settle)


def subscribe_the_seat_taken_refund_emailer(
    dispatcher: EventDispatcher, email: EmailTheSeatTakenRefund
) -> None:
    """The subscriber that emails a seat-taken refund once it is made (#641):
    its sum is known to the grosz only then. It **writes** the mail queue, so it
    is added per delivery run over that run's session, as the settler is."""

    dispatcher.subscribe(SeatChargeRefunded, email)


def subscribe_the_club_payout_sender(
    dispatcher: EventDispatcher, send: SendClubPayout
) -> None:
    """The subscriber that makes a club's payout at the provider and tells its
    desk (#548) — it **writes** the provider's answer onto the payout, so it is
    added per delivery run over that run's session and provider, as the seat
    charge settler is."""

    dispatcher.subscribe(ClubPayoutDecided, send)
