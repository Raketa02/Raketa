"""The standby queue: the two writes, the read, and the table under them.

ADR-0087 says leaving standby needs *"a write that asks nothing"*, and the whole
of that sentence turns out to be a property of this table rather than of the
route above it:

1. **Asking twice is asking once**, so joining is idempotent and the pair is the
   primary key. That is what lets the route refuse an idempotency key.
2. **Leaving twice is leaving once**, so the delete reads no row count and a
   player who holds no place gets the same nothing as one who did.
3. **Deleted, not ended** — the opposite of every other child table in this
   context, and the decision rather than an oversight: a vacancy, a departure
   and a seat claim are kept because *what happened at 18:03* is a support
   question about money or a seat, and neither is true of a queue place.
4. **Nothing is announced.** Matches' obligation is *every change is its own
   named event*, and it is about a **match**; a queue place moves no money and
   confers no place, and its one reader is the cascade, which reads the list
   when a seat frees rather than following it.

Driven against the real SQLite the fast suite already stands up, because every
one of them is a property of the table rather than of a fake.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.kernel import Instant, instant, minutes, shifted
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchStandbyPlaceORM,
)
from app.modules.matches.infrastructure.sqlalchemy_standby_list import (
    SqlAlchemyStandbyPlaces,
)

NOW: Instant = instant(datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc))
LATER: Instant = shifted(NOW, minutes(90))


async def _places(session) -> int:
    return await session.scalar(select(func.count()).select_from(MatchStandbyPlaceORM))


async def _joined_at(session, match_id: UUID, player_id: UUID) -> datetime:
    """The stored moment, in UTC.

    SQLite hands back a naive datetime whatever went in, so the zone is put
    back here rather than compared away — the alternative is asserting a naive
    value, which would pass on a column that had lost its `timezone=True`.
    """

    stored = await session.scalar(
        select(MatchStandbyPlaceORM.joined_at).where(
            MatchStandbyPlaceORM.match_id == match_id,
            MatchStandbyPlaceORM.player_id == player_id,
        )
    )
    return stored.replace(tzinfo=timezone.utc)


async def test_a_join_puts_her_on_the_queue(session_factory) -> None:
    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await session.commit()

        assert await places.held_by(player) == frozenset({match})


async def test_a_player_who_never_asked_is_queued_for_nothing(session_factory) -> None:
    async with session_factory() as session:
        assert await SqlAlchemyStandbyPlaces(session).held_by(uuid4()) == frozenset()


async def test_the_queue_answers_only_this_player(session_factory) -> None:
    """It is a membership of a pair, and the read is the player's half of it."""

    match, mine, hers = uuid4(), uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=mine, at=NOW)
        await places.join(match_id=match, player_id=hers, at=NOW)
        await session.commit()

        assert await places.held_by(mine) == frozenset({match})


async def test_a_player_may_be_queued_for_several_matches(session_factory) -> None:
    one, two, player = uuid4(), uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=one, player_id=player, at=NOW)
        await places.join(match_id=two, player_id=player, at=NOW)
        await session.commit()

        assert await places.held_by(player) == frozenset({one, two})


async def test_asking_twice_is_asking_once(session_factory) -> None:
    """The property ADR-0087 rests the whole route's shape on.

    *Priority, not a place*: there is no position, so there is nothing a second
    ask could buy and nothing a duplicate row could mean. A second row would
    also make the cascade offer one seat to one player twice.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.join(match_id=match, player_id=player, at=LATER)
        await session.commit()

        assert await _places(session) == 1


async def test_a_second_join_does_not_move_the_moment_she_first_asked(
    session_factory,
) -> None:
    """Of the two answers the honest one is *when she first asked*.

    Nothing reads `joined_at` today — rung 1 of the invitation ladder is
    fit-ordered within itself (ADR-0061) — so this is about the fact staying
    true rather than about an order. A join that overwrote it would make a
    standing rule re-joining her every night look like somebody who asked
    tonight.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.join(match_id=match, player_id=player, at=LATER)
        await session.commit()

        assert await _joined_at(session, match, player) == NOW


async def test_leaving_takes_her_off(session_factory) -> None:
    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.leave(match_id=match, player_id=player)
        await session.commit()

        assert await places.held_by(player) == frozenset()


async def test_leaving_a_queue_she_is_not_on_is_the_state_she_asked_for(
    session_factory,
) -> None:
    """ADR-0087's reason for refusing an idempotency key, as a property.

    *"A repeated delete of a standby place a player no longer holds is the state
    they asked for."* Nothing raises, nothing is reported, and the second call
    answers exactly what the first did.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.leave(match_id=match, player_id=player)
        await places.leave(match_id=match, player_id=player)
        await session.commit()

        assert await places.held_by(player) == frozenset()


async def test_leaving_takes_off_one_pair_and_not_a_player_or_a_match(
    session_factory,
) -> None:
    """The delete names both halves of the key, so it cannot empty a queue."""

    match, other_match = uuid4(), uuid4()
    player, other_player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.join(match_id=other_match, player_id=player, at=NOW)
        await places.join(match_id=match, player_id=other_player, at=NOW)
        await places.leave(match_id=match, player_id=player)
        await session.commit()

        assert await places.held_by(player) == frozenset({other_match})
        assert await places.held_by(other_player) == frozenset({match})


async def test_leaving_deletes_the_row_rather_than_ending_it(session_factory) -> None:
    """The opposite of every other child table here, and it is the decision.

    A vacancy is filled, a departure settles, a claim ends — all three are kept
    because a support agent may be asked about them. A queue place moves no
    money and confers no place, so there is no fact a tombstone would preserve
    — and *"rejoining costs what joining cost, which is nothing"* is only true
    if the platform is not keeping a record of every time she changed her mind.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.leave(match_id=match, player_id=player)
        await session.commit()

        assert await _places(session) == 0


async def test_a_rejoin_after_a_leave_is_a_place_again(session_factory) -> None:
    """Which is what *free to rejoin* means, and the row being gone allows it."""

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.leave(match_id=match, player_id=player)
        await places.join(match_id=match, player_id=player, at=LATER)
        await session.commit()

        assert await places.held_by(player) == frozenset({match})
        assert await _joined_at(session, match, player) == LATER


async def test_neither_write_commits(session_factory) -> None:
    """The transaction boundary is the caller's, like every other write here.

    The seed writes a whole week in one, and the route closes the delete and the
    read that composes its answer together.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        await SqlAlchemyStandbyPlaces(session).join(
            match_id=match, player_id=player, at=NOW
        )
        await session.rollback()

    async with session_factory() as session:
        assert await _places(session) == 0


async def test_neither_write_announces_anything(session_factory) -> None:
    """The one place Matches departs from *every change is its own named event*.

    That obligation is about a **match**: the outbox is the only trail a support
    agent has for a game somebody paid for, because ADR-0034 keeps no history. A
    queue place is not a fact about the match — it is a fact about a viewer, and
    ``kernel.Viewer`` is where the resolver takes it — and its one reader is the
    cascade, which reads the list when a seat frees rather than following it.
    An outbox row nothing subscribes to is a field with no reader (ADR-0071),
    written once per tap.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)
        await places.leave(match_id=match, player_id=player)
        await session.commit()

        assert await session.scalar(
            select(func.count()).select_from(EventOutboxORM)
        ) == 0


async def test_a_join_is_visible_to_the_next_read_in_its_own_transaction(
    session_factory,
) -> None:
    """Because this app's sessions are ``autoflush=False``.

    A pending ORM object would be invisible to the very next ``SELECT``, and the
    caller that joins and then asks is not hypothetical: the seed's own name
    check does exactly that, in one transaction, and read a queue it had just
    written as empty.
    """

    match, player = uuid4(), uuid4()

    async with session_factory() as session:
        places = SqlAlchemyStandbyPlaces(session)
        await places.join(match_id=match, player_id=player, at=NOW)

        assert await places.held_by(player) == frozenset({match})


# --- the migration and the model describe one table -------------------------
#
# Two things describe `match_standby_places`: `Base.metadata`, which the fast
# suite builds a SQLite database from, and `0016_match_standby_places.py`, which
# is what a real database gets. Nothing else compares them, and a composite
# primary key present in one and absent from the other is the guarantee this
# whole file rests on holding in every test and nowhere else. The shape is
# `test_command_log.py`'s.


class _Recorder:
    """Stands in for `alembic.op`, collecting what `upgrade()` asks for."""

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        self.indexes: list[sa.Index] = []
        self.created: list[str] = []
        # The table this one hangs a foreign key on, declared here so the key
        # resolves and the DDL below is the DDL a real database gets. Stubbed
        # rather than replayed: `0009_matches` is not this migration's subject,
        # and `test_matches_migration.py` is where its own shape is asserted.
        sa.Table(
            "matches",
            self.metadata,
            sa.Column("id", UUIDType(binary=False), primary_key=True),
        )

    def create_table(self, name: str, *columns, **kw) -> None:
        self.created.append(name)
        sa.Table(name, self.metadata, *columns, **kw)

    def create_index(self, name, table, columns, unique=False, **kw) -> None:
        self.indexes.append(
            sa.Index(
                name,
                *(self.metadata.tables[table].c[column] for column in columns),
                unique=unique,
                **kw,
            )
        )

    def drop_table(self, name: str) -> None:  # pragma: no cover - upgrade only
        raise AssertionError("upgrade() must not drop a table")


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "0016_match_standby_places.py"
    )
    spec = importlib.util.spec_from_file_location("standby_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.op = recorder = _Recorder()
    module.upgrade()
    return recorder


def _ddl(subject) -> str:
    statement = (
        CreateIndex(subject) if isinstance(subject, sa.Index) else CreateTable(subject)
    )
    return str(statement.compile(dialect=postgresql.dialect())).strip()


def test_the_migration_creates_the_table_the_model_describes(migrated) -> None:
    assert migrated.created == ["match_standby_places"]
    assert _ddl(migrated.metadata.tables["match_standby_places"]) == _ddl(
        Base.metadata.tables["match_standby_places"]
    )


def test_the_migration_creates_the_index_the_model_describes(migrated) -> None:
    """*What is this player queued for* is paid on every compose of Now.

    The composite key answers the cascade's direction off its own left edge; the
    strip's direction has nothing to ride and needs this.
    """

    model = list(Base.metadata.tables["match_standby_places"].indexes)
    assert [_ddl(index) for index in migrated.indexes] == [
        _ddl(index) for index in model
    ]


def test_the_pair_is_the_primary_key_in_both(migrated) -> None:
    """Read out rather than inferred from the DDL comparison above.

    That comparison would stay green if *both* sides lost the key together,
    which is the edit somebody makes while adding a surrogate id — and the
    uniqueness is what makes joining idempotent in the database rather than in
    a read somebody could interleave.
    """

    for table in (
        migrated.metadata.tables["match_standby_places"],
        Base.metadata.tables["match_standby_places"],
    ):
        assert [column.name for column in table.primary_key] == [
            "match_id",
            "player_id",
        ]
