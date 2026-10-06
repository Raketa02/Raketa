"""A game event nothing writes any more still decodes, and folds to nothing.

``games.dismissed`` was the old game card's *Remove this card* (``docs/adr/0172``
§5), and it went with the challenges (#578). Rows of it are already in stores —
a booked game called off at its cut-off could be dismissed — and every read of a
game walks its whole stream: the rating catch-up, ``GET /games``, the history
reads. **Stored events outlive the code that wrote them**
(``.claude/rules/domain-events.md``), so the name stays registered, and the fold
reads the row and changes nothing but the stream's version.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.kernel import Sport, instant
from app.modules.games.application.event_subscriptions import register_game_events
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.standing import GameStanding
from app.shared.ids import new_uuid

ANA, BO, CY, DEE = (new_uuid() for _ in range(4))
BOOKED_AT = instant(datetime(2026, 9, 10, 18, 0, tzinfo=timezone.utc))
HOUR = instant(BOOKED_AT + timedelta(days=3))


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_game_events(catalog)
    return JsonEventCodec(catalog)


def _a_game_called_off_at_its_cut_off() -> Game:
    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=ANA),
                Seating(side=GameSide.A, player_id=BO),
                Seating(side=GameSide.B, player_id=CY),
                Seating(side=GameSide.B, player_id=DEE),
            )
        ),
        occurred_at=BOOKED_AT,
        starts_at=HOUR,
    )
    game.vacate(DEE, occurred_at=instant(BOOKED_AT + timedelta(hours=1)))
    game.call_off(by=None, occurred_at=instant(BOOKED_AT + timedelta(hours=2)))
    return game


def test_a_stored_dismissal_decodes_and_folds_to_nothing_but_a_version():
    game = _a_game_called_off_at_its_cut_off()
    written = game.pull_events()
    dismissed = _codec().decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type="games.dismissed",
            schema_version=1,
            payload={
                "game_id": str(game.game_id),
                "dismissed_by": str(ANA),
                "occurred_at": (BOOKED_AT + timedelta(hours=3)).isoformat(),
            },
            occurred_at=instant(BOOKED_AT + timedelta(hours=3)),
        )
    )

    folded = Game.from_history([*written, dismissed])

    assert folded.version == len(written) + 1, "the row is a version of the stream"
    assert folded.standing_at(HOUR) is GameStanding.CALLED_OFF
    assert folded.line_up == game.line_up
    assert folded.called_off_at == game.called_off_at
