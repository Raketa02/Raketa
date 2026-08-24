"""The channel's two tables: the one line per player, the phones, the migration.

Driven against the real SQLite the fast suite already stands up, because every
claim here is a property of the **table** rather than of a fake: the key that
makes one row per player mean *one live message*, the partial index the tick
reads, the predicate that keeps an owed send at its earlier moment, the delete
that stops a signed-out phone receiving somebody else's seats, and the two DDLs
agreeing.

The migration is compared through the same recorder `test_cascade_stores.py`
and `test_command_log.py` use, and for its reason: a migration and a model that
describe different tables is a defect that only shows up on a database nobody
has run yet.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base
from app.kernel import Instant, minutes, shifted

from app.modules.now.domain.push import (
    LiveLine,
    Platform,
    PushDevice,
    TimeSensitiveSetting,
)
from app.modules.now.infrastructure.push_stores import (
    SqlAlchemyPushDevices,
    SqlAlchemyPushLines,
)
from app.modules.now.infrastructure.sqlalchemy_push_models import PushLineORM
from tests.unit.match_records import START

NOW: Instant = START
LATER: Instant = shifted(START, minutes(5))


def _owed(player: UUID, at: Instant) -> LiveLine:
    """The line a send read: the player, and the moment its debt was owed at.

    Both halves are load-bearing — clearing a debt is a compare-and-set against
    that moment, so a case that settled by player id alone would be asserting a
    port this one does not have.
    """

    return LiveLine(player_id=player, due_at=at)


def a_device(
    player: UUID,
    *,
    token: str = "ExponentPushToken[aaaaaaaaaaaaaaaaaaaaaa]",
    platform: Platform = Platform.IOS,
    setting: TimeSensitiveSetting = TimeSensitiveSetting.ENABLED,
    at: Instant = NOW,
) -> PushDevice:
    return PushDevice(
        player_id=player,
        token=token,
        platform=platform,
        time_sensitive=setting,
        registered_at=at,
    )


# ---------------------------------------------------------------------------
# 1. The line, and the queue over it
# ---------------------------------------------------------------------------


async def test_owing_a_send_creates_the_line_it_will_be_read_from(
    session_factory,
) -> None:
    her = uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)

        owed = await lines.due(now=NOW, limit=10)

    assert owed == (LiveLine(player_id=her, named_match_id=None, due_at=NOW),)


async def test_a_send_already_owed_takes_the_later_moment(
    session_factory,
) -> None:
    """One row and one send, at the newest debt's moment.

    A player told about a second seat while her first send is still queued gets
    **one** send that sees both — which is what one row per player means on this
    side of the wire. The moment moving is what the compare-and-set below
    compares against; it cannot push her send into the future, because every
    moment written here is a dispatch's own instant and is therefore past.
    """

    her = uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)
        await lines.owe([her], at=LATER)

        (line,) = await lines.due(now=LATER, limit=10)

    assert line.due_at == LATER


async def test_a_send_owed_later_is_not_due_yet(session_factory) -> None:
    her = uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=LATER)

        assert await lines.due(now=NOW, limit=10) == ()
        assert len(await lines.due(now=LATER, limit=10)) == 1


async def test_one_dispatch_owes_a_batch_in_one_write(session_factory) -> None:
    """Forty people told about one seat is one statement, not forty."""

    told = [uuid4() for _ in range(4)]
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe(told, at=NOW)

        owed = await lines.due(now=NOW, limit=10)

    assert {line.player_id for line in owed} == set(told)


async def test_owing_nobody_writes_nothing(session_factory) -> None:
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([], at=NOW)

        assert await lines.due(now=NOW, limit=10) == ()


async def test_a_replaced_line_names_the_match_and_owes_nothing(
    session_factory,
) -> None:
    her, match = uuid4(), uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)
        await lines.replaced(_owed(her, NOW), named_match_id=match, at=NOW)

        assert await lines.due(now=LATER, limit=10) == ()
        await lines.owe([her], at=LATER)
        (line,) = await lines.due(now=LATER, limit=10)

    assert line.named_match_id == match


async def test_a_settled_line_keeps_what_her_phone_shows(session_factory) -> None:
    """Clearing the debt is not forgetting the line.

    Nothing can take a message off a lock screen, so a settled send that dropped
    the naming column would make the next dispatch send her the same line again
    — which is the frequency control this table *is* failing open.
    """

    her, match = uuid4(), uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)
        await lines.replaced(_owed(her, NOW), named_match_id=match, at=NOW)
        await lines.owe([her], at=LATER)
        await lines.settled(_owed(her, LATER))

        assert await lines.due(now=LATER, limit=10) == ()
        await lines.owe([her], at=LATER)
        (line,) = await lines.due(now=LATER, limit=10)

    assert line.named_match_id == match


async def test_a_debt_owed_while_a_send_ran_survives_it(session_factory) -> None:
    """The compare-and-set, and the lost message it exists to prevent.

    A send reads her line, ranks her seats and decides; while it is deciding, a
    dispatch tells her about another seat and owes her a send. Clearing *the
    player's* debt on the way out would clear that one too, and the seat that
    dispatch was about would reach nobody — nothing re-reads old offers looking
    for the ones that were missed. So the debt cleared is the one that was read.
    """

    her = uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)
        (read,) = await lines.due(now=NOW, limit=10)

        # The dispatch that lands mid-send.
        await lines.owe([her], at=LATER)
        await lines.settled(read)

        still_owed = await lines.due(now=LATER, limit=10)

    assert [line.due_at for line in still_owed] == [LATER]


async def test_a_message_sent_mid_debt_still_moves_what_her_phone_shows(
    session_factory,
) -> None:
    """The other half: the naming columns move whatever the debt has done.

    The message really did reach her phone, and nothing can take it back — so a
    send that finds its debt already superseded must still record what it put
    there, or the next send names the same seat and sends it to her again.
    """

    her, match = uuid4(), uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her], at=NOW)
        (read,) = await lines.due(now=NOW, limit=10)
        await lines.owe([her], at=LATER)
        await lines.replaced(read, named_match_id=match, at=NOW)

        (line,) = await lines.due(now=LATER, limit=10)

    assert line.named_match_id == match
    assert line.due_at == LATER


async def test_one_player_is_one_row_however_often_she_is_told(
    session_factory,
) -> None:
    """ADR-0062's *one live message per player*, as a key rather than a rule."""

    her = uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        for _ in range(3):
            await lines.owe([her], at=NOW)
            await lines.replaced(_owed(her, NOW), named_match_id=uuid4(), at=NOW)

        rows = await session.execute(
            select(PushLineORM).where(PushLineORM.player_id == her)
        )

    assert len(rows.scalars().all()) == 1


async def test_owed_sends_come_back_oldest_first_and_bounded(
    session_factory,
) -> None:
    """A batch that is not deterministic is one whose truncation is not either.

    The two ids are chosen so that **player order and moment order disagree**:
    with random ones an order on the key alone agrees with the right answer half
    the time, and a case that passes on a coin toss is a case that cannot fail.
    """

    early, late = sorted((uuid4(), uuid4()), key=str, reverse=True)
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([late], at=LATER)
        await lines.owe([early], at=NOW)

        taken = await lines.due(now=LATER, limit=1)

    assert [line.player_id for line in taken] == [early]


async def test_the_settled_lines_are_not_in_the_ticks_query(
    session_factory,
) -> None:
    """Every player who has ever been sent a message keeps a row for ever.

    **One equivalent mutant is recorded here rather than papered over.**
    Deleting the read's `due_at IS NOT NULL` predicate changes nothing: a
    settled row holds `NULL`, and `NULL <= now` is unknown rather than true, so
    it is filtered by the comparison beside it either way. The predicate stays
    because it is the one the **partial index** is declared on, and a reader
    matching the index by accident is a reader somebody may quietly stop
    matching.
    """

    her, him = uuid4(), uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her, him], at=NOW)
        await lines.settled(_owed(her, NOW))

        owed = await lines.due(now=NOW, limit=10)

    assert [line.player_id for line in owed] == [him]


async def test_one_players_debt_is_not_another_players(session_factory) -> None:
    her, him = uuid4(), uuid4()
    async with session_factory() as session:
        lines = SqlAlchemyPushLines(session)
        await lines.owe([her, him], at=NOW)
        await lines.replaced(_owed(her, NOW), named_match_id=uuid4(), at=NOW)

        owed = await lines.due(now=NOW, limit=10)

    assert [line.player_id for line in owed] == [him]


# ---------------------------------------------------------------------------
# 2. The phones
# ---------------------------------------------------------------------------


async def test_a_device_round_trips_every_field_it_stores(session_factory) -> None:
    her = uuid4()
    device = a_device(
        her, platform=Platform.ANDROID, setting=TimeSensitiveSetting.NOT_SUPPORTED
    )
    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        await devices.register(device)

        assert await devices.for_player(her) == (device,)


async def test_registering_the_same_phone_twice_is_one_row(session_factory) -> None:
    """The same phone re-registers on every sign-in and every token rotation."""

    her = uuid4()
    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        await devices.register(a_device(her))
        await devices.register(
            a_device(her, setting=TimeSensitiveSetting.DISABLED, at=LATER)
        )

        held = await devices.for_player(her)

    assert len(held) == 1
    assert held[0].time_sensitive is TimeSensitiveSetting.DISABLED
    assert held[0].registered_at == LATER


async def test_two_phones_are_two_rows(session_factory) -> None:
    her = uuid4()
    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        await devices.register(a_device(her, token="hers-ios", at=NOW))
        await devices.register(
            a_device(her, token="hers-android", platform=Platform.ANDROID, at=LATER)
        )

        held = await devices.for_player(her)

    assert [device.token for device in held] == ["hers-ios", "hers-android"]


async def test_a_token_belongs_to_one_player_at_a_time(session_factory) -> None:
    """The sign-out case, and the one deletion anywhere in the push path.

    A phone signed into a second account still answers to the same token. A row
    left behind would put one player's seats on somebody else's lock screen,
    which is the one failure in this channel worse than silence — and it is
    unfixable afterwards, because nothing can take a delivered message back.

    **A second equivalent mutant is recorded here.** Dropping the delete's
    `player_id != device.player_id` leaves every state below identical: it would
    delete the registering player's own row too, and the insert beside it would
    put an equal one back inside the same transaction. The `!=` is kept because
    what it expresses is *replace her row*, and delete-then-insert is a window
    rather than a replacement — invisible to a test that owns the transaction,
    and not invisible to a second writer.
    """

    her, him = uuid4(), uuid4()
    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        await devices.register(a_device(her, token="one-phone"))
        await devices.register(a_device(him, token="one-phone", at=LATER))

        assert await devices.for_player(her) == ()
        assert [device.player_id for device in await devices.for_player(him)] == [him]


async def test_registering_takes_nothing_off_her_other_phone(
    session_factory,
) -> None:
    """The delete is scoped to *this token*, or a second phone is a sign-out."""

    her, him = uuid4(), uuid4()
    async with session_factory() as session:
        devices = SqlAlchemyPushDevices(session)
        await devices.register(a_device(her, token="hers-ios"))
        await devices.register(a_device(her, token="hers-android", at=LATER))
        await devices.register(a_device(him, token="his", at=LATER))

        assert len(await devices.for_player(her)) == 2
        assert len(await devices.for_player(him)) == 1


async def test_a_player_with_no_phone_answers_nothing(session_factory) -> None:
    async with session_factory() as session:
        assert await SqlAlchemyPushDevices(session).for_player(uuid4()) == ()


# ---------------------------------------------------------------------------
# 3. The migration against the models
# ---------------------------------------------------------------------------


class _Recorder:
    """Alembic's `op`, recording the DDL a migration asks for.

    `test_cascade_stores.py`'s, less the seeded `matches` table: neither of
    these tables carries a foreign key, and seeding one would let a `REFERENCES`
    that had appeared on either side compare equal to nothing.
    """

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        self.indexes: list[sa.Index] = []

    @property
    def created(self) -> list[str]:
        return list(self.metadata.tables)

    def create_table(self, name: str, *columns, **kw) -> None:
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
        / "0019_push_lines_and_devices.py"
    )
    spec = importlib.util.spec_from_file_location("push_migration", path)
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


def test_the_migration_creates_the_two_tables_the_models_describe(
    migrated,
) -> None:
    assert migrated.created == ["push_lines", "push_devices"]
    for name in ("push_lines", "push_devices"):
        assert _ddl(migrated.metadata.tables[name]) == _ddl(
            Base.metadata.tables[name]
        ), name


def test_the_migration_creates_the_indexes_the_models_describe(migrated) -> None:
    model = [
        index
        for name in ("push_lines", "push_devices")
        for index in sorted(Base.metadata.tables[name].indexes, key=lambda i: i.name)
    ]
    assert sorted(_ddl(one) for one in migrated.indexes) == sorted(
        _ddl(one) for one in model
    )


def test_the_ticks_index_is_partial_over_the_owed_rows(migrated) -> None:
    """Named rather than inferred, so it going missing from *both* sides fails.

    A comparison alone would call that agreement — and the settled rows are the
    ones that accumulate, so an index carrying them all grows with the platform
    for a query that never reads them.
    """

    for index in (
        next(one for one in migrated.indexes if one.name == "ix_push_lines_due_at"),
        next(
            one
            for one in Base.metadata.tables["push_lines"].indexes
            if one.name == "ix_push_lines_due_at"
        ),
    ):
        assert "due_at IS NOT NULL" in _ddl(index)


def test_the_token_has_an_index_of_its_own(migrated) -> None:
    """*Who else holds this token* cannot be answered off the key's left edge."""

    assert any(one.name == "ix_push_devices_token" for one in migrated.indexes)
    assert any(
        one.name == "ix_push_devices_token"
        for one in Base.metadata.tables["push_devices"].indexes
    )


def test_both_keys_are_named_on_both_sides(migrated) -> None:
    for name, columns in (
        ("push_lines", ["player_id"]),
        ("push_devices", ["player_id", "token"]),
    ):
        for table in (migrated.metadata.tables[name], Base.metadata.tables[name]):
            assert [
                column.name for column in table.primary_key.columns
            ] == columns, name
            assert table.primary_key.name == f"pk_{name}", name


def test_the_line_names_a_match_without_pointing_at_one(migrated) -> None:
    """Deliberately not a foreign key: it is what her phone *says*.

    A cascade on the match would rewrite that history when a row went, and a
    restrict would make deleting a match depend on whose lock screen mentioned
    it.
    """

    for table in (
        migrated.metadata.tables["push_lines"],
        Base.metadata.tables["push_lines"],
    ):
        assert table.c.named_match_id.foreign_keys == set()
        assert isinstance(table.c.named_match_id.type, UUIDType)
