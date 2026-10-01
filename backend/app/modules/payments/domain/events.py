"""The Payment method stream: one per player, filed under the player's own id.

**Born by being used.** Nothing is written at sign-up; a player who never opened
the payment setup has no stream and folds to *no method*, which is exactly what
the You tab's *Not set up* says (``docs/adr/0189`` §5).

**No secret is on it** (``docs/adr/0184`` §4): the secret a phone confirms a
setup with is asked of the provider when it is needed and never recorded, and a
card number never reaches Raketa at all — only its brand and last four digits,
which every receipt prints. What is here is the provider's **ids** for the
player's customer, each setup and each saved card, and the **consent**: which
terms, when, and from which address.

Every event carries ``player_id``, the stream's own key, so a record read alone
still says whose it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PaymentSetupStarted:
    """The player opened the payment setup: the provider opened a **setup** —
    for off-session use — under the player's **customer**, opened with the first
    one and the same for every one after it.

    ``replaced_setup_id`` is the setup left open before this one, which saves
    nothing from now on and is cancelled at the provider after the commit — a
    phone still holding its secret could otherwise save a card nobody
    records."""

    player_id: UUID
    setup_id: str
    customer_id: str
    replaced_setup_id: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentTermsAccepted:
    """The player accepted the payment terms — *the club charges your share when
    a game fills* (the mechanics §12.5).

    ``setup_id`` is the setup they were accepted for, **before anything was
    saved**; ``None`` is the terms asked again for the method already saved,
    after its bank moved it to another brand. ``terms_version`` names the words
    shown and never carries them; ``ip`` is the address they were accepted
    from.
    """

    player_id: UUID
    terms_version: str
    ip: str | None
    setup_id: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentMethodSaved:
    """The setup saved the player's first method."""

    player_id: UUID
    setup_id: str
    method_id: str
    brand: str
    last_four: str
    wallet: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentMethodChanged:
    """A setup saved a new method over the old one, **which kept working until
    this moment** and is released at the provider after it."""

    player_id: UUID
    setup_id: str
    method_id: str
    brand: str
    last_four: str
    wallet: str | None
    previous_method_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentMethodRemoved:
    """The player removed their method. It is released at the provider after
    this, and can never be charged again."""

    player_id: UUID
    method_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentMethodUpdated:
    """The player's bank updated the saved card — a new card number, or a new
    brand — as the provider reported it. **A new brand asks for the terms
    again**, because a card whose brand changed cannot be charged off-session
    until its holder agrees again (the mechanics Appendix A); that is read off
    the stream, never recorded here."""

    player_id: UUID
    method_id: str
    brand: str
    last_four: str
    occurred_at: datetime


# --------------------------------------------------------------------------- #
# The Seat charge stream: one per payment for one player's share of one game
# --------------------------------------------------------------------------- #
#
# **Born at the fill** (#541; the mechanics §12.2), held or refused, and never
# before: a yes moves no money. Every event carries ``charge_id``, the stream's
# own key, and ``player_id``, whose share it is, so a record read alone still
# says whose money it is about. **No secret is on it**: the secret a phone
# confirms a payment with is asked of the provider when it is handed out.
#
# Two kinds of event, and the difference is load-bearing. **What the provider
# said** — ``Authorised``, ``Failed``, ``Confirmed``, ``Captured``,
# ``Cancelled`` — is read off the provider, by the fill or from a notice. **What
# Raketa decided** — ``Taken`` and ``Released`` — is the fill's verdict on the
# hold, recorded in the transaction that books the game or does not, and acted
# on at the provider **after** the commit by a subscriber, retried until it
# lands (``docs/adr/0190`` §4).


@dataclass(frozen=True)
class SeatChargeAuthorised:
    """A player's share was held on their card, off-session, on the club's
    account — the first half of the all-or-nothing fill. ``game_id`` is the
    proposal that filled, whose id its booking takes."""

    charge_id: UUID
    player_id: UUID
    game_id: UUID
    club_id: UUID
    #: The club's account at the provider — the seller's.
    account_id: str
    payment_id: str
    amount_grosze: int
    sport: str
    starts_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeFailed:
    """A player's share could not be held when the game filled: the bank
    refused, the bank wants the player present, or the player's method cannot
    be charged — no method, or a brand the terms were not accepted for, which
    asks the provider nothing (``payment_id`` is ``None``). **Nobody paid**, and
    the player is asked to confirm this payment to keep their seat."""

    charge_id: UUID
    player_id: UUID
    game_id: UUID
    club_id: UUID
    account_id: str
    payment_id: str | None
    amount_grosze: int
    sport: str
    starts_at: datetime
    #: ``AUTHENTICATION_REQUIRED``, ``DECLINED``, ``TERMS_NEEDED`` or
    #: ``NO_METHOD``.
    reason: str
    decline_code: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeConfirmed:
    """The player confirmed a failed payment in the app, and the provider holds
    it now — *confirming the same payment is your yes again* (§12.2)."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeTaken:
    """**The game booked, so the hold is taken.** Raketa's decision, recorded
    with the booking; captured at the provider after the commit."""

    charge_id: UUID
    player_id: UUID
    booking_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeReleased:
    """**The game did not book on it, so the hold is let go** — another seat
    failed, or somebody else took this one. Raketa's decision; cancelled at the
    provider after the commit, which costs nothing."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeCaptured:
    """The provider took the share — the player paid, the club the seller."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeCancelled:
    """The provider released the payment untaken, or there was nothing there to
    release."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeRefundDecided:
    """**The share is to be given back** (#544; the mechanics §12.3) — the
    player left before the club's cut-off, and the card fee is withheld; or the
    game was called off at its cut-off, and nothing is. Raketa's decision,
    recorded with the act that caused it; refunded at the provider after the
    commit, which says what it gave back."""

    charge_id: UUID
    player_id: UUID
    #: The card fee the provider never returns is kept back — a leaver's — or
    #: the share goes back whole.
    withhold_fee: bool
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeRefunded:
    """The provider gave the share back: ``amount_grosze`` to the player, and
    ``fee_withheld_grosze`` kept — the card fee, nought on a refund in full."""

    charge_id: UUID
    player_id: UUID
    refund_id: str
    amount_grosze: int
    fee_withheld_grosze: int
    occurred_at: datetime
