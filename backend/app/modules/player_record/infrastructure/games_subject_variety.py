"""``SubjectVariety`` over ``games``' published fold. **A rename and nothing else.**

Two words change at this seam and no arithmetic does. ``games`` measured
``distinct_counterparts`` over ``counted_games`` — *everybody who was on a court
with them*, on that context's own rule that a pair is anybody you have played —
and a record prints ``distinct_opponents`` over ``games_played``, which is what
the row is called on screen. The honest word stays with the measurement and the
product's word stays on the sheet; this file is the one place they meet
(``docs/adr/0155``).

**The share is not computed here, and not anywhere on this side of the wire.**
The pair crosses and the client divides — because *fourteen of twenty* and *seven
of ten* are the same percentage and different claims, and this card argues two
rows above that a bar alone hides which one a reader is looking at.

**The absence passes straight through.** ``None`` from the provider is ``None``
here: a player no counted game was ever recorded for has no habit to describe,
and every layer between the fold and the response spells that the same way rather
than turning it into a nought on the way past.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.ports import OpponentVarietyQuery
from app.modules.player_record.domain.record import OpponentVariety


@final
class GamesSubjectVariety:
    """How widely this person spreads their games, in the record's own words."""

    def __init__(self, games: OpponentVarietyQuery) -> None:
        self._games = games

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> OpponentVariety | None:
        """The pair, renamed — or nothing, unchanged.

        **One player, because the port on both sides says so.** The fold behind
        this is unbounded, and the reason neither signature admits a collection
        is the same on both sides of the seam: a career statistic in a set-shaped
        read is one somebody calls inside a walk over five hundred candidates.
        """

        measured = await self._games.variety_of(player_id, now=now)
        if measured is None:
            return None
        return OpponentVariety(
            distinct_opponents=measured.distinct_counterparts,
            games_played=measured.counted_games,
        )


__all__ = ["GamesSubjectVariety"]
