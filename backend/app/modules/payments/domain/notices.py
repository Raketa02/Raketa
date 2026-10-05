"""What the payment provider tells Raketa on its own, after the fact.

A provider **notifies** — Stripe by webhook — about things that happened on its
side: a setup that succeeded while the app was closed, a card its bank replaced.
A notice arrives signed, **twice** as often as not, and **out of order**
(the mechanics Appendix A), so three rules hold every one of them:

- it is **verified before a byte of it is read**, and refused whole otherwise;
- it is **read once**: its id is recorded in the notice inbox in the same
  transaction as whatever it moved, so a second delivery finds it and does
  nothing (``NoticeInbox``);
- what it moves is **read from the provider as it stands**, never off the
  notice, and is **idempotent in its own right** — a setup saved twice is saved
  once, a card updated to what it already says records nothing — so a notice
  arriving late, or after the app already said the same thing, changes nothing
  it should not.

**Translated at the edge.** ``PaymentNotices`` reads the provider's own shape
and answers one of the notices below, in Raketa's words; a kind nothing here
listens to is ``Unheeded`` and is acknowledged all the same.

**Two endpoints, one reading.** The platform's notices — a setup, a card — and
the **Connected accounts** notices — a club's account, and later the payments
made on it — arrive at two endpoints, each signed with its own secret; both
are read by one ``PaymentNotices`` over that endpoint's secret, and acted on by
the one ``ReceivePaymentNotice``, so a notice is read once whichever it came
through.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable



@final
@dataclass(frozen=True, slots=True)
class SetupSucceeded:
    """A setup saved a card — the notice that saves it when the app never came
    back to say so."""

    notice_id: str
    customer_id: str
    setup_id: str


@final
@dataclass(frozen=True, slots=True)
class CardUpdatedByBank:
    """The bank updated a saved card: a new number, or a new brand. It names
    the card and carries none of it: two updates can arrive in either order, so
    the card is read from the provider as it stands, never off the notice."""

    notice_id: str
    customer_id: str
    method_id: str


@final
@dataclass(frozen=True, slots=True)
class ConnectedAccountChanged:
    """A club's account at the provider changed — its details, or whether it
    can take a payment and pay it out (#537). It names the account and carries
    nothing of it: two changes arrive in either order, so the account is read
    from the provider as it stands."""

    notice_id: str
    account_id: str


@final
@dataclass(frozen=True, slots=True)
class SeatPaymentChanged:
    """A payment on a club's account moved — held, taken, released, refused, or
    confirmed by its player in the app (#541). It names the payment and the
    account and carries nothing of it: two moves arrive in either order, so the
    payment is read from the provider as it stands, and folded onto its seat
    charge only forward."""

    notice_id: str
    account_id: str
    payment_id: str


@final
@dataclass(frozen=True, slots=True)
class Unheeded:
    """A notice of a kind nothing here acts on yet."""

    notice_id: str
    kind: str


Notice = (
    SetupSucceeded
    | CardUpdatedByBank
    | ConnectedAccountChanged
    | SeatPaymentChanged
    | Unheeded
)


@runtime_checkable
class PaymentNotices(Protocol):
    """Reads one notice off the wire, verified, or refuses it whole."""

    def read(self, payload: bytes, *, signature: str | None) -> Notice:
        """``payment_notice_refused`` for anything unsigned, signed with another
        secret or too old; ``payment_notices_not_configured`` where this
        process holds no secret to verify with."""
        ...
