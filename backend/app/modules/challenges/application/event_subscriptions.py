"""The Challenges context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``ChallengeSent`` must never change what is already in the store.

**Six names, on one aggregate.** The prefix is the context's, which is what makes
a name a statement about *what happened* rather than about which class wrote it.

The two most likely to be asked to carry more later are ``challenges.sent`` — a
send that one day cites something other than a search — and
``challenges.seats_invited``. Either will be a version 2 registered beside
version 1, never an edit to it: the rows already in the store must keep decoding.

**No name here says the challenge is on, expired or declined.** That is not an
omission to be filled in by whoever needs one; the standing is derived from the
seats and the clock, and a durable name announcing a conclusion would be a second
place for it to be true — the one a subscriber would believe.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.challenges.application.handlers import LogChallengeEvent
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)

_CONTRACTS = (
    (ChallengeSent, "challenges.sent"),
    (
        ChallengeOpenedFromMutualInterest,
        "challenges.opened_from_mutual_interest",
    ),
    (SeatAccepted, "challenges.seat_accepted"),
    (SeatDeclined, "challenges.seat_declined"),
    (SeatLapsed, "challenges.seat_lapsed"),
    (SeatsInvited, "challenges.seats_invited"),
)


def register_challenge_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_challenge_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogChallengeEvent(name))
