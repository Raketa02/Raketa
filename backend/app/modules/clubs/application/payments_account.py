"""Connecting the club's payments, and keeping what the provider says of it
(#537, the mechanics §16.2, the screens B2).

**The desk asks, and the provider decides.** Asking opens the club's account at
the provider the first time — once, for ever — and answers a link to the
provider's own hosted pages; the club fills them in there and comes back.
Whether the account can take a payment and pay it out is the provider's to
say, by notice (``HeedPaymentsAccount``), and **every link also reads the
account as it stands**, because a notice can be late or lost: *Continue with
Stripe* must find a club the provider has already finished with, and a club
recorded ready is asked about before it is refused one — or a lost notice
would leave the desk no way back to the provider's pages.

**What is written, the provider was asked first.** An account the provider
opened is recorded and committed before the link is asked for, so a link that
fails leaves the account the next try continues; a link that could not be made
records nothing more. The read after the link is not the response, and is
still inline: it is what a desk back from the provider's pages sees at once,
and it costs one call.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.application.ports.mail import MailQueue
from app.kernel import Clock, Instant, invariant
from app.modules.clubs.application.club_details import the_club
from app.modules.clubs.application.commands import ConnectPaymentsCommand
from app.modules.clubs.application.payments_email import (
    payments_need_attention_email,
)
from app.modules.clubs.domain.errors import PaymentsAlreadyConnected
from app.modules.clubs.domain.payments_account import (
    OnboardingPages,
    PaymentsStatus,
    needs_attention,
)
from app.modules.clubs.domain.ports import (
    ClubAccountRepository,
    ClubCourtsRepository,
    ClubRepository,
    PaymentsAccounts,
)


class ConnectPayments:
    """*Connect with Stripe*, or *Continue with Stripe*: a link to the
    provider's pages for the club's one account. Refused once the provider
    says the account is ready — there is nothing left to fill in."""

    def __init__(
        self,
        *,
        clubs: ClubRepository,
        courts: ClubCourtsRepository,
        payments_accounts: PaymentsAccounts,
        pages: OnboardingPages,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._courts = courts
        self._payments_accounts = payments_accounts
        self._pages = pages
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ConnectPaymentsCommand) -> str:
        club = await self._courts.load(command.club_id)
        now = self._clock.now()
        if club.payments is None:
            name = (await the_club(self._clubs, command.club_id)).details.name
            opened = await self._payments_accounts.open(
                club_id=command.club_id,
                name=name.value,
                email=command.email,
                asked_at=now,
            )
            club.open_payments_account(opened, occurred_at=now)
            await self._courts.save(club)
            await self._uow.commit()
        account_id = invariant(club.payments, "an account opened above").account_id
        if club.payments_status is PaymentsStatus.READY:
            standing = await self._payments_accounts.status_of(account_id)
            if standing is PaymentsStatus.READY:
                raise PaymentsAlreadyConnected()
            club.record_payments_status(standing, occurred_at=now)
        url = await self._payments_accounts.onboarding_link(
            account_id, pages=self._pages
        )
        club.record_payments_status(
            await self._payments_accounts.status_of(account_id), occurred_at=now
        )
        await self._courts.save(club)
        await self._uow.commit()
        return url


class HeedPaymentsAccount:
    """The provider said a club's account changed: read it **as it stands** —
    never off the notice, which arrives out of order — and record it; and for
    an account that was ready and is not, queue *Stripe needs something from
    you* for the desk.

    **In the caller's transaction, and never committed here**: the notice's
    inbox row and what it moved commit together (``docs/adr/0190`` §3), so the
    webhook that reads the notice is the one that commits."""

    def __init__(
        self,
        *,
        clubs: ClubRepository,
        club_accounts: ClubAccountRepository,
        courts: ClubCourtsRepository,
        payments_accounts: PaymentsAccounts,
        mail: MailQueue,
        pages: OnboardingPages,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._club_accounts = club_accounts
        self._courts = courts
        self._payments_accounts = payments_accounts
        self._mail = mail
        self._pages = pages
        self._clock = clock

    async def execute(self, account_id: str) -> bool:
        """``True`` once heeded, ``False`` for an account no club here holds."""

        club_id = await self._courts.club_of_payments_account(account_id)
        if club_id is None:
            return False
        club = await self._courts.load(club_id)
        was = club.payments_status
        now_is = await self._payments_accounts.status_of(account_id)
        now = self._clock.now()
        club.record_payments_status(now_is, occurred_at=now)
        await self._courts.save(club)
        if needs_attention(was, now_is):
            await self._tell_the_desk(club_id, at=now)
        return True

    async def _tell_the_desk(self, club_id: UUID, *, at: Instant) -> None:
        desk = await self._club_accounts.get_by_club(club_id)
        if desk is None:
            # A club is signed up with its account, in one transaction.
            raise RuntimeError(f"club {club_id} has no account to email")
        name = (await the_club(self._clubs, club_id)).details.name
        await self._mail.enqueue(
            payments_need_attention_email(
                to=desk.email.value, club=name.value, link=self._pages.refresh_url
            ),
            at=at,
        )
