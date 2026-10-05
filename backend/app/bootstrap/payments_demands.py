"""The register of payment providers, and the one question every one of them answers.

**An eleventh register, and a kind of its own.** The other ten hold ports one
context declares of another, answered over the database; this one holds the
**two adapters of one port** onto the outside world — the fake that local runs,
seeds and every API test stand on, and Stripe — so the suite in
``tests/demands/test_payments_demands.py`` asks both the same questions and a
fake that drifts from the provider goes red rather than green. A row carries a
builder over the **settings**, not over a session: a provider holds no
database, and whether Stripe can be asked at all is a fact about which keys a
person has placed (#533).

**A row can be absent, and says why.** Stripe is built only with a test key —
never a live one, which would move real money — and is otherwise skipped by
name, so a run reports which half of the contract it did not check. The fake is
never absent, and the suite asserts that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.bootstrap.composition import build_fake_payments, build_stripe_payments
from app.core.config import STRIPE_TEST_KEY_PREFIXES, Settings
from app.modules.payments.domain.provider import PaymentProvider


@dataclass(frozen=True)
class RegisteredProvider:
    """One adapter of the payment provider, and how to build it here.

    ``name`` is the class's own, so a failure reads as the implementation that
    broke the contract. ``build`` answers ``None`` where this adapter cannot be
    asked, and ``absent_because`` is what the skip says then.
    """

    name: str
    build: Callable[[Settings], PaymentProvider | None]
    absent_because: str


def _stripe_in_test_mode(settings: Settings) -> PaymentProvider | None:
    key = settings.STRIPE_SECRET_KEY
    if not key or not key.startswith(STRIPE_TEST_KEY_PREFIXES):
        return None
    return build_stripe_payments(settings)


PAYMENTS_IMPLEMENTATIONS: tuple[RegisteredProvider, ...] = (
    RegisteredProvider(
        name="FakePayments",
        build=lambda settings: build_fake_payments(),
        absent_because="never — the fake always runs",
    ),
    RegisteredProvider(
        name="StripePayments",
        build=_stripe_in_test_mode,
        absent_because=(
            "no Stripe test key is placed — STRIPE_SECRET_KEY must start with "
            f"{' or '.join(STRIPE_TEST_KEY_PREFIXES)} (#533)"
        ),
    ),
)


__all__ = ["PAYMENTS_IMPLEMENTATIONS", "RegisteredProvider"]
