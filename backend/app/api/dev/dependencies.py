"""Request-scoped declarations the console needs and no context declares.

When each port is built and how long it lives; **what** is built is the
composition root's (``app/bootstrap/composition.py``), as for every other
surface. Everything else the console takes — the proposals' repository and
directory, the group directory, the seat charges, a yes and a deck, the club's
acts, the payment provider — it takes through the context's own declaration, so
a test that replaces one replaces it for the console too.

**Most are jobs' units of work** (#591, #592) — what *Run it now* runs: the
book-by sweep, the cut-off, the day close's payouts and summary, the rating
catch-up and the chat sweep, each the builder its job calls — and one is the
step the outbox runs for a seat's money. Each is over this request's session
and its clock, which is the real *now*.

**And the dealer's first act** (#592): ``MakeProposal``, which no route takes
— the proposer's, a seed's and *About to expire*'s. **And what a notice is
pushed as** (#594): ``NoticePushes``, the pusher's own, which the *Sent* pane
shows. **And who a rescue is offered to** (#593): ``RescueOffers``, *Fill in*'s
and the deck's own rule, which a row's rescues are read through; a member's
week (``PlayersInPlay``), which *Kuba leaves* keeps her rescue inside; and
**two acts on a clock the caller names** — *Post — you're In* and *We played,
here is the score* — which situations write her post and a score on as if
earlier (``docs/adr/0194`` §4), as the seed writes them.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Callable
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
    build_booking_repository,
    build_the_cut_off,
    build_the_holding,
    build_ask_how_did_it_go,
    build_club_payout_repository,
    build_club_terms,
    build_court_hours,
    build_deck_people,
    build_decide_club_payouts,
    build_destroy_ended_conversations,
    build_expire_proposals,
    build_run_out_the_time_to_pay,
    build_run_out_the_invitations,
    build_warn_the_covers,
    build_reader_relations,
    build_make_proposal,
    build_notice_pushes,
    build_players_in_play,
    build_pools,
    build_post_a_game,
    build_proposal_player_names,
    build_propose_games,
    build_read_posting,
    build_rescue_offers,
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
    SummaryRepository,
)
from app.kernel import Clock
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.games.application.answer_result import StateResult
from app.modules.games.presentation.dependencies import (
    GameRepositoryDep,
    PlayerNamesDep as CourtNamesDep,
)
from app.modules.notifications.application.pushing import NoticePushes
from app.modules.notifications.application.asking import AskHowDidItGo
from app.modules.payments.application.handlers.settle_seat_charges import (
    SettleSeatCharges,
)
from app.modules.payments.application.payouts import DecideClubPayouts
from app.modules.payments.domain.ports import ClubPayoutRepository
from app.modules.payments.presentation.dependencies import PaymentProviderDep
from app.modules.proposals.application.cut_off import TheCutOff
from app.modules.proposals.application.holding import TheHolding
from app.modules.proposals.application.expire_proposals import ExpireProposals
from app.modules.proposals.application.friends_games import (
    RunOutTheInvitations,
    WarnTheCovers,
)
from app.modules.proposals.application.time_to_pay import RunOutTheTimeToPay
from app.modules.proposals.application.making import MakeProposal
from app.modules.proposals.application.posting import PostAGame, ReadPosting
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.application.rescues import RescueOffers
from app.modules.proposals.domain.ports import (
    ClubTerms,
    CourtHours,
    DeckPeople,
    PlayerNames,
    PlayersInPlay,
    Pools,
    ReaderRelations,
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
    """Whether each club sells, and its cut-off."""
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


def get_reader_relations(db: DbSession) -> ReaderRelations:
    """Whom each row is friends with — Friends' read, as every proposals read
    asks it (#751)."""
    return build_reader_relations(db)


ReaderRelationsDep = Annotated[ReaderRelations, Depends(get_reader_relations)]


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


def get_run_out_the_time_to_pay(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> RunOutTheTimeToPay:
    """The ``time-to-pay`` job's unit of work, over the real *now*."""
    return build_run_out_the_time_to_pay(db, clock=clock, settings=settings)


RunOutTheTimeToPayDep = Annotated[
    RunOutTheTimeToPay, Depends(get_run_out_the_time_to_pay)
]


def get_run_out_the_invitations(db: DbSession, clock: ClockDep) -> RunOutTheInvitations:
    """The ``invitations`` job's unit of work, over the real *now* (#751)."""
    return build_run_out_the_invitations(db, clock=clock)


RunOutTheInvitationsDep = Annotated[
    RunOutTheInvitations, Depends(get_run_out_the_invitations)
]


def get_warn_the_covers(db: DbSession, clock: ClockDep) -> WarnTheCovers:
    """The ``cover-warning`` job's unit of work, over the real *now* (#752)."""
    return build_warn_the_covers(db, clock=clock)


WarnTheCoversDep = Annotated[WarnTheCovers, Depends(get_warn_the_covers)]


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


def get_the_cut_off(
    db: DbSession, clock: ClockDep, settings: SettingsDep
) -> TheCutOff:
    """The ``cut-off`` job's unit of work, over the real *now*."""
    return build_the_cut_off(db, clock=clock, settings=settings)


TheCutOffDep = Annotated[TheCutOff, Depends(get_the_cut_off)]


def get_the_holding(
    db: DbSession, clock: ClockDep, provider: PaymentProviderDep, settings: SettingsDep
) -> TheHolding:
    """The ``holding`` job's unit of work, over the real *now* and the provider
    this process moves money through (#639)."""
    return build_the_holding(db, clock=clock, provider=provider, settings=settings)


TheHoldingDep = Annotated[TheHolding, Depends(get_the_holding)]


def get_ask_how_did_it_go(db: DbSession, clock: ClockDep) -> AskHowDidItGo:
    """The ``how-did-it-go`` job's unit of work, over the real *now* (#663)."""
    return build_ask_how_did_it_go(db, clock=clock)


AskHowDidItGoDep = Annotated[AskHowDidItGo, Depends(get_ask_how_did_it_go)]


def get_decide_club_payouts(db: DbSession, clock: ClockDep) -> DecideClubPayouts:
    """The ``club-payouts`` job's unit of work — the day close's decision —
    over the real *now*. The outbox pays out."""
    return build_decide_club_payouts(db, clock=clock)


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


def get_settle_ratings_on_results(
    db: DbSession, clock: ClockDep
) -> SettleRatingsOnResults:
    """The ``rating-catch-up`` job's unit of work, over the real *now* — the
    request's clock, read when the press runs, where the job builds its own
    (#593: so a stated result before its day is left, as the tick leaves it)."""
    return build_settle_ratings_on_results(db, clock=clock)


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
    """The dealer's first act, at the real *now* — no route makes a card itself."""
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


def get_rescue_offers(db: DbSession, booked: BookedGamesDep) -> RescueOffers:
    """Who a booked game's open seat is offered to, and its best fits — the
    rule *Fill in* and the deck read, which a row's rescues show (#593)."""
    return build_rescue_offers(db, booked=booked)


RescueOffersDep = Annotated[RescueOffers, Depends(get_rescue_offers)]


def get_players_in_play(db: DbSession) -> PlayersInPlay:
    """Each member's Level and week, as the proposer deals from them — the
    week a situation keeps her game inside (#593)."""
    return build_players_in_play(db)


PlayersInPlayDep = Annotated[PlayersInPlay, Depends(get_players_in_play)]


def get_read_posting(db: DbSession, booked: BookedGamesDep) -> ReadPosting:
    """What every step of posting reads, as of whatever instant it is asked
    about — *A posted game* reads it as of her post (#593)."""
    return build_read_posting(db, booked=booked)


ReadPostingDep = Annotated[ReadPosting, Depends(get_read_posting)]

#: An act built over this request's session on the clock the caller names.
PostAGameOn = Callable[[Clock], PostAGame]
StateResultOn = Callable[[Clock], StateResult]


def get_post_a_game_on(db: DbSession, booked: BookedGamesDep) -> PostAGameOn:
    """*Post — you're In* on a clock the caller names — the one stopped
    earlier that *A posted game* writes her post on (#593)."""

    def on(clock: Clock) -> PostAGame:
        return build_post_a_game(db, clock=clock, booked=booked)

    return on


PostAGameOnDep = Annotated[PostAGameOn, Depends(get_post_a_game_on)]


def get_state_result_on(
    uow: UnitOfWorkDep, games: GameRepositoryDep, names: CourtNamesDep
) -> StateResultOn:
    """*We played, here is the score* on a clock the caller names — the one
    stopped earlier that *Just played* states a score on (#593). Built as the
    game route's own (``get_state_result``), on another clock."""

    def on(clock: Clock) -> StateResult:
        return StateResult(games=games, names=names, uow=uow, clock=clock)

    return on


StateResultOnDep = Annotated[StateResultOn, Depends(get_state_result_on)]
