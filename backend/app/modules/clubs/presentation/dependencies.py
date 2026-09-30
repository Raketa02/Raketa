from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    MailQueueDep,
    OneTimeCredentialsDep,
    PasswordHasherDep,
    RefreshTokenRepositoryDep,
    SettingsDep,
    SignOutEverywhereDep,
    TokenRotatorDep,
    TokenServiceDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_club_account_passwords,
    build_club_account_repository,
    build_club_account_session_holders,
    build_club_courts_repository,
    build_club_repository,
    build_court_bookings,
    build_official_group_sports,
)
from app.core.security import BearerCredentialsDep
from app.modules.auth.application.forgot_password import (
    ClaimPasswordReset,
    RequestPasswordReset,
    SetNewPassword,
)
from app.modules.auth.application.logout import Logout
from app.modules.auth.application.refresh_token import RefreshAuthTokens
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.password_reset import ResetPage
from app.modules.auth.domain.ports import PasswordAccounts, SessionHolders
from app.modules.clubs.application.club_courts import (
    AddCourt,
    ChangeCourt,
    ReadClubCourts,
    ReadSetup,
    RemoveCourt,
    SetRaketaHours,
)
from app.modules.clubs.application.prices import ReadPrices, SetPrices
from app.modules.clubs.application.raketa_settings import (
    ChooseWayOfWorking,
    SaveRaketaSettings,
)
from app.modules.clubs.application.hours_exceptions import (
    AddException,
    ReadExceptions,
    RemoveException,
)
from app.modules.clubs.application.club_details import (
    ChangeClubDetails,
    ReadClubDetails,
)
from app.modules.clubs.application.resolve_club_account import (
    ResolveClubAccountFromAccessToken,
)
from app.modules.clubs.application.sign_in_club import SignInClub
from app.modules.clubs.application.sign_up_club import SignUpClub
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.ports import (
    ClubAccountRepository,
    ClubCourtsRepository,
    ClubRepository,
    CourtBookings,
)


def get_club_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ClubRepository:
    return build_club_repository(db, event_store=event_store, events=events)


ClubRepositoryDep = Annotated[ClubRepository, Depends(get_club_repository)]


def get_club_account_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ClubAccountRepository:
    return build_club_account_repository(db, event_store=event_store, events=events)


ClubAccountRepositoryDep = Annotated[
    ClubAccountRepository, Depends(get_club_account_repository)
]


def get_sign_up_club(
    clubs: ClubRepositoryDep,
    accounts: ClubAccountRepositoryDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SignUpClub:
    return SignUpClub(
        clubs=clubs, accounts=accounts, hasher=hasher, uow=uow, clock=clock
    )


SignUpClubDep = Annotated[SignUpClub, Depends(get_sign_up_club)]


def get_read_club_details(clubs: ClubRepositoryDep) -> ReadClubDetails:
    return ReadClubDetails(clubs=clubs)


ReadClubDetailsDep = Annotated[ReadClubDetails, Depends(get_read_club_details)]


# --- Club courts: courts, hours, exceptions, prices, settings (#535) ---------


def get_club_courts_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ClubCourtsRepository:
    return build_club_courts_repository(db, event_store=event_store, events=events)


ClubCourtsRepositoryDep = Annotated[
    ClubCourtsRepository, Depends(get_club_courts_repository)
]


def get_read_club_courts(courts: ClubCourtsRepositoryDep) -> ReadClubCourts:
    return ReadClubCourts(courts=courts)


ReadClubCourtsDep = Annotated[ReadClubCourts, Depends(get_read_club_courts)]


def get_read_setup(courts: ClubCourtsRepositoryDep) -> ReadSetup:
    return ReadSetup(courts=courts)


ReadSetupDep = Annotated[ReadSetup, Depends(get_read_setup)]


def get_read_exceptions(
    courts: ClubCourtsRepositoryDep, clock: ClockDep
) -> ReadExceptions:
    return ReadExceptions(courts=courts, clock=clock)


ReadExceptionsDep = Annotated[ReadExceptions, Depends(get_read_exceptions)]


def get_add_court(
    clubs: ClubRepositoryDep,
    courts: ClubCourtsRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AddCourt:
    return AddCourt(clubs=clubs, courts=courts, uow=uow, clock=clock)


AddCourtDep = Annotated[AddCourt, Depends(get_add_court)]


def get_court_bookings() -> CourtBookings:
    return build_court_bookings()


CourtBookingsDep = Annotated[CourtBookings, Depends(get_court_bookings)]


def get_change_court(
    clubs: ClubRepositoryDep,
    courts: ClubCourtsRepositoryDep,
    bookings: CourtBookingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeCourt:
    return ChangeCourt(
        clubs=clubs, courts=courts, bookings=bookings, uow=uow, clock=clock
    )


ChangeCourtDep = Annotated[ChangeCourt, Depends(get_change_court)]


def get_remove_court(
    courts: ClubCourtsRepositoryDep,
    bookings: CourtBookingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RemoveCourt:
    return RemoveCourt(courts=courts, bookings=bookings, uow=uow, clock=clock)


RemoveCourtDep = Annotated[RemoveCourt, Depends(get_remove_court)]


def get_set_raketa_hours(
    courts: ClubCourtsRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SetRaketaHours:
    return SetRaketaHours(courts=courts, uow=uow, clock=clock)


SetRaketaHoursDep = Annotated[SetRaketaHours, Depends(get_set_raketa_hours)]


def get_change_club_details(
    db: DbSession,
    clubs: ClubRepositoryDep,
    courts: ClubCourtsRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ChangeClubDetails:
    return ChangeClubDetails(
        clubs=clubs,
        courts=courts,
        groups=build_official_group_sports(db),
        uow=uow,
        clock=clock,
    )


ChangeClubDetailsDep = Annotated[ChangeClubDetails, Depends(get_change_club_details)]


def get_add_exception(
    courts: ClubCourtsRepositoryDep,
    bookings: CourtBookingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AddException:
    return AddException(courts=courts, bookings=bookings, uow=uow, clock=clock)


AddExceptionDep = Annotated[AddException, Depends(get_add_exception)]


def get_remove_exception(
    courts: ClubCourtsRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> RemoveException:
    return RemoveException(courts=courts, uow=uow, clock=clock)


RemoveExceptionDep = Annotated[RemoveException, Depends(get_remove_exception)]


def get_read_prices(
    clubs: ClubRepositoryDep, courts: ClubCourtsRepositoryDep
) -> ReadPrices:
    return ReadPrices(clubs=clubs, courts=courts)


ReadPricesDep = Annotated[ReadPrices, Depends(get_read_prices)]


def get_set_prices(
    clubs: ClubRepositoryDep,
    courts: ClubCourtsRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetPrices:
    return SetPrices(clubs=clubs, courts=courts, uow=uow, clock=clock)


SetPricesDep = Annotated[SetPrices, Depends(get_set_prices)]


def get_choose_way_of_working(
    courts: ClubCourtsRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ChooseWayOfWorking:
    return ChooseWayOfWorking(courts=courts, uow=uow, clock=clock)


ChooseWayOfWorkingDep = Annotated[
    ChooseWayOfWorking, Depends(get_choose_way_of_working)
]


def get_save_raketa_settings(
    courts: ClubCourtsRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SaveRaketaSettings:
    return SaveRaketaSettings(courts=courts, uow=uow, clock=clock)


SaveRaketaSettingsDep = Annotated[SaveRaketaSettings, Depends(get_save_raketa_settings)]


# --- The club's session: the auth use cases, built for the club audience -----


def get_sign_in_club(
    accounts: ClubAccountRepositoryDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
) -> SignInClub:
    return SignInClub(accounts=accounts, hasher=hasher, rotator=rotator)


SignInClubDep = Annotated[SignInClub, Depends(get_sign_in_club)]


def get_club_session_holders(accounts: ClubAccountRepositoryDep) -> SessionHolders:
    return build_club_account_session_holders(accounts)


ClubSessionHoldersDep = Annotated[SessionHolders, Depends(get_club_session_holders)]


def get_refresh_club_tokens(
    holders: ClubSessionHoldersDep,
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> RefreshAuthTokens:
    return RefreshAuthTokens(
        audience=Audience.CLUB,
        holders=holders,
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


RefreshClubTokensDep = Annotated[RefreshAuthTokens, Depends(get_refresh_club_tokens)]


def get_sign_out_club(
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> Logout:
    return Logout(
        audience=Audience.CLUB,
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


SignOutClubDep = Annotated[Logout, Depends(get_sign_out_club)]


# --- Forgot password?, for the club website (docs/adr/0184 §5) ----------------


def get_club_password_accounts(
    accounts: ClubAccountRepositoryDep,
) -> PasswordAccounts:
    return build_club_account_passwords(accounts)


ClubPasswordAccountsDep = Annotated[
    PasswordAccounts, Depends(get_club_password_accounts)
]


def get_request_club_password_reset(
    accounts: ClubPasswordAccountsDep,
    credentials: OneTimeCredentialsDep,
    mail: MailQueueDep,
    settings: SettingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RequestPasswordReset:
    return RequestPasswordReset(
        audience=Audience.CLUB,
        accounts=accounts,
        credentials=credentials,
        mail=mail,
        # The club website's own *Set a new password* page, because clubs
        # already use that site (#522's correction to #500).
        reset_page=ResetPage(settings.CLUB_WEBSITE_URL),
        uow=uow,
        clock=clock,
    )


RequestClubPasswordResetDep = Annotated[
    RequestPasswordReset, Depends(get_request_club_password_reset)
]


def get_claim_club_password_reset(
    credentials: OneTimeCredentialsDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ClaimPasswordReset:
    return ClaimPasswordReset(
        audience=Audience.CLUB, credentials=credentials, uow=uow, clock=clock
    )


ClaimClubPasswordResetDep = Annotated[
    ClaimPasswordReset, Depends(get_claim_club_password_reset)
]


def get_set_new_club_password(
    accounts: ClubPasswordAccountsDep,
    credentials: OneTimeCredentialsDep,
    sign_out_everywhere: SignOutEverywhereDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> SetNewPassword:
    return SetNewPassword(
        audience=Audience.CLUB,
        accounts=accounts,
        credentials=credentials,
        sign_out_everywhere=sign_out_everywhere,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


SetNewClubPasswordDep = Annotated[SetNewPassword, Depends(get_set_new_club_password)]


def get_resolve_club_account(
    token_service: TokenServiceDep, accounts: ClubAccountRepositoryDep
) -> ResolveClubAccountFromAccessToken:
    return ResolveClubAccountFromAccessToken(
        token_service=token_service, accounts=accounts
    )


ResolveClubAccountDep = Annotated[
    ResolveClubAccountFromAccessToken, Depends(get_resolve_club_account)
]


async def current_club_account(
    credentials: BearerCredentialsDep, use_case: ResolveClubAccountDep
) -> ClubAccount:
    """The Club account a **club-audience** bearer token was issued to. A
    player's token is refused here, whatever account it names."""

    token = credentials.credentials if credentials else None
    return await use_case.execute(token)


CurrentClubAccountDep = Annotated[ClubAccount, Depends(current_club_account)]
