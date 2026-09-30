"""The Proposals context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are. **A yes and a no are silent to people, not to the log**:
the line carries the game and whose answer it was, and nothing a card shows. A
player's Games & money is logged by whose it is, and never by what it says.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.proposals.domain.events import (
    CourtHourLost,
    GamesAndMoneySet,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
    YesSaid,
    YesWithdrawn,
)

logger = logging.getLogger(__name__)

ProposalEvent = (
    ProposalMade
    | VersionDealt
    | YesSaid
    | NoSaid
    | YesWithdrawn
    | ProposalWithdrawn
    | ProposalExpired
    | CourtHourLost
)

_LINES: dict[type, str] = {
    ProposalMade: "proposals.proposal.made",
    VersionDealt: "proposals.version.dealt",
    YesSaid: "proposals.yes.said",
    NoSaid: "proposals.no.said",
    YesWithdrawn: "proposals.yes.withdrawn",
    ProposalWithdrawn: "proposals.proposal.withdrawn",
    ProposalExpired: "proposals.proposal.expired",
    CourtHourLost: "proposals.court_hour.lost",
}


class LogProposalEvent:
    async def __call__(self, event: ProposalEvent, context: DeliveryContext) -> None:
        extra = {
            "proposal_id": str(event.proposal_id),
            "occurred_at": event.occurred_at.isoformat(),
            "event_id": str(context.event_id),
            "attempt": context.attempt,
        }
        player_id = getattr(event, "player_id", None)
        if player_id is not None:
            extra["player_id"] = str(player_id)
        logger.info(_LINES[type(event)], extra=extra)


class LogGamesAndMoneySet:
    async def __call__(self, event: GamesAndMoneySet, context: DeliveryContext) -> None:
        logger.info(
            "proposals.games_and_money.set",
            extra={
                "player_id": str(event.player_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
