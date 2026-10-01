"""The subscriber that tells the proposer what changed — see
``propose_games.py``'s ``DueForProposing``.

**It notes, and never writes**: the change is delivered, the pool, the player or
the game it touched is remembered in this process, and the proposer's short tick
deals from it. So a delivery never waits on a batch and a batch that fails never
holds a delivery back — and the sweep over every pool is what guarantees nothing
is missed.

What makes a pool due (the mechanics §5.1: *a court frees up, a member joins,
someone changes their hours*): somebody joining a group, a player's week, Play
intent, first rating in a sport or Games & money — each of which changes which
games they may be dealt in every pool they are in — a swipe, which may leave a
seat for the next best fits or a pick at half In, and **anything a club changes
about what it sells**, which is everywhere: a club's courts may be in reach of
any group near it. Its payments account going ready — or ready no longer — is
one of those, since it is what makes a club live (#537). **A game filling is
one too** (#541): its booking took a court hour from every card at that club
and hour, in any pool — and a seat reopened, or a yes paused, left a seat open.
**So is a game put to an On request club, and the club's answer** (#543): the
request holds a court hour, and a request refused, unanswered or withdrawn
frees it — and a turned-down game's people are owed a new card first.
"""

from __future__ import annotations

from app.application.events import DeliveryContext
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    RequestWithdrawn,
)
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PaymentsStatusChanged,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
    WayOfWorkingChosen,
)
from app.modules.groups.domain.events import GroupJoined, JoinRequestApproved
from app.modules.player_profile.domain.events import (
    PlayIntentDeclared,
    WeeklyHoursSet,
)
from app.modules.proposals.application.propose_games import DueForProposing
from app.modules.proposals.domain.events import (
    GamesAndMoneySet,
    NoSaid,
    ProposalFilled,
    SeatReopened,
    YesPaused,
    YesSaid,
    YesWithdrawn,
)
from app.modules.rating.domain.events import RatingInitialised

#: A member joining a pool.
POOL_EVENTS = (GroupJoined, JoinRequestApproved)
#: A change to what one player may be dealt, in every pool they are in.
PLAYER_EVENTS = (
    WeeklyHoursSet,
    PlayIntentDeclared,
    RatingInitialised,
    GamesAndMoneySet,
)
#: A swipe on a game still filling — or a yes that stopped counting, which
#: opens a seat as a withdrawal does.
SWIPE_EVENTS = (YesSaid, NoSaid, YesWithdrawn, SeatReopened, YesPaused)
#: A change to what a club sells.
CLUB_EVENTS = (
    CourtAdded,
    CourtChanged,
    CourtSwitchedOff,
    CourtSwitchedOn,
    CourtRemoved,
    RaketaHoursSet,
    ExceptionAdded,
    ExceptionRemoved,
    PricesSet,
    WayOfWorkingChosen,
    RaketaSettingsChanged,
    RaketaPaused,
    RaketaResumed,
    # Ready is the checklist's first step: a club goes live on it, and off.
    PaymentsStatusChanged,
    # A booking holds a court hour the club no longer sells (#541).
    ProposalFilled,
    # A request holds one, and its answer or its withdrawal frees it (#543).
    BookingRequested,
    BookingAccepted,
    BookingRefused,
    BookingTimedOut,
    RequestWithdrawn,
)


class MarkDueForProposing:
    def __init__(self, due: DueForProposing) -> None:
        self._due = due

    async def __call__(self, event: object, context: DeliveryContext) -> None:
        if isinstance(event, POOL_EVENTS):
            # A group's pool is filed under the group's own id.
            self._due.pool(event.group_id)
        elif isinstance(event, PLAYER_EVENTS):
            self._due.player(event.player_id)
        elif isinstance(event, SWIPE_EVENTS):
            self._due.proposal(event.proposal_id)
        elif isinstance(event, CLUB_EVENTS):
            self._due.everywhere()
