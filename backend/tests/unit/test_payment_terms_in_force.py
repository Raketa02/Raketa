"""**The fill holds only a player who accepted the terms in force** (#637; the
mechanics §12.5, Q113).

The terms got a new version when the share came to be held at the fill and
taken at the cut-off. A player who accepted an older version has their card
saved and is still asked again before their next game holds anything: their
method waits on the terms (``terms_needed``), which the fill reads as
``TERMS_NEEDED`` without asking the provider — and accepting the version in
force, through the same press as for a card of a new brand, answers it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.kernel import instant
from app.modules.payments.domain.events import (
    PaymentMethodSaved,
    PaymentSetupStarted,
    PaymentTermsAccepted,
)
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.terms import PAYMENT_TERMS_VERSION

AT = instant(datetime(2026, 10, 1, 9, tzinfo=timezone.utc))
LATER = instant(datetime(2026, 10, 12, 9, tzinfo=timezone.utc))

#: The words a player accepted before the share was held until the cut-off.
BEFORE_Q113 = "2026-09-29"


def a_method_saved_under(version: str) -> PaymentMethod:
    player = uuid4()
    return PaymentMethod.from_history(
        player,
        [
            PaymentSetupStarted(
                player_id=player,
                setup_id="seti_1",
                customer_id="cus_1",
                replaced_setup_id=None,
                occurred_at=AT,
            ),
            PaymentTermsAccepted(
                player_id=player,
                terms_version=version,
                ip=None,
                setup_id="seti_1",
                occurred_at=AT,
            ),
            PaymentMethodSaved(
                player_id=player,
                setup_id="seti_1",
                method_id="pm_1",
                brand="visa",
                last_four="4242",
                wallet=None,
                occurred_at=AT,
            ),
        ],
    )


def test_the_terms_in_force_are_a_newer_version_than_before_q113():
    assert PAYMENT_TERMS_VERSION > BEFORE_Q113


def test_a_card_saved_under_the_terms_in_force_needs_nothing():
    assert a_method_saved_under(PAYMENT_TERMS_VERSION).terms_needed is False


def test_a_card_saved_under_older_terms_waits_on_the_terms_in_force():
    method = a_method_saved_under(BEFORE_Q113)

    assert method.terms_needed is True


def test_accepting_the_terms_in_force_answers_a_card_saved_under_older_ones():
    method = a_method_saved_under(BEFORE_Q113)

    answered = method.accept_terms(
        terms_version=PAYMENT_TERMS_VERSION, ip="203.0.113.7", at=LATER
    )

    assert answered is None  # no setup was open: the saved card's terms
    assert method.terms_needed is False
    [accepted] = method.pull_events()
    assert isinstance(accepted, PaymentTermsAccepted)
    assert (accepted.terms_version, accepted.setup_id) == (PAYMENT_TERMS_VERSION, None)
