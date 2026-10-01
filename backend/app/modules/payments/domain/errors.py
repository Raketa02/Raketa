"""The Payments context's refusals.

**A player is saving a card, so every refusal says what to do next** — and the
client chooses the sentence from the code (``docs/adr/0187`` §6). None of them
names a card number, a provider id or the secret a setup is confirmed with.
"""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain import AppError, ConflictError, NotFoundError


class PaymentsUnavailable(AppError):
    """The payment provider could not be reached, or answered with an outage.

    A 503 and never a 500, because it is transient and about the platform: the
    same request, retried, is the remedy. **Nothing was recorded** — every use
    case asks the provider before it writes, or writes what it already knows
    and asks after, so a retry finds either nothing done or everything.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "payments_unavailable"

    def __init__(
        self, message: str = "The payment provider could not be reached."
    ) -> None:
        super().__init__(message)


class PaymentSetupNotStarted(ConflictError):
    """Nothing is being set up: the terms or the save were asked for with no
    setup open — never started, or cancelled at the provider. Start one."""

    code = "payment_setup_not_started"

    def __init__(self) -> None:
        super().__init__("no payment setup is open; start one")


class PaymentTermsNotAccepted(ConflictError):
    """**The terms are accepted before anything is saved** (the mechanics
    §12.5): a save asked for before them is refused, and nothing is saved."""

    code = "payment_terms_not_accepted"

    def __init__(self) -> None:
        super().__init__("the payment terms have not been accepted for this setup")


class PaymentTermsOutdated(ConflictError):
    """The player was shown words that are no longer the terms in force. Show
    them the current ones — the version is on the setup's answer."""

    code = "payment_terms_outdated"

    def __init__(self, *, in_force: str) -> None:
        super().__init__(
            "these are not the payment terms in force",
            details={"terms_version": in_force},
        )


class PaymentSetupNotFinished(ConflictError):
    """The provider has not saved the card yet: the phone has not confirmed it,
    the bank's one-time check is not done, or the provider is still deciding.
    ``details.status`` says which; finish it on the phone and ask again."""

    code = "payment_setup_not_finished"

    def __init__(self, *, status: str) -> None:
        super().__init__(
            "the payment setup has not finished", details={"status": status}
        )


class PaymentMethodDeclined(ConflictError):
    """The bank refused the card. Nothing was saved, and the same setup can be
    tried again with another card."""

    code = "payment_method_declined"

    def __init__(self) -> None:
        super().__init__("the bank declined this card; try another")


class PaymentMethodNotFound(NotFoundError):
    """The player has no saved method."""

    code = "payment_method_not_found"

    def __init__(self) -> None:
        super().__init__("no payment method is saved")


class PaymentMethodInUse(ConflictError):
    """**Remove** is refused while anything could still be charged to it — a
    live yes, which charges when its game fills, or a booked game still ahead
    (the mechanics §12.5). ``details`` counts both, which is the reason the
    screen gives."""

    code = "payment_method_in_use"

    def __init__(self, *, live_yeses: int, upcoming_games: int) -> None:
        super().__init__(
            "the payment method is still needed",
            details={"live_yeses": live_yeses, "upcoming_games": upcoming_games},
        )


class PaymentSetupsExhausted(AppError):
    """Too many setups started in a day — the card-testing guard
    (``domain/terms.py``). Nothing was asked of the provider; try tomorrow."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "payment_setups_exhausted"

    def __init__(self) -> None:
        super().__init__("too many payment setups were started today")


class PaymentNoticeRefused(AppError):
    """A notice arrived at the webhook without a valid signature — unsigned,
    signed with another secret, or too old. Nothing was read out of it."""

    status_code = HTTPStatus.BAD_REQUEST
    code = "payment_notice_refused"

    def __init__(self) -> None:
        super().__init__("the notice's signature could not be verified")


class PaymentNoticesNotConfigured(AppError):
    """This process holds no webhook secret, so it can verify nothing and
    reads nothing. A laptop running on the fake is exactly this."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "payment_notices_not_configured"

    def __init__(self) -> None:
        super().__init__("no webhook secret is configured here")


class SeatChargeNotFound(NotFoundError):
    """No such charge **for this player**: it does not exist, or it is somebody
    else's share. One code for both."""

    code = "seat_charge_not_found"

    def __init__(self) -> None:
        super().__init__("no such seat charge")


class PaymentNotConfirmed(ConflictError):
    """The payment still waits for its player at the provider — the bank's
    check was not finished, or the other card was refused too. ``details.status``
    says which; confirm it in the app and ask again. A charge that was never a
    payment — terms to accept again, or no method — is ``NOTHING_TO_CONFIRM``,
    and the remedy is the setup, then a yes."""

    code = "payment_not_confirmed"

    def __init__(self, *, status: str) -> None:
        super().__init__(
            "the payment has not been confirmed", details={"status": status}
        )
