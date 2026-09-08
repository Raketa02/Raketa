"""The Challenges context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``ChallengeSent`` must never change what is already in the store.

**Seven names, on one aggregate.** The prefix is the context's, which is what
makes a name a statement about *what happened* rather than about which class
wrote it.

The two most likely to be asked to carry more later are ``challenges.sent`` — a
send that one day cites something other than a search — and
``challenges.seats_invited``. Either will be a version 2 registered beside
version 1, never an edit to it: the rows already in the store must keep decoding.

**``seats_invited`` was asked, and it took a nullable ``invited_by`` instead.**
The argument is written at the field in ``domain/events.py``, because that is
where the interesting part is: the rule's *reason* is that stored rows keep
decoding, and a key the codec never sees takes its default rather than being
reinterpreted — while a version 2 in this catalog costs **two Python classes**,
since ``EventCatalog.register`` binds one class to one ``(name, version)``. What
still earns those two classes is a change that makes a stored row **mean**
something else. That distinction, rather than *never an edit*, is the line these
two files now draw together.

**No name here says the challenge is on, expired or declined.** That is not an
omission to be filled in by whoever needs one; the standing is derived from the
seats and the clock, and a durable name announcing a conclusion would be a second
place for it to be true — the one a subscriber would believe.

**``challenges.withdrawn`` is the one that does say a challenge ended, and it is
allowed to** (``docs/adr/0142`` §3): a withdrawal is a decision a person took and
no arrangement of the seats reaches it, so the name is the only place the fact is
true rather than a second one. It is also the first name here a **subscriber**
will want: the conversation the first acceptance opened has to be destroyed, and
the context that owns conversations will hear it here rather than being called
from the use case.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.challenges.application.handlers import LogChallengeEvent
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
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
    (ChallengeWithdrawn, "challenges.withdrawn"),
)


def register_challenge_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_challenge_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogChallengeEvent(name))
