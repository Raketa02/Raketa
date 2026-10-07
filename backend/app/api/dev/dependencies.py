"""Request-scoped declarations the console needs and no context declares.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``), as for every other
surface. Everything else the console takes — the proposals' repository and
directory, the group directory, the seat charges, a yes and a deck, the club's
answers, the payment provider — it takes through the context's own
declaration, so a test that replaces one replaces it for the console too.

**Most are jobs' units of work** (#591, #592) — what *Run it now* runs: the
On request timeout, the book-by sweep, the cut-off, the day close's payouts and
summary, the rating catch-up and the chat sweep, each the builder its job
calls — and one is the step the outbox runs for a seat's money. Each is over
this request's session and its clock, which is the real *now*.

**And the dealer's first act** (#592): ``MakeProposal``, which no route takes
— the proposer's, a seed's and *About to expire*'s. **And what a notice is
pushed as** (#594): ``NoticePushes``, the pusher's own, which the *Sent* pane
shows.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
)
from app.bootstrap.composition import (
    build_booking_repository,
    build_call_off_short_games,
    build_check_in_codes,
    build_club_payout_repository,
    build_club_terms,
    build_court_hours,
    build_deck_people,
    build_decide_club_payouts,
    build_destroy_ended_conversations,
    build_expire_proposals,
    build_expire_unanswered_requests,
    build_make_proposal,
    build_notice_pushes,
    build_pools,
    build_proposal_player_names,
    build_propose_games,
    build_saved_methods,
    build_settle_ratings_on_results,
    build_settle_seat_charges,
    build_summarise_new_bookings,
    build_summary_repository,
    build_where_pools_play,
)
from app.modules.bookings.application.daily_summary import SummariseNewBookings
from app.modules.bookings.domain.ports import (
    BookingRepository,
    CheckInCodes,
    SummaryRepository,
)
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.notifications.application.pushing import NoticePushes
from app.modules.payments.application.handlers.settle_seat_charges import (
    SettleSeatCharges,
)
from app.modules.payments.application.payouts import DecideClubPayouts
from app.modules.payments.domain.ports import ClubPayoutRepository
from app.modules.payments.presentation.dependencies import PaymentProviderDep
from app.modules.proposals.application.club_requests import (
    ExpireUnansweredRequests,
)
from app.modules.proposals.application.cut_off import CallOffShortGames
from app.modules.proposals.application.expire_proposals import ExpireProposals
from app.modules.proposals.application.making import MakeProposal
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.domain.ports import (
    ClubTerms,
    CourtHours,
    DeckPeople,
    PlayerNames,
    Pools,
    SavedMethods,
    WherePoolsPlay,
)
from app.modules.proposals.presentation.dependencies import BookedGamesDep
from app.modules.rating.application.settle_results import SettleRatingsOnResults


def get_booking_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> BookingRepository:
    return build_booking_repository(db, event_store=event_store, events=events)


BookingRepositoryDep = Annotated[BookingRepository, Depends(get_booking_repository)]


def get_deck_people(db: DbSession, settings: SettingsDep) -> DeckPeople:
    """A row's name, face and Level — what a card draws of a person."""
    return build_deck_people(db, settings=settings)


DeckPeopleDep = Annotated[DeckPeople, Depends(get_deck_people)]


def get_player_names(db: DbSession) -> PlayerNames:
    return build_proposal_player_names(db)


PlayerNamesDep = Annotated[PlayerNames, Depends(get_player_names)]


def get_club_terms(db: DbSession) -> ClubTerms:
    """Whether each club sells, its cut-off, and whether it confirms each game."""
    return build_club_terms(db)


ClubTermsDep = Annotated[ClubTerms, Depends(get_club_terms)]


def get_saved_methods(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> SavedMethods:
    return build_saved_methods(db, event_store=event_store, events=events)


SavedMethodsDep = Annotated[SavedMethods, Depends(get_saved_methods)]


def get_propose_games(
    db: DbSession, clock: ClockDep, booked: BookedGamesDep
) -> ProposeGames:
    """The proposer the jobs run, over this request's clock — the real *now*."""
    return build_propose_games(db, clock=clock, booked=booked)


ProposeGamesDep = Annotated[ProposeGames, Depends(get_propose_games)]


def get_pools(db: DbSession) -> Pools:
    return build_pools(db)


PoolsDep = Annotated[Pools, Depends(get_pools)]


def get_where_pools_play(db: DbSession) -> WherePoolsPlay:
    """A group's home club, and the clubs its games may also use."""
    return build_where_pools_play(db)


WherePoolsPlayDep = Annotated[WherePoolsPlay, Depends(get_where_pools_play)]


def get_court_hours(db: DbSession) -> CourtHours:
    """What a club sells at an hour, at a given *now* — the backdated one a
    situation writes its history on, too."""
    return build_court_hours(db)


CourtHoursDep = Annotated[CourtHours, Depends(get_court_hours)]


def get_check_in_codes(settings: SettingsDep) -> CheckInCodes:
    """Each seat's code, as the phone shows it and the desk recomputes it."""
    return build_check_in_codes(settings)


CheckInCodesDep = Annotated[CheckInCodes, Depends(get_check_in_codes)]


def get_expire_unanswered_requests(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> ExpireUnansweredRequests:
    """The ``request-timeout`` job's unit of work, over the real *now*."""
    return build_expire_unanswered_requests(db, clock=clock, settings=settings)


ExpireUnansweredRequestsDep = Annotated[
    ExpireUnansweredRequests, Depends(get_expire_unanswered_requests)
]


def get_settle_seat_charges(
    db: DbSession, provider: PaymentProviderDep, clock: ClockDep
) -> SettleSeatCharges:
    """The outbox's step for a seat's money, over the provider this process
    moves money through."""
    return build_settle_seat_charges(db, provider=provider, clock=clock)


SettleSeatChargesDep = Annotated[SettleSeatCharges, Depends(get_settle_seat_charges)]


def get_expire_proposals(db: DbSession, clock: ClockDep) -> ExpireProposals:
    """The ``proposal-expiry`` job's unit of work, over the real *now*."""
    return build_expire_proposals(db, clock=clock)


ExpireProposalsDep = Annotated[ExpireProposals, Depends(get_expire_proposals)]


def get_call_off_short_games(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> CallOffShortGames:
    """The ``cut-off`` job's unit of work, over the real *now*."""
    return build_call_off_short_games(db, clock=clock, settings=settings)


CallOffShortGamesDep = Annotated[CallOffShortGames, Depends(get_call_off_short_games)]


def get_decide_club_payouts(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> DecideClubPayouts:
    """The ``club-payouts`` job's unit of work — the day close's decision —
    over the real *now*. The outbox pays out."""
    return build_decide_club_payouts(db, clock=clock, settings=settings)


DecideClubPayoutsDep = Annotated[DecideClubPayouts, Depends(get_decide_club_payouts)]


def get_summarise_new_bookings(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> SummariseNewBookings:
    """The ``new-bookings-summary`` job's unit of work — the day close's email
    to each desk — over the real *now*."""
    return build_summarise_new_bookings(db, clock=clock, settings=settings)


SummariseNewBookingsDep = Annotated[
    SummariseNewBookings, Depends(get_summarise_new_bookings)
]


def get_settle_ratings_on_results(db: DbSession) -> SettleRatingsOnResults:
    """The ``rating-catch-up`` job's unit of work. It reads the wall clock
    itself, as the job does (``build_settle_ratings_on_results`` says why)."""
    return build_settle_ratings_on_results(db)


SettleRatingsOnResultsDep = Annotated[
    SettleRatingsOnResults, Depends(get_settle_ratings_on_results)
]


def get_destroy_ended_conversations(
    db: DbSession, clock: ClockDep
) -> DestroyEndedConversations:
    """The ``conversation-sweep`` job's unit of work, over the real *now*."""
    return build_destroy_ended_conversations(db, clock=clock)


DestroyEndedConversationsDep = Annotated[
    DestroyEndedConversations, Depends(get_destroy_ended_conversations)
]


def get_make_proposal(db: DbSession, clock: ClockDep) -> MakeProposal:
    """The dealer's first act, at the real *now* — no route makes a proposal."""
    return build_make_proposal(db, clock=clock)


MakeProposalDep = Annotated[MakeProposal, Depends(get_make_proposal)]


def get_club_payout_repository(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> ClubPayoutRepository:
    """Each club's payout per day — whether a day close has paid it already."""
    return build_club_payout_repository(db, event_store=event_store, events=events)


ClubPayoutRepositoryDep = Annotated[
    ClubPayoutRepository, Depends(get_club_payout_repository)
]


def get_summary_repository(
    event_store: DomainEventStoreDep, events: EventPublisherDep
) -> SummaryRepository:
    """Each club's summed-up days — whether a day close has told its desk."""
    return build_summary_repository(event_store=event_store, events=events)


SummaryRepositoryDep = Annotated[SummaryRepository, Depends(get_summary_repository)]


def get_notice_pushes(db: DbSession) -> NoticePushes:
    """What each notice is pushed as — the pusher's own, which a seed account,
    with no phone, is never pushed."""
    return build_notice_pushes(db)


NoticePushesDep = Annotated[NoticePushes, Depends(get_notice_pushes)]
