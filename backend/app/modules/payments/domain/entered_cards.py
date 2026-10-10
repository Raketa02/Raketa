"""The cards a phone can enter, in a payment provider's test mode.

**Stripe's own test cards, down to the last four digits** — the ones its test
mode answers as a real bank would: a card that saves and always pays, one the
bank refuses, one that saves and then declines every payment, and the two a bank
checks with 3-D Secure, once when saved or every time.

They are here, beside the port, rather than inside the fake because they are the
**vocabulary the port's demands are asked in**: the fake behaves as each would,
Stripe's test mode is confirmed with the matching test PaymentMethod
(``tests/demands/test_payments_demands.py``), and a seed says which one each of
its players typed (``app/seeds/payments.py``). A card number never reaches the
backend in any mode; this is the part of one a provider tells Raketa about,
plus how it will behave.

**And the kind of card it is** (ADR-0190's 2026-10-10 amendment): what Stripe
keeps on a payment depends on whether the card is a personal one issued in the
EU, a business card, a UK card or one from outside Europe, and a late leaver's
refund is the share less exactly that. Every test card is a personal EU one
unless a test says otherwise — the kind nine players in ten pay with.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final

from app.modules.payments.domain.provider import Wallet


class CardBehaviour(StrEnum):
    """What a test card does, after Stripe's own test cards."""

    #: Saved, and every payment goes through.
    SUCCEEDS = "SUCCEEDS"
    #: The bank refuses to save it.
    DECLINED_AT_SETUP = "DECLINED_AT_SETUP"
    #: Saved, and every payment on it is declined.
    DECLINES_PAYMENTS = "DECLINES_PAYMENTS"
    #: The bank checks it when it is saved; off-session payments then go
    #: through.
    CHECKED_AT_SETUP = "CHECKED_AT_SETUP"
    #: The bank checks it when it is saved and wants the player present for
    #: every payment.
    CHECKED_EVERY_TIME = "CHECKED_EVERY_TIME"


class CardKind(StrEnum):
    """Which price the provider charges on a card — the fee kept when its
    money is taken."""

    #: A personal card issued in the EU — Stripe's standard EEA price.
    PERSONAL_EU = "PERSONAL_EU"
    #: A business card issued in the EU.
    BUSINESS = "BUSINESS"
    #: A card issued in the United Kingdom.
    UK = "UK"
    #: A card issued outside Europe.
    OUTSIDE_EUROPE = "OUTSIDE_EUROPE"


@final
@dataclass(frozen=True, slots=True)
class EnteredCard:
    """A card as a phone entered it: what it is, how its bank answers, and
    which kind of card it is. ``brand`` is its network — ``visa`` or
    ``mastercard`` — which says how long a hold on it lasts."""

    brand: str = "visa"
    last_four: str = "4242"
    wallet: Wallet | None = None
    behaviour: CardBehaviour = CardBehaviour.SUCCEEDS
    kind: CardKind = CardKind.PERSONAL_EU


#: 4242 4242 4242 4242 — saved, and always pays.
A_CARD = EnteredCard()
#: 4000 0000 0000 0002 — the bank refuses it.
A_CARD_THE_BANK_DECLINES = EnteredCard(
    last_four="0002", behaviour=CardBehaviour.DECLINED_AT_SETUP
)
#: 4000 0000 0000 0341 — saved, and every payment declined.
A_CARD_THAT_DECLINES_LATER = EnteredCard(
    last_four="0341", behaviour=CardBehaviour.DECLINES_PAYMENTS
)
#: 4000 0025 0000 3155 — checked once, when saved.
A_CARD_THE_BANK_CHECKS_ONCE = EnteredCard(
    last_four="3155", behaviour=CardBehaviour.CHECKED_AT_SETUP
)
#: 4000 0027 6000 3184 — checked every time.
A_CARD_THE_BANK_ALWAYS_CHECKS = EnteredCard(
    last_four="3184", behaviour=CardBehaviour.CHECKED_EVERY_TIME
)
