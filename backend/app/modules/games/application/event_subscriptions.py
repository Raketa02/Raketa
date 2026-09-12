"""The Games context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``GamePlanned`` must never change what is already in the store.

**Nine names, on one aggregate**, and every one of them is something a person did.
``games.planned`` is the exception that proves it — a line-up completing is four
people's acceptances arriving at a total, and it is recorded because *the
arrangement at the instant it was settled* is not recoverable from anywhere else
once seats start moving.

**No name here says a result is confirmed, unscored or never played.** That is
not an omission to be filled in by whoever needs one: the standing is derived
from the record and the clock, and a durable name announcing a conclusion would
be a second place for it to be true — the one a subscriber would believe, and the
one that would be wrong for the whole gap between a deadline passing and anything
looking. The rating context reads confirmed results forward instead
(``docs/adr/0137``).

**``games.called_off`` is the ninth, and the one end a name announces**
(``docs/adr/0163``): a decision somebody took while a seat was open, which no
reading of the record could reach — so the name is the fact's only home rather
than a second one, on ``challenges.withdrawn``'s exemption.

**``games.seat_vacated`` and ``games.line_up_reseated`` are the seventh and
eighth** (``docs/adr/0162``): the two ways a line-up moves after the plan, each
told by ``challenges`` in the transaction of the act that caused it. Neither
announces a standing.

The two most likely to be asked to carry more later are ``games.planned`` — a
game that one day comes from something other than a challenge — and
``games.result_proposed``, if a score ever grows a shape richer than sets. Either
will be a version 2 registered beside version 1, never an edit to it: the rows
already in the store must keep decoding.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.games.application.handlers import LogGameEvent
from app.modules.games.domain.events import (
    GameCalledOff,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
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
)


def register_game_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_game_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogGameEvent(name))
