"""Request-scoped declarations for the Proposals context.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_booked_games,
    build_cancel_the_game,
    build_move_the_game,
    build_preview_the_cancel,
    build_read_club_bookings,
    build_read_club_money,
    build_read_free_courts,
    build_confirm_payment,
    build_say_no_to_a_rescue,
    build_games_and_money_repository,
    build_join_a_rescue,
    build_leave_the_game,
    build_post_a_game,
    build_proposal_club_names,
    build_proposal_directory,
    build_proposal_repository,
    build_read_booking_details,
    build_read_fill_in,
    build_read_group_deck,
    build_read_home,
    build_read_payments_to_confirm,
    build_read_posting_grid,
    build_read_posting_slot,
    build_read_proposal_details,
    build_say_yes,
    build_withdraw_yes,
)
from app.modules.payments.presentation.dependencies import PaymentProviderDep
from app.modules.proposals.application.answers import (
    ConfirmPayment,
    SayNo,
    SayYes,
    WithdrawYes,
)
from app.modules.proposals.application.booking_details import ReadBookingDetails
from app.modules.proposals.application.club_money import ReadClubMoney
from app.modules.proposals.application.club_bookings import (
    CancelTheGame,
    MoveTheGame,
    PreviewTheCancel,
    ReadClubBookings,
    ReadFreeCourts,
)
from app.modules.proposals.application.games_and_money import (
    ReadGamesAndMoney,
    SetGamesAndMoney,
)
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.application.home import ReadHome
from app.modules.proposals.application.leave_the_game import LeaveTheGame
from app.modules.proposals.application.live_yeses import ReadLiveYeses
from app.modules.proposals.application.payments_to_confirm import (
    ReadPaymentsToConfirm,
)
from app.modules.proposals.application.posting import (
    PostAGame,
    ReadPostingGrid,
    ReadPostingSlot,
)
from app.modules.proposals.application.proposal_details import ReadProposalDetails
from app.modules.proposals.application.rescues import (
    SayNoToARescue,
    JoinARescue,
    ReadFillIn,
)
from app.modules.proposals.domain.ports import (
    BookedGames,
    ClubNames,
    GamesAndMoneyRepository,
    ProposalDirectory,
    ProposalRepository,
)


def get_proposal_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ProposalRepository:
    return build_proposal_repository(db, event_store=event_store, events=events)


ProposalRepositoryDep = Annotated[ProposalRepository, Depends(get_proposal_repository)]


def get_proposal_directory(db: DbSession) -> ProposalDirectory:
    return build_proposal_directory(db)


ProposalDirectoryDep = Annotated[ProposalDirectory, Depends(get_proposal_directory)]


def get_proposal_club_names(db: DbSession) -> ClubNames:
    return build_proposal_club_names(db)


ProposalClubNamesDep = Annotated[ClubNames, Depends(get_proposal_club_names)]


def get_say_yes(
    db: DbSession,
    clock: ClockDep,
    provider: PaymentProviderDep,
    settings: SettingsDep,
) -> SayYes:
    """A yes — and, when it is the last, the fill over the provider this
    process moves money through (#541)."""
    return build_say_yes(db, clock=clock, provider=provider, settings=settings)


SayYesDep = Annotated[SayYes, Depends(get_say_yes)]


def get_confirm_payment(
    db: DbSession,
    clock: ClockDep,
    provider: PaymentProviderDep,
    settings: SettingsDep,
) -> ConfirmPayment:
    return build_confirm_payment(db, clock=clock, provider=provider, settings=settings)


ConfirmPaymentDep = Annotated[ConfirmPayment, Depends(get_confirm_payment)]


def get_say_no(
    proposals: ProposalRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SayNo:
    return SayNo(proposals=proposals, uow=uow, clock=clock)


SayNoDep = Annotated[SayNo, Depends(get_say_no)]


def get_withdraw_yes(db: DbSession, clock: ClockDep) -> WithdrawYes:
    """*Withdraw*, and *Leave the game* while a payment is awaited (#625)."""
    return build_withdraw_yes(db, clock=clock)


WithdrawYesDep = Annotated[WithdrawYes, Depends(get_withdraw_yes)]


def get_read_live_yeses(
    directory: ProposalDirectoryDep, clubs: ProposalClubNamesDep, clock: ClockDep
) -> ReadLiveYeses:
    return ReadLiveYeses(directory=directory, clubs=clubs, clock=clock)


ReadLiveYesesDep = Annotated[ReadLiveYeses, Depends(get_read_live_yeses)]


def get_read_payments_to_confirm(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadPaymentsToConfirm:
    return build_read_payments_to_confirm(db, settings=settings, clock=clock)


ReadPaymentsToConfirmDep = Annotated[
    ReadPaymentsToConfirm, Depends(get_read_payments_to_confirm)
]


def get_games_and_money_repository(
    event_store: DomainEventStoreDep, events: EventPublisherDep
) -> GamesAndMoneyRepository:
    return build_games_and_money_repository(event_store=event_store, events=events)


GamesAndMoneyRepositoryDep = Annotated[
    GamesAndMoneyRepository, Depends(get_games_and_money_repository)
]


def get_read_games_and_money(
    settings: GamesAndMoneyRepositoryDep,
) -> ReadGamesAndMoney:
    return ReadGamesAndMoney(settings=settings)


ReadGamesAndMoneyDep = Annotated[ReadGamesAndMoney, Depends(get_read_games_and_money)]


def get_set_games_and_money(
    settings: GamesAndMoneyRepositoryDep, uow: UnitOfWorkDep, clock: ClockDep
) -> SetGamesAndMoney:
    return SetGamesAndMoney(settings=settings, uow=uow, clock=clock)


SetGamesAndMoneyDep = Annotated[SetGamesAndMoney, Depends(get_set_games_and_money)]


def get_booked_games(db: DbSession) -> BookedGames:
    """The games a player has booked, off the bookings (#541); a test may stand
    in for them by overriding this."""
    return build_booked_games(db)


BookedGamesDep = Annotated[BookedGames, Depends(get_booked_games)]


def get_read_group_deck(
    db: DbSession, settings: SettingsDep, clock: ClockDep, booked: BookedGamesDep
) -> ReadGroupDeck:
    return build_read_group_deck(db, settings=settings, clock=clock, booked=booked)


ReadGroupDeckDep = Annotated[ReadGroupDeck, Depends(get_read_group_deck)]


def get_read_home(db: DbSession, settings: SettingsDep, clock: ClockDep) -> ReadHome:
    return build_read_home(db, settings=settings, clock=clock)


ReadHomeDep = Annotated[ReadHome, Depends(get_read_home)]


def get_read_booking_details(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadBookingDetails:
    return build_read_booking_details(db, settings=settings, clock=clock)


ReadBookingDetailsDep = Annotated[ReadBookingDetails, Depends(get_read_booking_details)]


def get_leave_the_game(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> LeaveTheGame:
    """*Leave the game* (#544). Asks nothing of the provider: the refund follows
    the commit, from the outbox."""
    return build_leave_the_game(db, clock=clock, settings=settings)


LeaveTheGameDep = Annotated[LeaveTheGame, Depends(get_leave_the_game)]


def get_read_proposal_details(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadProposalDetails:
    return build_read_proposal_details(db, settings=settings, clock=clock)


ReadProposalDetailsDep = Annotated[
    ReadProposalDetails, Depends(get_read_proposal_details)
]


def get_read_fill_in(
    db: DbSession, settings: SettingsDep, clock: ClockDep, booked: BookedGamesDep
) -> ReadFillIn:
    """A group's *Fill in* tab (#545)."""
    return build_read_fill_in(db, settings=settings, clock=clock, booked=booked)


ReadFillInDep = Annotated[ReadFillIn, Depends(get_read_fill_in)]


def get_join_a_rescue(
    db: DbSession,
    clock: ClockDep,
    provider: PaymentProviderDep,
    settings: SettingsDep,
) -> JoinARescue:
    """*I'm in* on an open seat — the share charged over the provider this
    process moves money through (#545)."""
    return build_join_a_rescue(db, clock=clock, provider=provider, settings=settings)


JoinARescueDep = Annotated[JoinARescue, Depends(get_join_a_rescue)]


def get_say_no_to_a_rescue(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> SayNoToARescue:
    return build_say_no_to_a_rescue(db, clock=clock, settings=settings)


SayNoToARescueDep = Annotated[SayNoToARescue, Depends(get_say_no_to_a_rescue)]


# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


def get_read_club_bookings(db: DbSession, clock: ClockDep) -> ReadClubBookings:
    return build_read_club_bookings(db, clock=clock)


ReadClubBookingsDep = Annotated[ReadClubBookings, Depends(get_read_club_bookings)]


def get_read_club_money(db: DbSession, clock: ClockDep) -> ReadClubMoney:
    return build_read_club_money(db, clock=clock)


ReadClubMoneyDep = Annotated[ReadClubMoney, Depends(get_read_club_money)]


def get_read_free_courts(db: DbSession, clock: ClockDep) -> ReadFreeCourts:
    return build_read_free_courts(db, clock=clock)


ReadFreeCourtsDep = Annotated[ReadFreeCourts, Depends(get_read_free_courts)]


def get_move_the_game(db: DbSession, clock: ClockDep) -> MoveTheGame:
    return build_move_the_game(db, clock=clock)


MoveTheGameDep = Annotated[MoveTheGame, Depends(get_move_the_game)]


def get_preview_the_cancel(db: DbSession, clock: ClockDep) -> PreviewTheCancel:
    return build_preview_the_cancel(db, clock=clock)


PreviewTheCancelDep = Annotated[PreviewTheCancel, Depends(get_preview_the_cancel)]


def get_cancel_the_game(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> CancelTheGame:
    return build_cancel_the_game(db, clock=clock, settings=settings)


CancelTheGameDep = Annotated[CancelTheGame, Depends(get_cancel_the_game)]


# --------------------------------------------------------------------------- #
# Posting a game (#546)
# --------------------------------------------------------------------------- #


def get_read_posting_grid(
    db: DbSession, clock: ClockDep, booked: BookedGamesDep
) -> ReadPostingGrid:
    return build_read_posting_grid(db, clock=clock, booked=booked)


ReadPostingGridDep = Annotated[ReadPostingGrid, Depends(get_read_posting_grid)]


def get_read_posting_slot(
    db: DbSession, settings: SettingsDep, clock: ClockDep, booked: BookedGamesDep
) -> ReadPostingSlot:
    return build_read_posting_slot(db, settings=settings, clock=clock, booked=booked)


ReadPostingSlotDep = Annotated[ReadPostingSlot, Depends(get_read_posting_slot)]


def get_post_a_game(
    db: DbSession, clock: ClockDep, booked: BookedGamesDep
) -> PostAGame:
    """*Post — you're In*: made and dealt through the dealer's own act."""
    return build_post_a_game(db, clock=clock, booked=booked)


PostAGameDep = Annotated[PostAGame, Depends(get_post_a_game)]
