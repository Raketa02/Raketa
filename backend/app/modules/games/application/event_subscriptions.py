"""The Games context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``GamePlanned`` must never change what is already in the store.

**Twelve names, on one aggregate — eleven written and one retired** — and every
one of them is something a person did.
``games.planned`` is the exception that proves it — a booking is everybody's yes
arriving at a total, and it is recorded because *the arrangement at the instant
it was settled* is not recoverable from anywhere else once seats start moving.

**No name here says a result is confirmed, unscored or never played.** That is
not an omission to be filled in by whoever needs one: the standing is derived
from the record and the clock, and a durable name announcing a conclusion would
be a second place for it to be true — the one a subscriber would believe, and the
one that would be wrong for the whole gap between a deadline passing and anything
looking. The rating context reads confirmed results forward instead
(``docs/adr/0137``).

**``games.called_off`` is the ninth, and the one end a name announces**
(``docs/adr/0163``): a decision taken while a seat was open, or over the whole
court by its club, which no reading of the record could reach — so the name is
the fact's only home rather than a second one.

**``games.seat_vacated`` and ``games.line_up_reseated`` are the seventh and
eighth** (``docs/adr/0162``): the two ways a line-up moves after the booking —
a departure (#544) and a rescue (#545) — each told by ``bookings`` in the
transaction of the act that caused it. Neither announces a standing.

**``games.dismissed`` is retired** with the old game card's dismissal (#578):
nothing writes it, and it stays registered so a stored row still decodes — the
fold reads it and changes nothing.

**``games.no_show_reported`` and ``games.no_show_disputed`` are the tenth
and eleventh** (#547): somebody who came to a booked game saying another did not,
and that other saying they did. Neither announces a standing — a report stands
by its day passing in silence.

The two most likely to be asked to carry more later are ``games.planned`` — a
game that one day comes from something other than a booking — and
``games.result_proposed``, if a score ever grows a shape richer than sets. Either
will be a version 2 registered beside version 1, never an edit to it: the rows
already in the store must keep decoding.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.games.application.handlers import LogGameEvent
from app.modules.games.domain.events import (
    GameCalledOff,
    GameDismissed,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    NoShowDisputed,
    NoShowReported,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
    SeatVacated,
)

_CONTRACTS = (
    (GamePlanned, "games.planned"),
    (SeatVacated, "games.seat_vacated"),
    (LineUpReseated, "games.line_up_reseated"),
    (GameCalledOff, "games.called_off"),
    (GamePlayed, "games.played"),
    (ResultProposed, "games.result_proposed"),
    (ResultCorrected, "games.result_corrected"),
    (ResultCountered, "games.result_countered"),
    (ResultAccepted, "games.result_accepted"),
    (GameDismissed, "games.dismissed"),
    (NoShowReported, "games.no_show_reported"),
    (NoShowDisputed, "games.no_show_disputed"),
)


def register_game_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_game_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogGameEvent(name))
