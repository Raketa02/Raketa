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


@dataclass(frozen=True)
class MaximumAgreed:
    """**The most a friends game's sender agreed to pay**, recorded with their
    terms acceptance (#751; ``docs/adr/0202`` §6): the sender's own share and a
    cover for every other seat — the whole court, *We hold 100 zł on your card
    until Fri 10:00* — for the game ``booking_id``, under the terms they
    accepted, ``terms_version``. The Payment Services Act's art. 49b allows a
    hold only for an amount its payer agreed to; this is that consent."""

    player_id: UUID
    booking_id: UUID
    amount_grosze: int
    terms_version: str
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
#
# **One share, and one payment at a time** (#639): a share checked at the fill
# (``Checked``) is held again at its Holding time on a new payment
# (``HeldAgain``), or refused there (``HoldingRefused``) — the stream's payment
# is the latest, and the check's was let go.


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
    #: When the hold ends unless it is taken — the provider's ``last_moment``
    #: (ADR-0190's 2026-10-10 amendment). ``None`` where the provider did not
    #: say, and on every hold recorded before it was asked: a default rather
    #: than a version 2, since a row without it is such a hold.
    last_moment: datetime | None = None
    #: **A Cover** (#751; ``docs/adr/0202`` §6): a friends game's sender's hold
    #: for a seat that isn't theirs — ``player_id`` is the payer, not the
    #: seat's player. ``False`` on every share, and on every row recorded
    #: before: a default, since a row without it is a share.
    cover: bool = False


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
    #: A cover the sender's card refused at send (#751), as on
    #: ``SeatChargeAuthorised``.
    cover: bool = False


@dataclass(frozen=True)
class SeatChargeConfirmed:
    """The player confirmed a failed payment in the app, and the provider holds
    it now — *confirming the same payment is your yes again* (§12.2)."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime
    #: When the hold the player confirmed ends unless it is taken — as on
    #: ``SeatChargeAuthorised``, and ``None`` on the same terms.
    last_moment: datetime | None = None


@dataclass(frozen=True)
class SeatChargeKept:
    """**The game booked on this hold, which is kept on the card until the
    club's cut-off** (#637; ADR-0189's 2026-10-10 amendment) — and taken then.
    Raketa's decision, recorded with the booking; nothing moves at the
    provider. Not paid: leaving before ``until`` lets it go, and nothing is
    taken."""

    charge_id: UUID
    player_id: UUID
    booking_id: UUID
    #: The club's cut-off, as the booking holds it: when the share is taken.
    until: datetime
    occurred_at: datetime
    #: A share refused at its Holding time and fixed in time by its player
    #: (#639): the game was told *It's a game!* when it filled, so nobody is
    #: told again. ``False`` on every keep recorded before.
    fixed: bool = False


@dataclass(frozen=True)
class SeatChargeChecked:
    """**A Card check** (#639; the mechanics Q113): the game booked on this
    hold before its club's cut-off, and the hold would not last until it — its
    last moment less than six hours past the cut-off. It is **let go at once**,
    which proves the money was there that day, and the share is held again at
    ``hold_at``, its Holding time, to stay until ``until``, the cut-off. Raketa's
    decision, recorded with the booking; ``payment_id`` — the check's — is
    cancelled at the provider after the commit. Nothing was taken."""

    charge_id: UUID
    player_id: UUID
    booking_id: UUID
    payment_id: str
    #: The club's cut-off, as the booking holds it: when the share is taken.
    until: datetime
    #: The Holding time: four days before the cut-off.
    hold_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeHeldAgain:
    """**The Holding time came, and the checked share is held again** (#639) —
    on a new payment, ``payment_id``, held until ``last_moment`` — to be taken
    at ``until``: the cut-off, or, a hold that still would not reach it, its
    last safe moment (the fallback). What the provider said, read inline by the
    holding job; nothing is taken."""

    charge_id: UUID
    player_id: UUID
    payment_id: str
    until: datetime
    occurred_at: datetime
    last_moment: datetime | None = None


@dataclass(frozen=True)
class SeatChargeHoldingRefused:
    """**The Holding time came, and the checked share could not be held**
    (#639): the bank refused, wants the player present, or the method cannot
    be charged — which asks the provider nothing (``payment_id`` is ``None``).
    The game stays booked while its player has their **time to fix the card**;
    nothing is paid in it. ``game_id`` and ``amount_grosze`` say whose game and
    what, as on ``SeatChargeFailed``."""

    charge_id: UUID
    player_id: UUID
    game_id: UUID
    payment_id: str | None
    amount_grosze: int
    #: ``AUTHENTICATION_REQUIRED``, ``DECLINED``, ``TERMS_NEEDED`` or
    #: ``NO_METHOD``.
    reason: str
    decline_code: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class SeatChargeTaken:
    """**The share is taken.** Raketa's decision — the game booked after its
    cut-off, or the cut-off came — recorded in that act's transaction; captured
    at the provider after the commit."""

    charge_id: UUID
    player_id: UUID
    booking_id: UUID
    occurred_at: datetime
    #: Taken at the cut-off off a hold kept for the booked game (#637), not at
    #: the fill: nobody is told *It's a game!* again. ``False`` on every take
    #: recorded before holds were kept — each was a fill's.
    kept: bool = False


@dataclass(frozen=True)
class SeatChargeReleased:
    """**The hold is let go** — the game did not book on it (another seat
    failed, or somebody else took this one), or a share held for the booked
    game is given up before the cut-off: a leave, a game short at it, the
    club's cancel (#637). Raketa's decision; cancelled at the provider after
    the commit, which costs nothing."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime
    #: Why a held share was let go — the ``RefundReason`` code its giving back
    #: was decided for (#637). ``None`` for an undecided hold the game did not
    #: book on, and on every release recorded before: a default rather than a
    #: version 2, since every such row is one.
    reason: str | None = None


@dataclass(frozen=True)
class SeatChargeCaptured:
    """The provider took the share — the player paid, the club the seller."""

    charge_id: UUID
    player_id: UUID
    occurred_at: datetime
    #: The card fee the provider took on it, which the club pays (#548) —
    #: ``None`` where it did not say, and on every capture recorded before it
    #: was asked: a default rather than a version 2, since every row written
    #: without it is exactly such a capture, and the estimate stands in.
    fee_grosze: int | None = None


@dataclass(frozen=True)
class SeatChargeFeeReported:
    """**The provider reported the real fee it kept on a share already taken**
    (ADR-0190's 2026-10-10 amendment) — a club on its own negotiated pricing is
    told its fee later than the capture, which recorded it *not yet known*."""

    charge_id: UUID
    player_id: UUID
    fee_grosze: int
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
    #: Why — the ``RefundReason`` code: ``LEFT``, ``CALLED_OFF_AT_THE_CUT_OFF``,
    #: ``SEAT_TAKEN``, ``CANCELLED_BY_THE_CLUB`` or ``CANCELLED_AFTER_YOU_LEFT``
    #: (#623). ``None`` on every decision recorded before it was kept: a
    #: default rather than a version 2, since a row without it is a refund
    #: decided in the past, read for nothing new.
    reason: str | None = None


@dataclass(frozen=True)
class SeatChargeRefunded:
    """The provider gave the share back: ``amount_grosze`` to the player, and
    ``fee_withheld_grosze`` kept — the fee kept on that payment, nought on a
    refund in full. Raketa asked for exactly that amount."""

    charge_id: UUID
    player_id: UUID
    refund_id: str
    amount_grosze: int
    fee_withheld_grosze: int
    occurred_at: datetime


# --------------------------------------------------------------------------- #
# The Club payout stream: one per club per day it is paid for (#548)
# --------------------------------------------------------------------------- #
#
# **The club is paid after the game is played** (the mechanics §12.6, §16.11).
# Its share of every game waits on its account at the provider — a refund before
# the start comes out of it — until the close of a day, when everything its
# games over and settled left it is **paid out** to its bank in one payout.
# Two events, the same two kinds as a refund's: **what Raketa decided**
# (``Decided``: the games and the amount, recorded in the job's transaction)
# and **what the provider said** (``Sent``: its payout, on its way — made from
# the outbox after the commit, as a refund is).


def _uuids(values: tuple[UUID, ...]) -> tuple[UUID, ...]:
    # JSON hands a list of strings back; the codec coerces a bare ``UUID`` hint
    # and nothing inside a tuple.
    return tuple(UUID(str(value)) for value in values)


@dataclass(frozen=True)
class ClubPayoutDecided:
    """**The club's money for these games is its own now**: every one is over
    — played, or called off and given back — and nothing about its money is
    still on its way, so ``amount_grosze`` — what the players paid, less what
    was given back, less the card fees — is to go to the club's bank. ``day``
    is the club day (``YYYY-MM-DD``) whose close decided it."""

    payout_id: UUID
    club_id: UUID
    account_id: str
    day: str
    amount_grosze: int
    game_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "game_ids", _uuids(self.game_ids))


@dataclass(frozen=True)
class ClubPayoutSent:
    """The provider took the payout: ``provider_payout_id`` is on its way to
    the club's bank, expected by ``arrives_at``."""

    payout_id: UUID
    club_id: UUID
    provider_payout_id: str
    arrives_at: datetime
    occurred_at: datetime
