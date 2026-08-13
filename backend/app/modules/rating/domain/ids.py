"""Identity in the rating context.

A **Player** is a User acting in the player app — its identity *is* the
``UserId``. A distinct ``PlayerId`` type exists so the code reads in the domain's
vocabulary and the two have one place to diverge later; there is no players
table.
"""

from __future__ import annotations

from typing import NewType
from uuid import NAMESPACE_URL, UUID, uuid5

from app.kernel import Sport

PlayerId = NewType("PlayerId", UUID)

# A Skill rating stream is keyed by (player, sport). A deterministic id derived
# from that pair means the pair has exactly one stream, found without a lookup
# table — every sport is fully isolated, so there is nothing to coordinate.
_RATING_NAMESPACE = uuid5(NAMESPACE_URL, "rakieta/skill-rating")


def skill_rating_id(player_id: UUID, sport: Sport) -> UUID:
    """The deterministic event-stream id for one player's rating in one sport."""

    return uuid5(_RATING_NAMESPACE, f"{player_id}:{sport.value}")
