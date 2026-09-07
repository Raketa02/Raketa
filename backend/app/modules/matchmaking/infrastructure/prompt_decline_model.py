"""The prompt-decline table. **Append-only, unexpiring, returned by no route.**

``the-engine.md`` §12 makes the decline a durable row while the raised prompt it
silences stays a Redis key with a TTL — the same split the pass record is under,
reached by the same argument about a **question** rather than a person. A
suppression that lapses leaves no trace the player was ever asked, and the two
constants in ``prompts.py`` declare falsifiers that need exactly that trace.

**The gate is the cache; the evidence is the row** — except that here the row is
also the gate, because there is no second store to derive one into: the filter
reads this table directly, once per search, and the window is a cut-off on
``declined_at`` rather than a key somebody has to keep in step.

**The primary key is a surrogate**, on the pass row's own argument: a natural key
on ``(player, prompt, sport)`` would collapse a second *not now* into the first,
and a decline never escalates — a second one buys the same thirty days and no
more — so nothing here counts them and there is nothing for a penalty to be grown
out of. Two rows are two facts with two moments.

**``sport`` is nullable, and the null is the meaning.** It is the sport the
suppression is keyed by, not the sport the search was in: ``NULL`` is *this
player, every sport*, which is what a radius and an availability grid are facts
about. What decides which one a row gets is ``declines.keyed_sport``, and there
is deliberately **no check constraint** restating that mapping here — a
biconditional naming prompt codes in SQL would be a second copy of the table the
domain owns, and the two would drift the first time a fifth prompt is added.

**No event and no outbox.** ADR-0094 says declining a prompt is not a domain fact
and earns no event, and its amendment kept that sentence literally: a pass earns
no event either, and is still a row.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class PromptDeclineORM(Base):
    """One *not now*, and the question it answered."""

    __tablename__ = "prompt_decline"
    __table_args__ = (
        # The filter's read: *what has this player declined lately*, both
        # families at once. The date is in the index because the window is
        # always applied — an unbounded read here would grow with the player's
        # whole history of saying no.
        Index("ix_prompt_decline_player", "player_id", "declined_at"),
    )

    #: A surrogate, because the fact is the **answer** and not the question. See
    #: the module docstring: a natural key would make a second decline
    #: unrepresentable, and two declines a month apart are two facts.
    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: The prompt's own code, which is the whole of the key — never the value it
    #: quoted. A player who declines *keep 22 km?* answered about a habit, and
    #: the ladder hands them a different number next month.
    prompt: Mapped[str] = mapped_column(String(50), nullable=False)
    #: What the silence is keyed by, or ``NULL`` for the player themselves.
    sport: Mapped[str | None] = mapped_column(String(50), nullable=True)
    declined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
