"""Two tables: the offers a cascade wrote, and the dispatches it has left to run.

**The first tables Now owns.** Every other write on this screen goes through
another context's aggregate — a departure and a result through ``Match``, a
queue place through the table Matches keeps — and ADR-0070's *"Now owns no
aggregate and writes nothing"* has been literally true until here. It still owns
no aggregate: nothing below is a consistency boundary, nothing has a version
column, and no invariant spans two rows. What it owns is a **record of what it
told whom**, and that has no other home.

It is not Matches', and the reason is the reason ADR-0091 gave for the standby
queue and gives more strongly here: **the match is unchanged by an offer.** No
rung reads one, no deadline moves, no seat changes state. Routing it through
``Match`` would bump ADR-0034's version column on every dispatch and invalidate
the scoring-context cache keyed ``matchId : recordVersion`` for a fact the
scoring context does not contain — forty people told about a seat would mean
forty cache misses on the busiest read in the product.

It is not the kernel's either. The ladder's seven rungs and its two waves are
ADR-0061's ranking policy, which is the same kind of thing ``funnel.py`` holds:
one implementation, one reader tree. ``Cover`` moved to the kernel because two
contexts *authored* it; nothing outside the cascade authors a rung.

**Neither table announces anything**, on ADR-0091's rule: the outbox is the
trail a support agent reads for a game somebody **paid for**, and an offer moves
no money and confers no place. ADR-0065 ranks *"the whole live set every
dispatch"*, which is a query over these rows rather than a subscription to them.

Nothing here is PostgreSQL-only.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class MatchOfferORM(Base):
    """One seat, put in front of one player, once.

    **Keyed ``(vacancy_id, player_id)``, and that key is the whole of *nobody is
    told twice*.** ADR-0061 promises that a suppressed wave resuming does not
    re-notify anybody already reached; the caller filters, and this refuses. Two
    guards for one rule, deliberately: the filter is what stops a rating replay
    and a score being paid to write nothing, and the key is what makes the
    promise true when two dispatches race.

    Keyed on the **hole** rather than on the match, because rung 3 —
    *offered an earlier vacancy on this match and did not get it* — is a
    comparison of holes. Filed under the match alone, a second hole could not be
    told from the first and the rung would answer *everybody already told*,
    which is every rung below it collapsed into one.

    **Never deleted and never withdrawn.** ADR-0061 keeps a taken seat honest by
    the *wording* rather than by retraction — *"a seat just opened, first to
    take it"* is true after somebody else takes it — and ADR-0062 adds that
    nothing is ever removed from a lock screen. So there is no ``withdrawn_at``
    and no state: an offer is a fact about the past, and whether the seat is
    still there is a question about the **match**, asked live.
    """

    __tablename__ = "match_offers"

    vacancy_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: Not a foreign key, for the reason ``match_seats.player_id`` is not one: a
    #: player lives behind a projection in another context.
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    match_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: Which rung of ADR-0061's ladder she stood on. Stored because it is read:
    #: ADR-0065 words the push differently for a seat she **asked** about than
    #: for one chosen for her, and that is the only place the difference shows.
    rung: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    #: Her fit for this match at the moment she was told. A fact about the
    #: dispatch and never re-read as a current score — the match moves.
    fit: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    #: What taking it would have cost her when she was told, in grosze. Stored
    #: because it is the sentence she was shown; ``kernel.seat_price`` answers
    #: the same question live, and the two differ exactly when the rescue
    #: deadline passed in between — a real change she is entitled to see.
    price_grosze: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    #: ``open`` for every row in v1. ADR-0061 retired the exclusive offer; the
    #: column exists because the kernel keeps both names so the ladder can say
    #: the other sentence the day it exists, not a release later.
    kind: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    offered_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        # Named, like `pk_command_log` and `pk_match_standby_places`, because
        # this key is the thing a decision rests on: a constraint a support
        # agent can find by name in a PostgreSQL error is one somebody can
        # reason about.
        sa.PrimaryKeyConstraint("vacancy_id", "player_id", name="pk_match_offers"),
        # Rung 3 asks *who has been told about any hole in this match*, and the
        # offers region asks *what has been offered to this player*. The
        # composite key answers neither from its own left edge.
        sa.Index("ix_match_offers_match_id", "match_id"),
        sa.Index("ix_match_offers_player_id", "player_id"),
    )


class MatchCascadeWaveORM(Base):
    """One dispatch waiting to happen. **Two rows per hole and no more.**

    ADR-0061's all-at-once shape in a table: *"an eligible set computed once,
    two dispatch jobs, first-to-accept wins"*. A row per candidate is the
    one-at-a-time design this replaced, and it needed a hold, a clock and a cap
    on every one of them.

    **Its own queue and not the match's schedule.** ``next_wake`` is computed by
    the kernel from the record on every write (ADR-0076) and a dispatch is not a
    boundary the ladder reads — nothing about the match resolves differently at
    vacancy + 10 minutes. Putting it there would be a threshold in the
    timekeeper, which ADR-0076 forbids by name.

    ``dispatched_at`` is the whole of the state: null is outstanding, set is
    done. A dispatch that reached **nobody** is still done — an empty rung is a
    real answer, and leaving the row due would re-run the whole pool every tick
    for a hole nobody can fill.
    """

    __tablename__ = "match_cascade_waves"

    vacancy_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True
    )
    #: 1 or 2 — ADR-0061's two dispatches. A small integer rather than a string,
    #: because the wave's *number* is what the ADR's table is written in.
    wave: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True)
    match_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        sa.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: When it may run, with the quiet hours **already applied**. Decided once,
    #: when the hole opened: re-deciding it on every tick would let a dispatch
    #: held to 08:00 be re-held to tomorrow's 08:00 for ever if a tick were
    #: ever late, which is the seat quietly never reaching anybody.
    due_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "vacancy_id", "wave", name="pk_match_cascade_waves"
        ),
        # The tick's one query: outstanding rows whose moment has come. Partial
        # on the outstanding ones, like `ix_matches_next_wake_at` — the done
        # rows are the ones that accumulate, and an index carrying them all
        # would grow without bound for a query that never reads them.
        sa.Index(
            "ix_match_cascade_waves_due_at",
            "due_at",
            postgresql_where=sa.text("dispatched_at IS NULL"),
            sqlite_where=sa.text("dispatched_at IS NULL"),
        ),
    )
