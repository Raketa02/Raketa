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
_RATING_NAMESPACE = uuid5(NAMESPACE_URL, "raketa/skill-rating")


def skill_rating_id(player_id: UUID, sport: Sport) -> UUID:
    """The deterministic event-stream id for one player's rating in one sport."""

    return uuid5(_RATING_NAMESPACE, f"{player_id}:{sport.value}")


# An Assessment stream is keyed by (player, sport, attempt). A rating has one
# stream per pair; a *run* can happen more than once for a pair — a run that was
# abandoned still exists, and the next one is a genuinely new stream — so the
# attempt is what distinguishes them.
#
# **This is a concurrency control, not a naming convenience.** Two starts that
# both read the store before either appends compute the same attempt, therefore
# the same stream id, therefore collide on version 1 of one stream — and
# ``uq_event_store_stream_version`` rejects the loser. With a random id each call
# minted its own stream, there was nothing for them to collide on, and both
# succeeded (#35).
_ASSESSMENT_NAMESPACE = uuid5(NAMESPACE_URL, "raketa/assessment")


def assessment_stream_id(player_id: UUID, sport: Sport, attempt: int) -> UUID:
    """The event-stream id for one player's nth run at one sport, zero-based.

    Derivable from the player, so an id is guessable by anyone who knows a player
    id — and that leaks nothing. Reading an assessment requires saying whose it
    is, and another player's is reported exactly as an absent one, so a guessed
    id answers not-found either way. What identity buys here is that the pair
    cannot quietly acquire two streams for the same attempt.
    """

    return uuid5(_ASSESSMENT_NAMESPACE, f"{player_id}:{sport.value}:{attempt}")
