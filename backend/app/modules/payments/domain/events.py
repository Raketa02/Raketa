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
