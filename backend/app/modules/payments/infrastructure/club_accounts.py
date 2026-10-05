"""The Club context's account at the provider — answered, and told — by this
context, which holds the provider (#537).

**Two directions, one arrow.** A club records its own payments account
(``docs/adr/0189`` §5: *the Stripe account link* is on the Club courts stream),
and it asks for it in its own words — ``PaymentsAccounts``: open one, a link to
the provider's pages, the state it stands in. The provider is this context's,
so the answer is signed here. And when the provider's Connected accounts
notice says an account changed, this context hears it and tells the club, in
**its** own words — ``ConnectedAccounts`` — over the Club context's own use
case. Both live here, so ``clubs`` imports nothing of ``payments`` and the
arrow runs ``payments → clubs`` only.
"""

from __future__ import annotations

from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.clubs.application.payments_account import HeedPaymentsAccount
from app.modules.clubs.domain.payments_account import OnboardingPages, PaymentsStatus
from app.modules.payments.application.setup import club_account_key
from app.modules.payments.domain.provider import ClubAccountStatus, PaymentProvider

#: The provider's three states and the club's, which are the same three —
#: spelled twice because each context speaks its own words.
_STATUSES: Final = {
    ClubAccountStatus.NOT_STARTED: PaymentsStatus.NOT_STARTED,
    ClubAccountStatus.NEEDS_DETAILS: PaymentsStatus.NEEDS_DETAILS,
    ClubAccountStatus.READY: PaymentsStatus.READY,
}


@final
class ProviderPaymentsAccounts:
    """The Club context's ``PaymentsAccounts``, over the payment provider."""

    def __init__(self, provider: PaymentProvider) -> None:
        self._provider = provider

    async def open(
        self, *, club_id: UUID, name: str, email: str, asked_at: Instant
    ) -> str:
        # A key is the act and the hour (``docs/adr/0190`` §4), built here
        # because it is the provider's word and never the club's.
        return await self._provider.open_club_account(
            club_id=club_id,
            name=name,
            email=email,
            idempotency_key=club_account_key(club_id, at=asked_at),
        )

    async def onboarding_link(self, account_id: str, *, pages: OnboardingPages) -> str:
        return await self._provider.onboarding_link(
            account_id, refresh_url=pages.refresh_url, return_url=pages.return_url
        )

    async def status_of(self, account_id: str) -> PaymentsStatus:
        return _STATUSES[(await self._provider.read_club_account(account_id)).status]


@final
class ClubsConnectedAccounts:
    """This context's ``ConnectedAccounts``, over the Club context's own use
    case for what its account became."""

    def __init__(self, heed: HeedPaymentsAccount) -> None:
        self._heed = heed

    async def heed(self, account_id: str) -> bool:
        return await self._heed.execute(account_id)
