"""Sending an invitation — the invite, a resend and the club's reset all end
here, so the three decide *which email* by one rule.

**The account decides, at the moment of sending, and nothing records it**:

- an address with an account that can sign in is asked to **accept in the
  app**, with no credential and no code (``docs/adr/0184`` §2) — and any link
  still live for this Administrator is retired, because the app is the way in
  now;
- otherwise somebody has a password to set, so a **credential** is issued and
  its link and code are emailed: the club's reset while one is pending
  (``docs/adr/0184`` §6), and the invitation for everybody else — a new
  person, or an account a club has cleared.

Each credential retires every live one of both kinds for the same
Administrator, so the newest email is the only one that opens anything. The
email is written to the mail queue in the caller's transaction; nothing here
sends and nothing here commits.

**A removal ends here too** (``docs/adr/0191`` §4): every live link retired,
and a notice that says so — *removed* to somebody who ran the club's groups,
*withdrawn* to somebody still invited.
"""

from __future__ import annotations

from typing import Final

from app.application.ports import MailQueue
from app.kernel import Instant
from app.modules.administrators.application.invitation_emails import (
    club_reset_email,
    existing_account_email,
    new_person_email,
)
from app.modules.administrators.application.removal_emails import (
    removed_email,
    withdrawn_email,
)
from app.modules.administrators.domain.administrator import Administrator
from app.modules.administrators.domain.ports import (
    AccountHolders,
    ClubNames,
    InvitationLinks,
    club_name_of,
)
from app.modules.auth.application.one_time_credentials import OneTimeCredentials
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.one_time_credential import CredentialPurpose

#: The two kinds of credential an Administrator's email carries, which open the
#: same page for the same person (``docs/adr/0186`` §3).
ADMINISTRATOR_CREDENTIALS: Final = frozenset(
    {CredentialPurpose.INVITATION, CredentialPurpose.CLUB_RESET}
)

#: An administrator profile runs under the player app's audience
#: (``docs/adr/0185`` §6): the credential and the session it opens are that
#: surface's.
AUDIENCE: Final = Audience.PLAYER_APP


class InvitationSender:
    def __init__(
        self,
        *,
        accounts: AccountHolders,
        credentials: OneTimeCredentials,
        mail: MailQueue,
        clubs: ClubNames,
        links: InvitationLinks,
    ) -> None:
        self._accounts = accounts
        self._credentials = credentials
        self._mail = mail
        self._clubs = clubs
        self._links = links

    async def send(self, administrator: Administrator, *, now: Instant) -> None:
        club_name = await club_name_of(self._clubs, administrator.club_id)
        to = administrator.email.value
        holder = await self._accounts.holder_of(administrator.email)
        if holder is not None and holder.can_sign_in:
            await self.retire(administrator, now=now)
            await self._mail.enqueue(
                existing_account_email(
                    to=to, club_name=club_name, app_link=self._links.app()
                ),
                at=now,
            )
            return

        purpose = (
            CredentialPurpose.CLUB_RESET
            if administrator.reset_pending
            else CredentialPurpose.INVITATION
        )
        prepared = self._credentials.prepare()
        await self._credentials.issue(
            prepared,
            purpose=purpose,
            audience=AUDIENCE,
            subject_id=administrator.id,
            email=to,
            now=now,
            retiring=ADMINISTRATOR_CREDENTIALS,
        )
        write = (
            club_reset_email
            if purpose is CredentialPurpose.CLUB_RESET
            else new_person_email
        )
        await self._mail.enqueue(
            write(
                to=to,
                name=administrator.name.value,
                club_name=club_name,
                link=self._links.invitation(prepared.token),
                code=prepared.code,
            ),
            at=now,
        )

    async def send_removal(self, administrator: Administrator, *, now: Instant) -> None:
        """The removal's notice, for an Administrator just removed: every live
        link retired, and the email that says what happened.

        **Whether they ran its groups is whether they took up the invitation**
        — an account on the administratorship, which the club's reset keeps
        and a new invitation clears — so it is read off the Administrator as
        the removal left it, and nothing records which email went."""

        await self.retire(administrator, now=now)
        write = withdrawn_email if administrator.account_id is None else removed_email
        await self._mail.enqueue(
            write(
                to=administrator.email.value,
                name=administrator.name.value,
                club_name=await club_name_of(self._clubs, administrator.club_id),
            ),
            at=now,
        )

    async def retire(self, administrator: Administrator, *, now: Instant) -> None:
        """Every live link and code for this Administrator, ended now — what an
        acceptance in the app and a removal do to an email still in an inbox."""

        await self._credentials.retire(
            administrator.id,
            purposes=ADMINISTRATOR_CREDENTIALS,
            audience=AUDIENCE,
            now=now,
        )
