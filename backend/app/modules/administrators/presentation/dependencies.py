"""When each administrators adapter and use case is built — one per request —
and **the administrator guard** every administrator operation declares.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    OneTimeCredentialsDep,
    PasswordHasherDep,
    SettingsDep,
    SignOutEverywhereDep,
    TokenRotatorDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_account_holders,
    build_administrator_directory,
    build_administrator_repository,
    build_club_names,
    build_invitation_sender,
    build_official_group_assignments,
)
from app.modules.administrators.application.administratorship import (
    ActiveAdministratorship,
    ReadAdministratorProfile,
)
from app.modules.administrators.application.club_administrators import (
    InviteAdministrator,
    ListClubAdministrators,
    RemoveAdministrator,
    ResendInvitation,
    ResetAdministratorPassword,
)
from app.modules.administrators.application.invitations import (
    AcceptInvitation,
    ClaimInvitation,
    ReadInvitationByToken,
    SetInvitationPassword,
    SetInvitationPasswordWithoutSigningIn,
)
from app.modules.administrators.application.profiles import ReadAccountProfiles
from app.modules.administrators.application.sending import InvitationSender
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorDirectory,
    AdministratorListing,
    AdministratorRepository,
    ClubNames,
    OfficialGroupAssignments,
)
from app.modules.users.presentation.dependencies import CurrentUserDep


def get_administrator_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> AdministratorRepository:
    return build_administrator_repository(db, event_store=event_store, events=events)


AdministratorRepositoryDep = Annotated[
    AdministratorRepository, Depends(get_administrator_repository)
]


def get_administrator_directory(db: DbSession) -> AdministratorDirectory:
    return build_administrator_directory(db)


AdministratorDirectoryDep = Annotated[
    AdministratorDirectory, Depends(get_administrator_directory)
]


def get_account_holders(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> AccountHolders:
    return build_account_holders(db, event_store=event_store, events=events)


AccountHoldersDep = Annotated[AccountHolders, Depends(get_account_holders)]


def get_club_names(db: DbSession) -> ClubNames:
    return build_club_names(db)


ClubNamesDep = Annotated[ClubNames, Depends(get_club_names)]


def get_invitation_sender(
    db: DbSession,
    settings: SettingsDep,
    accounts: AccountHoldersDep,
    credentials: OneTimeCredentialsDep,
) -> InvitationSender:
    return build_invitation_sender(
        db, settings, accounts=accounts, credentials=credentials
    )


InvitationSenderDep = Annotated[InvitationSender, Depends(get_invitation_sender)]


# --- The club surface ----------------------------------------------------------


def get_invite_administrator(
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    sender: InvitationSenderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> InviteAdministrator:
    return InviteAdministrator(
        administrators=administrators,
        accounts=accounts,
        sender=sender,
        uow=uow,
        clock=clock,
    )


InviteAdministratorDep = Annotated[
    InviteAdministrator, Depends(get_invite_administrator)
]


def get_official_group_assignments(db: DbSession) -> OfficialGroupAssignments:
    return build_official_group_assignments(db)


OfficialGroupAssignmentsDep = Annotated[
    OfficialGroupAssignments, Depends(get_official_group_assignments)
]


def get_list_club_administrators(
    directory: AdministratorDirectoryDep,
    accounts: AccountHoldersDep,
    groups: OfficialGroupAssignmentsDep,
    clock: ClockDep,
) -> ListClubAdministrators:
    return ListClubAdministrators(
        directory=directory, accounts=accounts, groups=groups, clock=clock
    )


ListClubAdministratorsDep = Annotated[
    ListClubAdministrators, Depends(get_list_club_administrators)
]


def get_resend_invitation(
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    sender: InvitationSenderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ResendInvitation:
    return ResendInvitation(
        administrators=administrators,
        accounts=accounts,
        sender=sender,
        uow=uow,
        clock=clock,
    )


ResendInvitationDep = Annotated[ResendInvitation, Depends(get_resend_invitation)]


def get_reset_administrator_password(
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    sign_out_everywhere: SignOutEverywhereDep,
    sender: InvitationSenderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ResetAdministratorPassword:
    return ResetAdministratorPassword(
        administrators=administrators,
        accounts=accounts,
        sign_out_everywhere=sign_out_everywhere,
        sender=sender,
        uow=uow,
        clock=clock,
    )


ResetAdministratorPasswordDep = Annotated[
    ResetAdministratorPassword, Depends(get_reset_administrator_password)
]


def get_remove_administrator(
    administrators: AdministratorRepositoryDep,
    sender: InvitationSenderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RemoveAdministrator:
    return RemoveAdministrator(
        administrators=administrators, sender=sender, uow=uow, clock=clock
    )


RemoveAdministratorDep = Annotated[
    RemoveAdministrator, Depends(get_remove_administrator)
]


# --- The player surface --------------------------------------------------------


def get_claim_invitation(
    credentials: OneTimeCredentialsDep,
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ClaimInvitation:
    return ClaimInvitation(
        credentials=credentials,
        administrators=administrators,
        accounts=accounts,
        uow=uow,
        clock=clock,
    )


ClaimInvitationDep = Annotated[ClaimInvitation, Depends(get_claim_invitation)]


def get_set_invitation_password(
    credentials: OneTimeCredentialsDep,
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    sign_out_everywhere: SignOutEverywhereDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> SetInvitationPassword:
    return SetInvitationPassword(
        credentials=credentials,
        administrators=administrators,
        accounts=accounts,
        sign_out_everywhere=sign_out_everywhere,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


SetInvitationPasswordDep = Annotated[
    SetInvitationPassword, Depends(get_set_invitation_password)
]


def get_read_invitation_by_token(
    credentials: OneTimeCredentialsDep,
    administrators: AdministratorRepositoryDep,
    clubs: ClubNamesDep,
    clock: ClockDep,
) -> ReadInvitationByToken:
    return ReadInvitationByToken(
        credentials=credentials, administrators=administrators, clubs=clubs, clock=clock
    )


ReadInvitationByTokenDep = Annotated[
    ReadInvitationByToken, Depends(get_read_invitation_by_token)
]


def get_accept_invitation(
    administrators: AdministratorRepositoryDep,
    sender: InvitationSenderDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AcceptInvitation:
    return AcceptInvitation(
        administrators=administrators, sender=sender, uow=uow, clock=clock
    )


AcceptInvitationDep = Annotated[AcceptInvitation, Depends(get_accept_invitation)]


def get_read_account_profiles(
    directory: AdministratorDirectoryDep,
    accounts: AccountHoldersDep,
    clubs: ClubNamesDep,
    groups: OfficialGroupAssignmentsDep,
    clock: ClockDep,
) -> ReadAccountProfiles:
    # Declared here rather than in the users context that serves it on `/me`,
    # because *what* is built is this context's answer — as the Player
    # profile's `HasPlayerProfile` is declared in its own context.
    return ReadAccountProfiles(
        directory=directory, accounts=accounts, clubs=clubs, groups=groups, clock=clock
    )


ReadAccountProfilesDep = Annotated[
    ReadAccountProfiles, Depends(get_read_account_profiles)
]


def get_read_administrator_profile(clubs: ClubNamesDep) -> ReadAdministratorProfile:
    return ReadAdministratorProfile(clubs=clubs)


ReadAdministratorProfileDep = Annotated[
    ReadAdministratorProfile, Depends(get_read_administrator_profile)
]


def get_active_administratorship(
    directory: AdministratorDirectoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ActiveAdministratorship:
    return ActiveAdministratorship(directory=directory, uow=uow, clock=clock)


ActiveAdministratorshipDep = Annotated[
    ActiveAdministratorship, Depends(get_active_administratorship)
]


async def administrator_at(
    club_id: UUID, user: CurrentUserDep, guard: ActiveAdministratorshipDep
) -> AdministratorListing:
    """**The administrator guard** (``docs/adr/0184`` §7): the signed-in
    account's active administratorship at the club the path names, **read on
    every request**, or ``403 not_an_administrator``.

    Every administrator operation declares it, and takes the club from its own
    path as ``club_id`` — so an operation cannot name one club and be checked
    against another."""

    return await guard.execute(account_id=user.id, club_id=club_id)


AdministratorAtClubDep = Annotated[AdministratorListing, Depends(administrator_at)]


# --- The public surface --------------------------------------------------------


def get_set_invitation_password_without_signing_in(
    credentials: OneTimeCredentialsDep,
    administrators: AdministratorRepositoryDep,
    accounts: AccountHoldersDep,
    sign_out_everywhere: SignOutEverywhereDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetInvitationPasswordWithoutSigningIn:
    return SetInvitationPasswordWithoutSigningIn(
        credentials=credentials,
        administrators=administrators,
        accounts=accounts,
        sign_out_everywhere=sign_out_everywhere,
        hasher=hasher,
        uow=uow,
        clock=clock,
    )


SetInvitationPasswordWithoutSigningInDep = Annotated[
    SetInvitationPasswordWithoutSigningIn,
    Depends(get_set_invitation_password_without_signing_in),
]
