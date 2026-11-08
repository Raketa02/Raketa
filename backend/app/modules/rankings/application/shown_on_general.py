"""Whether the Ranking shows a player **to everybody** (#773; ``docs/adr/0203``
§9; the mechanics §12–§13): listed on General in at least one sport — five
results, the last within the 90 days — and *Show me in General* on.

**What lets a stranger in.** Two readers ask it, each through a port of its own
signed on this side or theirs: the record, whose fourth strand it is, for any
reader with or without a level; and Friends, which admits a request from
somebody the two share no group with only to a player it answers yes about.

**Both halves are read live and recorded nowhere.** The rows are the
projection's own, so a player is off the moment their 90 days run out, with no
kept order's minute between; the switch is **the profile's**, read off its
stream (``GeneralSwitches``) rather than the rows' copy the outbox follows it
into, so a player who turns it off is closed to strangers on the next open, not
after the delivery. **A player with no profile is shown to nobody**: nothing
answers *yes* about an id this platform cannot describe.

**What it costs**: one read of the player's rows (the primary key's prefix)
and, only while one of them is listed, one fold of their profile's stream — a
deliberate tap's worth, which is the only shape anybody asks it in.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.rankings.domain.ports import GeneralSwitches, RankingRows


@final
class ShownOnGeneral:
    def __init__(self, *, rows: RankingRows, switches: GeneralSwitches) -> None:
        self._rows = rows
        self._switches = switches

    async def shown(self, player_id: UUID, *, now: Instant) -> bool:
        """Listed on General in at least one sport at ``now``, and not hidden
        from it."""

        if not any(
            row.listed_on_general(now) for row in await self._rows.of_player(player_id)
        ):
            return False
        switch = await self._switches.switch_of(player_id)
        return switch is not None and not switch.hidden


__all__ = ["ShownOnGeneral"]
