from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.money.application.handlers import LogMoneyEvent
from app.modules.money.domain.events import MovementRecorded, PlayerPseudonymised


def register_money_events(catalog: EventCatalog) -> None:
    catalog.register(MovementRecorded, name="money.movement_recorded", version=1)
    catalog.register(PlayerPseudonymised, name="money.player_pseudonymised", version=1)


def subscribe_money_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(MovementRecorded, LogMoneyEvent("money.movement_recorded"))
    dispatcher.subscribe(
        PlayerPseudonymised, LogMoneyEvent("money.player_pseudonymised")
    )
