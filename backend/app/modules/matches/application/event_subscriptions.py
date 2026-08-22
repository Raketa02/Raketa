"""Every Matches announcement, registered under a durable name.

**The catalog name is what history is recorded under**, never the Python class
name — so every registration here is explicit about both the name and the
version, and renaming a class cannot change what is already on the outbox.

**Twenty-one names, and the length is the decision.** ADR-0034 costs event
types now to buy the support timeline later: *"a longer, more specific event
list is more to name, more to version, and more to keep faithful — and nothing
mechanical catches an event that is published too coarsely."* Nothing is
mechanical, so ``tests/unit/test_match_events.py`` walks the aggregate instead
and fails when a mutating method announces nothing, or when a name here reads
like *updated*.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher

from app.modules.matches.application.handlers import LogMatchEvent
from app.modules.matches.domain.events import (
    CourtHeld,
    CourtLocked,
    CourtReleased,
    HoldExtended,
    InventoryLost,
    MatchCancelledAtCheckpoint,
    MatchCancelledByClub,
    MatchCancelledForWeather,
    MatchCancelledIncomplete,
    MatchCommitted,
    MatchPosted,
    MatchStartMoved,
    NoShowRecorded,
    ResultAgreed,
    ScoreProposed,
    SeatPaid,
    SeatsOpened,
    SeatTaken,
    SeatTransferEnded,
    SeatTransferStarted,
    SeatVacated,
)

#: Class to durable name. One table, read by both functions below, so an event
#: cannot be registered under a name nothing subscribes to — the shape of
#: *nothing mechanical catches a coarse event* made as mechanical as it can be.
MATCH_EVENTS: tuple[tuple[type, str], ...] = (
    (MatchPosted, "matches.match_posted"),
    (MatchStartMoved, "matches.match_start_moved"),
    (SeatTaken, "matches.seat_taken"),
    (SeatPaid, "matches.seat_paid"),
    (SeatVacated, "matches.seat_vacated"),
    (SeatsOpened, "matches.seats_opened"),
    (SeatTransferStarted, "matches.seat_transfer_started"),
    (SeatTransferEnded, "matches.seat_transfer_ended"),
    (CourtHeld, "matches.court_held"),
    (CourtReleased, "matches.court_released"),
    (CourtLocked, "matches.court_locked"),
    (HoldExtended, "matches.hold_extended"),
    (InventoryLost, "matches.inventory_lost"),
    (MatchCommitted, "matches.match_committed"),
    (MatchCancelledByClub, "matches.match_cancelled_by_club"),
    (MatchCancelledForWeather, "matches.match_cancelled_for_weather"),
    (MatchCancelledIncomplete, "matches.match_cancelled_incomplete"),
    (MatchCancelledAtCheckpoint, "matches.match_cancelled_at_checkpoint"),
    (NoShowRecorded, "matches.no_show_recorded"),
    (ScoreProposed, "matches.score_proposed"),
    (ResultAgreed, "matches.result_agreed"),
)


def register_match_events(catalog: EventCatalog) -> None:
    for event_cls, name in MATCH_EVENTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_match_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in MATCH_EVENTS:
        dispatcher.subscribe(event_cls, LogMatchEvent(name))
