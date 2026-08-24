"""The cascade's two tables: the offers, the queue, and the migration behind them.

Driven against the real SQLite the fast suite already stands up, because every
claim here is a property of the **table** rather than of a fake: the key that
refuses a second offer, the partial index the tick reads, the predicate that
stops a dispatch being pushed later, and the two DDLs agreeing.

The migration is compared through the same recorder `test_command_log.py`
established, and for its reason: a migration and a model that describe different
tables is a defect that only shows up on a database nobody has run yet.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.infrastructure.database.base import Base
from app.kernel import Instant, OfferKind, SeatShare, grosze, minutes, shifted

from app.modules.now.domain.cascade import Offer, PendingWave, Rung, Wave
from app.modules.now.infrastructure.cascade_stores import (
    SqlAlchemyCascadeWaves,
    SqlAlchemyOffers,
    offer_of,
)
from app.modules.now.infrastructure.sqlalchemy_cascade_models import (
    MatchCascadeWaveORM,
    MatchOfferORM,
)
from tests.unit.match_records import START

NOW: Instant = START
PRICE: SeatShare = SeatShare(grosze(3800))


def an_offer(
    *,
    match: UUID,
    vacancy: UUID,
    player: UUID,
    rung: Rung = Rung.IN_THE_BAND,
    fit: int = 88,
    at: Instant = NOW,
) -> Offer:
    return Offer(
        match_id=match,
        vacancy_id=vacancy,
        player_id=player,
        player_rung=rung,
        fit=fit,
        price=PRICE,
        kind=OfferKind.OPEN,
        offered_at=at,
    )


def a_wave(
    *, match: UUID, vacancy: UUID, wave: Wave = Wave.FIRST, due: Instant = NOW
) -> PendingWave:
    return PendingWave(
        match_id=match, vacancy_id=vacancy, wave=wave, due_at=due
    )


@pytest.fixture
async def match_id(session_factory) -> UUID:
    """A match row, because both tables carry a foreign key to one.

    Inserted as a bare row rather than through the aggregate: what is under test
    is two tables that hang off `matches.id`, and standing up a whole match
    through `PostMatch` would make every case here depend on a context it is not
    about.
    """

    async with session_factory() as session:
        which = await _a_match_row(session)
        await session.commit()
    return which


async def _a_match_row(session) -> UUID:
    """The narrowest row `matches` will accept, and nothing more.

    Every column it names is `NOT NULL` with no server default; the rest of the
    table is left to its own defaults, because what these cases are about is two
    tables hanging off `matches.id` and a row assembled through `PostMatch`
    would make each of them depend on a context they are not about.
    """

    from app.modules.matches.infrastructure.sqlalchemy_match_models import MatchORM

    which = uuid4()
    await session.execute(
        sa.insert(MatchORM).values(
            id=which,
            club_id=uuid4(),
            category_id=uuid4(),
            sport="PADEL",
            start=NOW,
            duration_minutes=90,
            share_grosze=3800,
            counted=True,
            created=NOW,
            created_at=NOW,
            kind="open",
            pay_model="split",
            policy_window_minutes=1440,
            policy_join_cut_minutes=120,
            policy_prob_hold=True,
            version=1,
        )
    )
    return which


# ---------------------------------------------------------------------------
# The offers
# ---------------------------------------------------------------------------


async def test_an_offer_round_trips_every_field_it_stores(
    session_factory, match_id
) -> None:
    """Read back through `offer_of`, which is the one mapper the region shares.

    A rung stored as an integer and mapped back in two places is two answers to
    *which rung was she on*, so the store's own reader is the one asserted.
    """

    vacancy, player = uuid4(), uuid4()
    async with session_factory() as session:
        await SqlAlchemyOffers(session).record(
            [
                an_offer(
                    match=match_id,
                    vacancy=vacancy,
                    player=player,
                    rung=Rung.STANDBY,
                    fit=93,
                )
            ]
        )
        await session.commit()

        row = (
            await session.execute(
                select(MatchOfferORM).where(MatchOfferORM.vacancy_id == vacancy)
            )
        ).scalar_one()

    read = offer_of(row)
    assert read.match_id == match_id
    assert read.vacancy_id == vacancy
    assert read.player_id == player
    assert read.player_rung is Rung.STANDBY
    assert read.fit == 93
    assert read.price == PRICE
    assert read.kind is OfferKind.OPEN
    assert read.offered_at == NOW


async def test_a_player_already_told_about_a_hole_is_left_exactly_as_she_was(
    session_factory, match_id
) -> None:
    """ADR-0061's *"nobody is told twice"*, in the store rather than the caller.

    The **instant does not move**, which is the half that matters: ADR-0065
    keeps one live message per player, and a row re-stamped an hour later is the
    same person told again as far as that rule can tell.
    """

    vacancy, player = uuid4(), uuid4()
    later = shifted(NOW, minutes(30))

    async with session_factory() as session:
        offers = SqlAlchemyOffers(session)
        await offers.record(
            [an_offer(match=match_id, vacancy=vacancy, player=player, fit=70)]
        )
        await offers.record(
            [
                an_offer(
                    match=match_id,
                    vacancy=vacancy,
                    player=player,
                    fit=99,
                    at=later,
                )
            ]
        )
        await session.commit()

        rows = (
            await session.execute(
                select(MatchOfferORM).where(MatchOfferORM.vacancy_id == vacancy)
            )
        ).scalars().all()

    assert len(rows) == 1
    assert rows[0].fit == 70
    # Compared through the store's own reader, because SQLite drops the
    # column's timezone and the comparison is about the *moment* rather than
    # about which dialect kept its offset.
    assert offer_of(rows[0]).offered_at == NOW


async def test_two_holes_in_one_match_are_two_offers_for_one_player(
    session_factory, match_id
) -> None:
    """The key is on the **hole**, and rung 3 is what needs it to be.

    *Offered an earlier vacancy on this match and did not get it* is a
    comparison of holes; filed under the match alone, a second hole could not be
    told from the first.
    """

    first, second, player = uuid4(), uuid4(), uuid4()
    async with session_factory() as session:
        offers = SqlAlchemyOffers(session)
        await offers.record(
            [an_offer(match=match_id, vacancy=first, player=player)]
        )
        await offers.record(
            [an_offer(match=match_id, vacancy=second, player=player)]
        )
        await session.commit()

        assert await offers.offered_for(vacancy_id=first) == {player}
        assert await offers.offered_for(vacancy_id=second) == {player}
        assert await offers.reached_on(match_id=match_id) == {player}


async def test_the_two_reads_answer_different_questions(
    session_factory, match_id
) -> None:
    """One hole's audience against the whole match's, with two holes to tell apart."""

    first, second = uuid4(), uuid4()
    early, late = uuid4(), uuid4()

    async with session_factory() as session:
        offers = SqlAlchemyOffers(session)
        await offers.record([an_offer(match=match_id, vacancy=first, player=early)])
        await offers.record([an_offer(match=match_id, vacancy=second, player=late)])
        await session.commit()

        assert await offers.offered_for(vacancy_id=second) == {late}
        assert await offers.reached_on(match_id=match_id) == {early, late}


async def test_offers_on_another_match_are_not_this_matchs(
    session_factory, match_id
) -> None:
    """The negative control for `reached_on`, which is rung 3's whole source."""

    stranger = uuid4()
    async with session_factory() as session:
        other = await _a_match_row(session)
        offers = SqlAlchemyOffers(session)
        await offers.record(
            [an_offer(match=other, vacancy=uuid4(), player=stranger)]
        )
        await session.commit()

        assert await offers.reached_on(match_id=match_id) == frozenset()


async def test_recording_nothing_writes_nothing(session_factory, match_id) -> None:
    async with session_factory() as session:
        await SqlAlchemyOffers(session).record([])
        await session.commit()

        assert (
            await session.scalar(
                select(sa.func.count()).select_from(MatchOfferORM)
            )
            == 0
        )


# ---------------------------------------------------------------------------
# The dispatch queue
# ---------------------------------------------------------------------------


async def test_a_dispatch_is_due_when_its_moment_has_come(
    session_factory, match_id
) -> None:
    """Asserted a minute either side, because a region is not a boundary."""

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open([a_wave(match=match_id, vacancy=vacancy, due=NOW)])
        await session.commit()

        assert (
            await waves.due(now=shifted(NOW, minutes(-1)), limit=10)
        ) == ()
        assert len(await waves.due(now=NOW, limit=10)) == 1
        assert len(await waves.due(now=shifted(NOW, minutes(1)), limit=10)) == 1


async def test_a_dispatch_that_has_run_is_never_due_again(
    session_factory, match_id
) -> None:
    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open([a_wave(match=match_id, vacancy=vacancy)])
        await waves.dispatched(vacancy_id=vacancy, wave=Wave.FIRST, at=NOW)
        await session.commit()

        assert await waves.due(now=NOW, limit=10) == ()


async def test_the_two_waves_of_one_hole_are_two_rows(
    session_factory, match_id
) -> None:
    """Marking one done leaves the other outstanding, which is the whole shape."""

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [
                a_wave(match=match_id, vacancy=vacancy, wave=Wave.FIRST),
                a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND),
            ]
        )
        await waves.dispatched(vacancy_id=vacancy, wave=Wave.FIRST, at=NOW)
        await session.commit()

        due = await waves.due(now=NOW, limit=10)

    assert [one.wave for one in due] == [Wave.SECOND]


async def test_opening_the_same_hole_twice_does_not_double_the_queue(
    session_factory, match_id
) -> None:
    """A departure replayed under its own key must not queue four dispatches."""

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        rows = [
            a_wave(match=match_id, vacancy=vacancy, wave=Wave.FIRST),
            a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND),
        ]
        await waves.open(rows)
        await waves.open(rows)
        await session.commit()

        assert (
            await session.scalar(
                select(sa.func.count()).select_from(MatchCascadeWaveORM)
            )
            == 2
        )


async def test_bringing_a_dispatch_forward_moves_it_earlier(
    session_factory, match_id
) -> None:
    vacancy = uuid4()
    later = shifted(NOW, minutes(10))

    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND, due=later)]
        )
        await waves.bring_forward(vacancy_id=vacancy, wave=Wave.SECOND, to=NOW)
        await session.commit()

        assert len(await waves.due(now=NOW, limit=10)) == 1


async def test_bringing_a_dispatch_forward_never_pushes_it_later(
    session_factory, match_id
) -> None:
    """*Never later*, and the predicate is in the statement rather than a caller.

    The only thing that may move a dispatch is the empty-rung rule, and the only
    direction it may move is towards now — the quiet hours were applied when the
    hole opened, and re-applying them on a tick could hold a dispatch to
    tomorrow's 08:00 for ever.
    """

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND, due=NOW)]
        )
        await waves.bring_forward(
            vacancy_id=vacancy, wave=Wave.SECOND, to=shifted(NOW, minutes(60))
        )
        await session.commit()

        assert len(await waves.due(now=NOW, limit=10)) == 1


async def test_a_dispatch_that_has_run_cannot_be_brought_forward(
    session_factory, match_id
) -> None:
    """There is nothing left to bring forward, and a done row must stay done."""

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND, due=NOW)]
        )
        await waves.dispatched(vacancy_id=vacancy, wave=Wave.SECOND, at=NOW)
        await waves.bring_forward(
            vacancy_id=vacancy, wave=Wave.SECOND, to=shifted(NOW, minutes(-60))
        )
        await session.commit()

        assert await waves.due(now=NOW, limit=10) == ()
        # Read off the **row** and not off `due`, which answers nothing for a
        # done dispatch either way: dropping the outstanding predicate from the
        # statement moves a moment nobody can see through the port, and the
        # column is the only place that difference shows.
        row = (
            await session.execute(
                select(MatchCascadeWaveORM).where(
                    MatchCascadeWaveORM.vacancy_id == vacancy
                )
            )
        ).scalar_one()

    assert row.due_at.replace(tzinfo=NOW.tzinfo) == NOW


async def test_the_due_read_is_ordered_and_bounded(
    session_factory, match_id
) -> None:
    """Oldest first, and the tie broken by the key — total, so a limit is stable.

    Two holes opened in the same millisecond would otherwise be taken in
    whatever order the plan chose, and a batch that is not deterministic is one
    whose truncation is not either.
    """

    early, late = uuid4(), uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [
                # The **later** row is the first wave and the earlier one the
                # second, deliberately: with both on one wave, an order that
                # led on the wave number would agree with this one by accident,
                # and the assertion would be about nothing.
                a_wave(
                    match=match_id,
                    vacancy=late,
                    wave=Wave.FIRST,
                    due=shifted(NOW, minutes(-1)),
                ),
                a_wave(
                    match=match_id,
                    vacancy=early,
                    wave=Wave.SECOND,
                    due=shifted(NOW, minutes(-10)),
                ),
            ]
        )
        await session.commit()

        due = await waves.due(now=NOW, limit=10)
        assert [one.vacancy_id for one in due] == [early, late]
        assert len(await waves.due(now=NOW, limit=1)) == 1


async def test_two_dispatches_due_at_one_instant_are_ordered_by_their_key(
    session_factory, match_id
) -> None:
    """The tie-break, and it is what makes a `limit` mean the same thing twice.

    Two holes opened in the same millisecond would otherwise be taken in
    whatever order the plan chose, and a batch that is not deterministic is one
    whose truncation is not either. Asserted against the ids **sorted**, so the
    case cannot pass by having been given them in the right order.
    """

    first, second = sorted((uuid4(), uuid4()), key=lambda one: one.bytes)
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [
                a_wave(match=match_id, vacancy=second, due=NOW),
                a_wave(match=match_id, vacancy=first, due=NOW),
            ]
        )
        await session.commit()

        due = await waves.due(now=NOW, limit=10)

    assert [one.vacancy_id for one in due] == [first, second]


async def test_a_dispatch_round_trips_its_match_and_its_wave(
    session_factory, match_id
) -> None:
    """The batch hands what it read straight to `RunCascade`, so it must be whole."""

    vacancy = uuid4()
    async with session_factory() as session:
        waves = SqlAlchemyCascadeWaves(session)
        await waves.open(
            [a_wave(match=match_id, vacancy=vacancy, wave=Wave.SECOND)]
        )
        await session.commit()

        one = (await waves.due(now=NOW, limit=10))[0]

    assert one.match_id == match_id
    assert one.vacancy_id == vacancy
    assert one.wave is Wave.SECOND
    assert one.due_at == NOW


# ---------------------------------------------------------------------------
# The migration against the models
# ---------------------------------------------------------------------------


class _Recorder:
    """Alembic's `op`, recording the DDL a migration asks for.

    `test_command_log.py`'s, and shared by reading rather than by import: this
    file needs the two methods that migration uses and no more, and a helper in
    a third place would be a fixture two suites had to agree about.
    """

    #: The one table the migration's foreign keys point at. Seeded so the DDL
    #: **compiles with its references intact** rather than being compared with
    #: them dropped: a `REFERENCES matches(id) ON DELETE CASCADE` that went
    #: missing from the migration is exactly the difference this comparison is
    #: for, and a metadata that could not resolve it would compare two
    #: constraint-less tables and call them equal.
    REFERENCED = "matches"

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        sa.Table(
            self.REFERENCED,
            self.metadata,
            sa.Column("id", UUIDType(binary=False), primary_key=True),
        )
        self.indexes: list[sa.Index] = []

    @property
    def created(self) -> list[str]:
        """The tables `upgrade()` asked for, less the one seeded above."""

        return [
            name for name in self.metadata.tables if name != self.REFERENCED
        ]

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
        / "0018_match_offers_and_cascade_waves.py"
    )
    spec = importlib.util.spec_from_file_location("cascade_migration", path)
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


def test_the_migration_creates_the_two_tables_the_models_describe(migrated) -> None:
    assert migrated.created == ["match_offers", "match_cascade_waves"]
    for name in ("match_offers", "match_cascade_waves"):
        assert _ddl(migrated.metadata.tables[name]) == _ddl(
            Base.metadata.tables[name]
        ), name


def test_the_migration_creates_the_indexes_the_models_describe(migrated) -> None:
    """Including the **partial** one, which is the tick's whole query.

    A partial index compiled without its `WHERE` is a different index wearing
    one name, and it is the difference between the tick reading the outstanding
    rows and reading every dispatch ever run.
    """

    model = [
        index
        for name in ("match_offers", "match_cascade_waves")
        for index in sorted(Base.metadata.tables[name].indexes, key=lambda i: i.name)
    ]
    assert sorted(_ddl(one) for one in migrated.indexes) == sorted(
        _ddl(one) for one in model
    )


def test_the_ticks_index_is_partial_over_the_outstanding_rows(migrated) -> None:
    """Named rather than inferred, so it going missing from *both* sides fails.

    A comparison alone would call that agreement — and the done rows are the
    ones that accumulate, so an index carrying them all grows without bound for
    a query that never reads them.
    """

    for index in (
        next(
            one
            for one in migrated.indexes
            if one.name == "ix_match_cascade_waves_due_at"
        ),
        next(
            one
            for one in Base.metadata.tables["match_cascade_waves"].indexes
            if one.name == "ix_match_cascade_waves_due_at"
        ),
    ):
        assert "dispatched_at IS NULL" in _ddl(index)


def test_both_keys_are_named_on_both_sides(migrated) -> None:
    for name, columns in (
        ("match_offers", ["vacancy_id", "player_id"]),
        ("match_cascade_waves", ["vacancy_id", "wave"]),
    ):
        for table in (migrated.metadata.tables[name], Base.metadata.tables[name]):
            assert [
                column.name for column in table.primary_key.columns
            ] == columns, name
            assert table.primary_key.name == f"pk_{name}", name
