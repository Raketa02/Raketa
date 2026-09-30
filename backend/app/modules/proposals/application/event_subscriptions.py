from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.groups.domain.events import GroupDeleted, GroupLeft
from app.modules.proposals.application.handlers import (
    LogGamesAndMoneySet,
    LogProposalEvent,
    WithdrawYesesOnLeaving,
)
from app.modules.proposals.application.leaving import WithdrawALeaversYeses
from app.modules.proposals.domain.events import (
    GamesAndMoneySet,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
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
    (GamesAndMoneySet, "proposals.games_and_money_set"),
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
    dispatcher.subscribe(GamesAndMoneySet, LogGamesAndMoneySet())


def subscribe_the_pool_leaver(
    dispatcher: EventDispatcher, withdraw: WithdrawALeaversYeses
) -> None:
    """The subscriber that **writes**, so it is added per delivery run over that
    run's session — as the room teller is — and a leaver's withdrawals commit
    with the delivery of the leaving (``app/bootstrap/events.py``)."""

    leaver = WithdrawYesesOnLeaving(withdraw)
    dispatcher.subscribe(GroupLeft, leaver)
    dispatcher.subscribe(GroupDeleted, leaver)
