"""The club's payments account: where it is paid as the seller (#537, the
mechanics §16.2, the screens B2).

**The club is the seller** (``docs/adr/0189`` §4): every share is charged on the
club's own account at the payment provider, so nothing can be sold until that
account can take a payment and pay it out. Raketa opens the account; the club
fills in the provider's own hosted pages — company, representative, bank — and
comes back; **the provider decides when it is ready**, and may later decide it
is not.

**Three states, in the words the Overview draws them** — not started, *Stripe
needs more details*, ready — and the provider's own detail stays the
provider's: a club's page is where it answers, never Raketa's.

**Recorded on the Club courts stream** (``docs/adr/0189`` §5, *the Stripe account
link*), because the setup checklist is a fold over that one stream and *live*
must not be a second fact kept somewhere else.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final


class PaymentsStatus(StrEnum):
    """Where the club's payments account stands."""

    #: No account yet, or one whose pages the club has not submitted.
    NOT_STARTED = "NOT_STARTED"
    #: Submitted, and the provider wants more before it can take a payment and
    #: pay it out — or wanted more again later, after it was ready.
    NEEDS_DETAILS = "NEEDS_DETAILS"
    #: It can take a share and pay it out: the checklist's first step is done.
    READY = "READY"


@final
@dataclass(frozen=True, slots=True)
class PaymentsAccount:
    """The club's account at the provider — its id there, and its state."""

    account_id: str
    status: PaymentsStatus


def needs_attention(was: PaymentsStatus, now: PaymentsStatus) -> bool:
    """**An account that was taking payments and stopped** is the one the club
    is emailed about at once (the mechanics §16.12, *Stripe needs something from
    you*). A club still in the middle of the provider's pages is not: its own
    Overview says *Stripe needs more details*, and it is there."""

    return was is PaymentsStatus.READY and now is not PaymentsStatus.READY


#: The club website's pages the provider sends the desk back to.
RETURN_PATH: Final = "/overview"
REFRESH_PATH: Final = "/payments/continue"


@final
@dataclass(frozen=True, slots=True)
class OnboardingPages:
    """Where the provider's hosted pages send the desk: **back to the
    Overview** when it leaves them, and to the club website's *continue* page
    when the link is spent or stale — which asks for a fresh one and follows it,
    since a link works once. The address is configuration, normalised here so
    a trailing slash in a setting is the same site."""

    site: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "site", self.site.rstrip("/"))

    @property
    def return_url(self) -> str:
        return f"{self.site}{RETURN_PATH}"

    @property
    def refresh_url(self) -> str:
        return f"{self.site}{REFRESH_PATH}"
