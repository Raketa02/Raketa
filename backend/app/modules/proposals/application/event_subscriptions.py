from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.domain.events import CalledOffAtCutOff, SeatLeft
from app.modules.groups.domain.events import GroupDeleted, GroupLeft
from app.modules.proposals.application.handlers import (
    LogGamesAndMoneySet,
    LogProposalEvent,
    MarkDueForProposing,
    ResumeYesesOnAFreedWeek,
    WithdrawYesesOnLeaving,
)
from app.modules.proposals.application.handlers.mark_due_for_proposing import (
    CLUB_EVENTS,
    PLAYER_EVENTS,
    POOL_EVENTS,
    SWIPE_EVENTS,
)
from app.modules.proposals.application.leaving import WithdrawALeaversYeses
from app.modules.proposals.application.propose_games import DueForProposing
from app.modules.proposals.application.resume_paused_yeses import ResumePausedYeses
from app.modules.proposals.domain.events import (
    CourtHourLost,
    GamesAndMoneySet,
    NoSaid,
    ProposalExpired,
    ProposalFilled,
    ProposalMade,
    ProposalWithdrawn,
    Redealt,
    SeatReopened,
    TurnedDown,
    VersionDealt,
    YesPaused,
    YesResumed,
    YesSaid,
    YesWithdrawn,
)

_EVENTS = (
    (ProposalMade, "proposals.proposal_made"),
    (VersionDealt, "proposals.version_dealt"),
    (YesSaid, "proposals.yes_said"),
    (NoSaid, "proposals.no_said"),
    (YesWithdrawn, "proposals.yes_withdrawn"),
    (ProposalWithdrawn, "proposals.proposal_withdrawn"),
    (ProposalExpired, "proposals.proposal_expired"),
    (CourtHourLost, "proposals.court_hour_lost"),
    (GamesAndMoneySet, "proposals.games_and_money_set"),
    (ProposalFilled, "proposals.proposal_filled"),
    (SeatReopened, "proposals.seat_reopened"),
    (YesPaused, "proposals.yes_paused"),
    (YesResumed, "proposals.yes_resumed"),
    (TurnedDown, "proposals.turned_down"),
    (Redealt, "proposals.redealt"),
)


def register_proposal_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_proposal_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(ProposalMade, LogProposalEvent())
    dispatcher.subscribe(VersionDealt, LogProposalEvent())
    dispatcher.subscribe(YesSaid, LogProposalEvent())
    dispatcher.subscribe(NoSaid, LogProposalEvent())
    dispatcher.subscribe(YesWithdrawn, LogProposalEvent())
    dispatcher.subscribe(ProposalWithdrawn, LogProposalEvent())
    dispatcher.subscribe(ProposalExpired, LogProposalEvent())
    dispatcher.subscribe(CourtHourLost, LogProposalEvent())
    dispatcher.subscribe(GamesAndMoneySet, LogGamesAndMoneySet())
    dispatcher.subscribe(ProposalFilled, LogProposalEvent())
    dispatcher.subscribe(SeatReopened, LogProposalEvent())
    dispatcher.subscribe(YesPaused, LogProposalEvent())
    dispatcher.subscribe(YesResumed, LogProposalEvent())
    dispatcher.subscribe(TurnedDown, LogProposalEvent())
    dispatcher.subscribe(Redealt, LogProposalEvent())


def subscribe_the_pool_leaver(
    dispatcher: EventDispatcher, withdraw: WithdrawALeaversYeses
) -> None:
    """The subscriber that **writes**, so it is added per delivery run over that
    run's session — as the room teller is — and a leaver's withdrawals commit
    with the delivery of the leaving (``app/bootstrap/events.py``)."""

    leaver = WithdrawYesesOnLeaving(withdraw)
    dispatcher.subscribe(GroupLeft, leaver)
    dispatcher.subscribe(GroupDeleted, leaver)


def subscribe_the_week_resumer(
    dispatcher: EventDispatcher, resume: ResumePausedYeses
) -> None:
    """The subscriber that brings back the yeses a full week paused when a
    booked game stops being a player's (#544). It **writes** — and may fill a
    game, charging its seats over the run's provider — so it is added per
    delivery run over that run's session and provider."""

    resumer = ResumeYesesOnAFreedWeek(resume)
    dispatcher.subscribe(SeatLeft, resumer)
    dispatcher.subscribe(CalledOffAtCutOff, resumer)


def subscribe_the_proposer_on_changes(
    dispatcher: EventDispatcher, due: DueForProposing
) -> None:
    """The subscriber that notes what changed for the proposer's short tick —
    added per delivery run, beside the room teller, because *which* process's
    proposer is told is a fact about the delivery: the API's is, and a seed's
    or a command-line drain's has no proposer listening."""

    marker = MarkDueForProposing(due)
    for event_class in (*POOL_EVENTS, *PLAYER_EVENTS, *SWIPE_EVENTS, *CLUB_EVENTS):
        dispatcher.subscribe(event_class, marker)
