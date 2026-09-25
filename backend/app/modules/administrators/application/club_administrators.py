"""The club's side of administrators (``docs/adr/0184`` §2, §6, §7): invite,
list, resend, reset a password, remove — each for **the signed-in club's own**
Administrators, and one transaction each.

**An Administrator of another club is not found here**, and neither is a
removed one: the desk's table lists neither, so there is nothing for it to act
on. Every email an act sends is written to the mail queue in the act's own
transaction (``docs/adr/0186`` §2).
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant
from app.modules.administrators.application.commands import (
    InviteAdministratorCommand,
)
from app.modules.administrators.application.sending import (
    AUDIENCE,
    InvitationSender,
)
from app.modules.administrators.application.views import (
    AdministratorRow,
    listing_of,
    row_of,
)
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorState,
)
from app.modules.administrators.domain.errors import (
    AdministratorAlsoPlays,
    AdministratorHasNoAccount,
    AdministratorNameInvalid,
    AdministratorNotFound,
)
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorDirectory,
    AdministratorRepository,
)
from app.modules.auth.application.sign_out_everywhere import SignOutEverywhere
from app.modules.users.domain.errors import EmailInvalid
from app.modules.users.domain.value_objects import Email, Name
from app.shared.ids import new_uuid


async def _row(
    administrator: Administrator, *, now: Instant, accounts: AccountHolders
) -> AdministratorRow:
    return await row_of(listing_of(administrator), now=now, accounts=accounts)


async def _administrator_of_club(
    administrators: AdministratorRepository, *, club_id: UUID, administrator_id: UUID
) -> Administrator:
    administrator = await administrators.load(administrator_id)
    if (
        administrator is None
        or administrator.club_id != club_id
        or administrator.state is AdministratorState.REMOVED
    ):
        raise AdministratorNotFound()
    return administrator


class InviteAdministrator:
    """The club names a person by name and email (``docs/adr/0184`` §2).

    Refused on the spot if that email is already *invited* — expired included
    — or *active* here. A removed person is invited again on the same stream.
    """

    def __init__(
        self,
        *,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sender: InvitationSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._administrators = administrators
        self._accounts = accounts
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(self, command: InviteAdministratorCommand) -> AdministratorRow:
        # In the form's order, so the first refusal is the first field read.
        try:
            name = Name(command.name)
        except ValueError:
            raise AdministratorNameInvalid() from None
        try:
            email = Email(command.email)
        except ValueError:
            raise EmailInvalid() from None

        now = self._clock.now()
        administrator = await self._administrators.at_club(command.club_id, email)
        if administrator is None:
            administrator = Administrator.invite(
                administrator_id=new_uuid(),
                club_id=command.club_id,
                email=email,
                name=name,
                occurred_at=now,
            )
        else:
            administrator.invite_again(name=name, occurred_at=now)
        await self._administrators.save(administrator)
        await self._sender.send(administrator, now=now)
        await self._uow.commit()
        return await _row(administrator, now=now, accounts=self._accounts)


class ListClubAdministrators:
    """The club's Administrators table: everybody not removed, by name."""

    def __init__(
        self,
        *,
        directory: AdministratorDirectory,
        accounts: AccountHolders,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._accounts = accounts
        self._clock = clock

    async def execute(self, club_id: UUID) -> list[AdministratorRow]:
        now = self._clock.now()
        listings = sorted(
            await self._directory.of_club(club_id),
            key=lambda listing: (listing.name.casefold(), listing.email, listing.id),
        )
        return [
            await row_of(listing, now=now, accounts=self._accounts)
            for listing in listings
        ]


class ResendInvitation:
    """A fresh 72 hours, for somebody *invited* or *expired*
    (``docs/adr/0184`` §2) — as the original: the reset's email again while a
    reset is what is waiting."""

    def __init__(
        self,
        *,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sender: InvitationSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._administrators = administrators
        self._accounts = accounts
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, administrator_id: UUID
    ) -> AdministratorRow:
        administrator = await _administrator_of_club(
            self._administrators, club_id=club_id, administrator_id=administrator_id
        )
        now = self._clock.now()
        administrator.resend(occurred_at=now)
        await self._administrators.save(administrator)
        await self._sender.send(administrator, now=now)
        await self._uow.commit()
        return await _row(administrator, now=now, accounts=self._accounts)


class ResetAdministratorPassword:
    """The club's *Reset password* (``docs/adr/0184`` §6).

    **Only for an account holding nothing but administrator profiles**, and
    refused for any account that also plays: the club made the one and may
    help recover it, and never made the other. It clears the password, signs
    the account out everywhere on the player app, and puts the person back to
    *invited* with a fresh 72-hour email carrying the invitation's own link and
    code — all in one transaction.
    """

    def __init__(
        self,
        *,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sign_out_everywhere: SignOutEverywhere,
        sender: InvitationSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._administrators = administrators
        self._accounts = accounts
        self._sign_out_everywhere = sign_out_everywhere
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, administrator_id: UUID
    ) -> AdministratorRow:
        administrator = await _administrator_of_club(
            self._administrators, club_id=club_id, administrator_id=administrator_id
        )
        account_id = administrator.account_id
        if account_id is None:
            raise AdministratorHasNoAccount()
        if await self._accounts.acts_as_player(account_id):
            raise AdministratorAlsoPlays()

        now = self._clock.now()
        administrator.reset_password(occurred_at=now)
        await self._accounts.clear_password(account_id, at=now)
        await self._sign_out_everywhere.execute(account_id, audience=AUDIENCE, now=now)
        await self._administrators.save(administrator)
        await self._sender.send(administrator, now=now)
        await self._uow.commit()
        return await _row(administrator, now=now, accounts=self._accounts)


class RemoveAdministrator:
    """End an administratorship (``docs/adr/0184`` §7). The next administrator
    request is refused; the person's player side and its sessions are
    untouched, and a link still in their inbox opens nothing."""

    def __init__(
        self,
        *,
        administrators: AdministratorRepository,
        sender: InvitationSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._administrators = administrators
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(self, *, club_id: UUID, administrator_id: UUID) -> None:
        administrator = await _administrator_of_club(
            self._administrators, club_id=club_id, administrator_id=administrator_id
        )
        now = self._clock.now()
        administrator.remove(occurred_at=now)
        await self._administrators.save(administrator)
        await self._sender.retire(administrator, now=now)
        await self._uow.commit()
