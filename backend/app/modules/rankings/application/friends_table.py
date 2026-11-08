"""A reader's Friends table in a sport (#771; ``docs/adr/0203`` §3, §10; the
mechanics §4.2, §5–§7, §16).

**The reader and their friends** — Friends' own friend list, read live through
``ReadersFriends`` — **with at least one result whose last settled within the
90 days**. **Worked out on each read, kept nowhere**: one pass of the
projection over that set alone (``RankingRows.listed(…, among=)``), the same
statement General's order is read by, so the order, every place and every chip
are worked out from one reading, over **this set only** — places counted within
it, and each chip comparing a place now with where today's same players stood
by their Levels 7 days earlier. **So an arrival moves nobody**: a friend just
added stands in both orders, and so does one whose first result has just put
them on. *New* is the 7 days after a first result.

**The whole table, never a page**: a friend list is the reader's own, and its
rows are read in the same one question for their faces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.rankings.domain.general_order import (
    GeneralOrder,
    ListedRow,
    OrderInHand,
    work_out,
)
from app.modules.rankings.domain.ports import RankingRows, ReadersFriends
from app.modules.rankings.domain.ranking import (
    FRIENDS_ENTRY,
    RankingRow,
    RankingView,
    chips_since,
    listed_since,
)


@final
@dataclass(frozen=True, slots=True)
class FriendsRead:
    """The table, the reader's row of it, and the reader's own row in the
    sport, read live."""

    table: OrderInHand
    mine: ListedRow | None
    own: RankingRow | None

    @property
    def friends_listed(self) -> int:
        """How many of the table are the reader's friends — the reader's own
        row aside."""

        return self.table.listed - (self.mine is not None)

    @property
    def place(self) -> int | None:
        """The reader's Friends place — ``None`` when they aren't listed, and
        when no friend is: *Just you so far* is no place (the mechanics §8)."""

        if self.mine is None or self.friends_listed == 0:
            return None
        return self.mine.place


@final
class TheFriendsTable:
    def __init__(self, *, rows: RankingRows, friends: ReadersFriends) -> None:
        self._rows = rows
        self._friends = friends

    async def read(self, sport: Sport, *, now: Instant, reader: UUID) -> FriendsRead:
        """``reader``'s Friends table in the sport, as it stands at ``now``."""

        friends = await self._friends.friends_of(reader)
        own = next(
            (row for row in await self._rows.of_player(reader) if row.sport is sport),
            None,
        )
        table: GeneralOrder = work_out(
            sport,
            await self._rows.listed(
                sport,
                at_least=FRIENDS_ENTRY,
                since=listed_since(now),
                then=chips_since(now),
                among={reader, *friends},
            ),
            now=now,
            view=RankingView.FRIENDS,
        )
        mine = next((row for row in table.rows if row.player_id == reader), None)
        return FriendsRead(table=OrderInHand(table), mine=mine, own=own)
