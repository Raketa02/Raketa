"""``PromptDeclineLedger`` over SQLAlchemy. **It adds rows and it never commits.**

The transaction boundary is the command's, exactly as it is for the pass ledger
beside it.

**There is no delete and no update here.** A decline does not expire — it stops
silencing, which is a cut-off and not a state — and nothing but erasure will ever
remove one, so a method for either would be a method somebody reaches for.

**Nothing here can answer a question a route could ask.** No list, no count, no
*have I declined this*: the port declares two methods and this implements exactly
those, so *no route ever returns a decline* is a property of the shapes that
exist rather than of the routes that happen to have been written.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Sport
from app.modules.matchmaking.domain.declines import PromptDecline
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.infrastructure.prompt_decline_model import (
    PromptDeclineORM,
)
from app.shared.ids import new_uuid


class SqlAlchemyPromptDeclineLedger:
    """The durable record of every *not now*, over the caller's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, decline: PromptDecline) -> None:
        """Append one decline. The caller commits.

        The id is minted here rather than carried on :class:`PromptDecline`,
        because it is a storage identity and nothing in the domain, in a response
        or in a falsifier ever names it: what identifies a decline to anybody who
        asks is the player, the question and the moment.
        """

        self._session.add(
            PromptDeclineORM(
                id=new_uuid(),
                player_id=decline.player_id,
                prompt=decline.prompt.value,
                sport=None if decline.sport is None else decline.sport.value,
                declined_at=decline.at,
            )
        )
        await self._session.flush()

    async def suppressed_for(
        self, *, player_id: UUID, sport: Sport, since: datetime
    ) -> frozenset[Prompt]:
        """Which prompts are still silent for this player, in this sport.

        **One read for both families**, which is the read `raised_for` is written
        to beside it: the rows keyed on the player carry ``NULL`` and the rows
        keyed on a sport carry theirs, and a search that asked twice could be
        told two things about one moment.

        A code this build does not know is **dropped rather than raised on**. The
        table outlives any one deployment's vocabulary — a prompt retired next
        year leaves its rows behind — and a decline of a question nobody asks any
        more silences nothing, which is exactly what dropping it does.
        """

        rows = await self._session.execute(
            select(PromptDeclineORM.prompt)
            .where(
                PromptDeclineORM.player_id == player_id,
                PromptDeclineORM.declined_at >= since,
                or_(
                    PromptDeclineORM.sport.is_(None),
                    PromptDeclineORM.sport == sport.value,
                ),
            )
            .distinct()
        )
        return frozenset(
            Prompt[code] for (code,) in rows.all() if code in Prompt.__members__
        )
