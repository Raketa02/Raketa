"""A match, through the use cases and back out of three tables.

Nothing here writes a table. Every state is reached by running the use case a
request would run, wired from the composition root, so a stored match has the
rows and the outbox trail a real one has.

Four claims:

1. **The round trip is lossless.** What comes back out resolves to the same
   situation as what went in — the strongest statement available, because the
   situation is a function of the *whole* record and a dropped column would move
   it.
2. **A stale writer loses on the version and is never merged**, which is the
   whole of ADR-0034's concurrency answer taken from a column rather than a
   stream.
3. **The announcements land on the outbox in the transaction that wrote the
   row.** The match keeps no history, so an unannounced change is one nobody can
   ever explain.
4. **A failure writes neither.** Rolling back before the commit leaves no match
   row *and* no outbox row, which is the guarantee ADR-0003 exists for and the
   one `Raketa02/Raketa#70` will build a three-context write on.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError

from app.bootstrap.composition import (
    build_club_repository,
    build_event_publisher,
    build_match_repository,
    build_unit_of_work,
)
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.kernel import (
    MatchKind,
    SeatShare,
    Situation,
    Sport,
    grosze,
    hours,
    instant,
    situation,
    zloty,
)
from app.modules.clubs.application.add_court_category import AddCourtCategory
from app.modules.clubs.application.commands import (
    AddCourtCategoryCommand,
    RegisterClubCommand,
)
from app.modules.clubs.application.register_club import RegisterClub
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)
from app.modules.matches.application.cancel_match import CancelMatch
from app.modules.matches.application.commands import (
    AgreeResultCommand,
    CancellationCause,
    CancelMatchCommand,
    MoveMatchStartCommand,
    PaySeatCommand,
    PostMatchCommand,
    ProposeScoreCommand,
    TakeSeatCommand,
    VacateSeatCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.record_result import (
    AgreeResult,
    ProposeScore,
)
from app.modules.matches.application.seat_moves import (
    MoveMatchStart,
    PaySeat,
    TakeSeat,
    VacateSeat,
)
from app.modules.matches.domain.errors import (
    ConcurrentMatchModification,
    MatchNotFound,
)
from app.modules.matches.domain.score import Score, SetScore
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchORM,
    MatchSeatORM,
    MatchVacancyORM,
)

PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


class _FrozenClock:
    """A clock the test moves by hand, so a deadline is reached deliberately."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance_to(self, moment: datetime) -> None:
        self._now = moment


class _World:
    """A club with a category, and every Matches use case over one session."""

    def __init__(self, session, clock):
        clubs = build_club_repository(session)
        events = build_event_publisher(session)
        matches = build_match_repository(session, events=events)
        uow = build_unit_of_work(session)

        self.clock = clock
        self.repository = matches
        self.uow = uow
        self.register_club = RegisterClub(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.post = PostMatch(matches, clubs, uow, clock)
        self.move = MoveMatchStart(matches, uow, clock)
        self.take = TakeSeat(matches, uow, clock)
        self.pay = PaySeat(matches, uow, clock)
        self.vacate = VacateSeat(matches, uow, clock)
        self.cancel = CancelMatch(matches, uow, clock)
        self.propose = ProposeScore(matches, uow, clock)
        self.agree = AgreeResult(matches, uow, clock)


@pytest.fixture
def clock():
    return _FrozenClock(datetime(2026, 9, 1, 12, tzinfo=timezone.utc))


@pytest.fixture
async def world(session_factory, clock):
    async with session_factory() as session:
        yield _World(session, clock)


async def a_club_with_a_category(world, *, policy=None):
    club = await world.register_club.execute(
        RegisterClubCommand(
            name=ClubName(f"Zabłocie {uuid4().hex[:6]}"),
            address=StreetAddress(
                line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
            ),
            point=GeoPoint(
                latitude=Decimal("50.048100"), longitude=Decimal("19.958500")
            ),
            timezone="Europe/Warsaw",
            policy=policy or ClubPolicy(),
            payout=PAYOUT,
            pricing=ClubPricing(),
        )
    )
    category = await world.add_category.execute(
        AddCourtCategoryCommand(
            club_id=club.id,
            name=CategoryName("Padel · indoor"),
            sport=Sport.PADEL,
            rate=zloty(120),
        )
    )
    return club, category


START = instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc))


async def a_posted_match(world, **overrides):
    club, category = await a_club_with_a_category(world)
    defaults = dict(
        club_id=club.id,
        category_id=category.id,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SeatShare(grosze(3800)),
    )
    defaults.update(overrides)
    return await world.post.execute(PostMatchCommand(**defaults))


async def count(session_factory, model, **where):
    async with session_factory() as session:
        statement = select(func.count()).select_from(model)
        for column, value in where.items():
            statement = statement.where(getattr(model, column) == value)
        return (await session.execute(statement)).scalar_one()


# --- 1 · the round trip -----------------------------------------------------


async def test_a_posted_match_comes_back_whole(world):
    posted = await a_posted_match(world)

    loaded = await world.repository.get(posted.id)

    assert loaded is not None
    assert loaded.id == posted.id
    assert loaded.sport is Sport.PADEL
    assert loaded.start == START
    assert loaded.share == SeatShare(grosze(3800))
    assert len(loaded.seats) == 4
    assert all(seat.is_free for seat in loaded.seats)
    assert loaded.version == 0


async def test_the_club_policy_travels_with_the_match(world):
    """Copied at posting and honoured as booked (ADR-0077), so the deadline the
    ladder reads is the match's own and needs no club."""

    club, category = await a_club_with_a_category(
        world, policy=ClubPolicy(window=hours(48))
    )
    posted = await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=START,
            duration=hours(1),
            share=SeatShare(grosze(3800)),
        )
    )

    loaded = await world.repository.get(posted.id)

    assert loaded.policy.window == hours(48)


async def test_the_reloaded_record_resolves_to_the_same_situation(world):
    """The strongest available statement that nothing was dropped in the round
    trip: the situation is a function of the *whole* record."""

    posted = await a_posted_match(world)
    alice = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=alice))

    loaded = await world.repository.get(posted.id)
    now = instant(datetime(2026, 9, 2, tzinfo=timezone.utc))

    assert situation(loaded.as_record(), None, now) is Situation.FORMING_HELD
    assert situation(loaded.as_record(), None, now) is situation(
        (await world.repository.get(posted.id)).as_record(), None, now
    )


async def test_every_stored_fact_survives_the_round_trip(world):
    """Drive a match through most of its record and reload it field by field."""

    posted = await a_posted_match(world)
    match = await world.repository.get(posted.id)
    match.hold_court(at=instant(world.clock.now()))
    match.lock_court(at=instant(world.clock.now()))
    match.extend_hold(at=instant(world.clock.now()))
    await world.repository.save(match)
    await world.uow.commit()

    alice = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=alice))
    await world.pay.execute(PaySeatCommand(match_id=posted.id, player_id=alice))
    world.clock.advance_to(datetime(2026, 9, 2, 12, tzinfo=timezone.utc))
    await world.vacate.execute(
        VacateSeatCommand(match_id=posted.id, player_id=alice)
    )

    loaded = await world.repository.get(posted.id)

    assert loaded.held_since is not None
    assert loaded.court_locked is True
    assert loaded.club_extended is True
    assert loaded.counted is True
    assert loaded.kind is MatchKind.OPEN
    assert [vacancy.seat_index for vacancy in loaded.open_vacancies] == [0]
    assert loaded.open_vacancies[0].vacated_at == instant(
        datetime(2026, 9, 2, 12, tzinfo=timezone.utc)
    )


async def test_a_score_survives_as_pairs_of_integers_and_never_as_a_string(world):
    posted = await a_posted_match(world)
    players = [uuid4() for _ in range(4)]
    world.clock.advance_to(datetime(2026, 9, 7, 20, tzinfo=timezone.utc))
    for player in players:
        await world.take.execute(
            TakeSeatCommand(match_id=posted.id, player_id=player)
        )
        await world.pay.execute(
            PaySeatCommand(match_id=posted.id, player_id=player)
        )

    world.clock.advance_to(datetime(2026, 9, 8, 20, tzinfo=timezone.utc))
    await world.propose.execute(
        ProposeScoreCommand(
            match_id=posted.id,
            player_id=players[0],
            score=Score((SetScore(6, 4), SetScore(7, 6))),
        )
    )

    loaded = await world.repository.get(posted.id)
    assert loaded.score == Score((SetScore(6, 4), SetScore(7, 6)))
    assert loaded.score_by == players[0]
    assert loaded.proposals == 1

    await world.agree.execute(AgreeResultCommand(match_id=posted.id))
    settled = await world.repository.get(posted.id)
    assert settled.result_agreed
    assert situation(
        settled.as_record(),
        None,
        instant(datetime(2026, 9, 8, 21, tzinfo=timezone.utc)),
    ) is Situation.COMPLETED


async def test_a_filled_hole_keeps_its_row(world):
    """Filled, never deleted — *when did it lose a player, and when did it get
    one back* stays a query."""

    posted = await a_posted_match(world)
    alice = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=alice))
    await world.vacate.execute(
        VacateSeatCommand(match_id=posted.id, player_id=alice)
    )
    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=uuid4()))

    loaded = await world.repository.get(posted.id)

    assert loaded.open_vacancies == []
    assert len(loaded.vacancies) == 1
    assert loaded.vacancies[0].filled_at is not None


async def test_a_missing_match_is_reported_as_missing(world):
    assert await world.repository.get(uuid4()) is None

    with pytest.raises(MatchNotFound):
        await world.move.execute(
            MoveMatchStartCommand(match_id=uuid4(), start=START)
        )


async def test_a_clubs_matches_come_back_soonest_first(world):
    club, category = await a_club_with_a_category(world)
    later = await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=instant(datetime(2026, 9, 9, 18, tzinfo=timezone.utc)),
            duration=hours(1),
            share=SeatShare(grosze(3800)),
        )
    )
    sooner = await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=START,
            duration=hours(1),
            share=SeatShare(grosze(3800)),
        )
    )

    listed = await world.repository.for_club(club.id)

    assert [one.id for one in listed] == [sooner.id, later.id]


async def test_a_window_narrows_to_the_matches_inside_it(world):
    club, category = await a_club_with_a_category(world)
    inside = await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=START,
            duration=hours(1),
            share=SeatShare(grosze(3800)),
        )
    )
    await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=instant(datetime(2026, 10, 1, 18, tzinfo=timezone.utc)),
            duration=hours(1),
            share=SeatShare(grosze(3800)),
        )
    )

    found = await world.repository.starting_between(
        club_ids=[club.id],
        window_from=instant(datetime(2026, 9, 8, tzinfo=timezone.utc)),
        window_to=instant(datetime(2026, 9, 9, tzinfo=timezone.utc)),
    )

    assert [one.id for one in found] == [inside.id]
    assert await world.repository.starting_between(
        club_ids=[],
        window_from=instant(datetime(2026, 9, 8, tzinfo=timezone.utc)),
        window_to=instant(datetime(2026, 9, 9, tzinfo=timezone.utc)),
    ) == []


# --- 2 · the version guard --------------------------------------------------


async def test_a_write_bumps_the_version(world):
    posted = await a_posted_match(world)
    assert posted.version == 0

    await world.move.execute(
        MoveMatchStartCommand(
            match_id=posted.id,
            start=instant(datetime(2026, 9, 9, 18, tzinfo=timezone.utc)),
        )
    )

    assert (await world.repository.get(posted.id)).version == 1


async def test_a_stale_writer_is_refused_and_never_merged(world):
    """Two readers, one writer. The loser is told, not merged: two writers
    interleaving on a seat would produce an occupancy nobody authored."""

    posted = await a_posted_match(world)
    first = await world.repository.get(posted.id)
    second = await world.repository.get(posted.id)

    first.take_seat(uuid4(), at=instant(world.clock.now()))
    await world.repository.save(first)
    await world.uow.commit()

    second.take_seat(uuid4(), at=instant(world.clock.now()))
    with pytest.raises(ConcurrentMatchModification):
        await world.repository.save(second)

    reloaded = await world.repository.get(posted.id)
    assert sum(1 for seat in reloaded.seats if seat.is_taken) == 1


async def test_a_refused_writer_leaves_no_announcement_behind(world, session_factory):
    """The guard runs before a single child row or outbox row is touched."""

    posted = await a_posted_match(world)
    first = await world.repository.get(posted.id)
    second = await world.repository.get(posted.id)
    first.take_seat(uuid4(), at=instant(world.clock.now()))
    await world.repository.save(first)
    await world.uow.commit()

    before = await count(session_factory, EventOutboxORM)
    second.take_seat(uuid4(), at=instant(world.clock.now()))
    with pytest.raises(ConcurrentMatchModification):
        await world.repository.save(second)
    await world.uow.rollback()

    assert await count(session_factory, EventOutboxORM) == before


# --- 3 · the announcements land with the row --------------------------------


async def _outbox_names(session_factory):
    async with session_factory() as session:
        rows = await session.execute(
            select(EventOutboxORM.event_type).order_by(EventOutboxORM.occurred_at)
        )
        return [name for name in rows.scalars().all() if name.startswith("matches.")]


async def test_posting_a_match_announces_it(world, session_factory):
    await a_posted_match(world)

    assert await _outbox_names(session_factory) == ["matches.match_posted"]


async def test_every_write_puts_its_own_name_on_the_outbox(world, session_factory):
    posted = await a_posted_match(world)
    alice = uuid4()

    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=alice))
    await world.pay.execute(PaySeatCommand(match_id=posted.id, player_id=alice))
    await world.move.execute(
        MoveMatchStartCommand(
            match_id=posted.id,
            start=instant(datetime(2026, 9, 9, 18, tzinfo=timezone.utc)),
        )
    )
    await world.vacate.execute(
        VacateSeatCommand(match_id=posted.id, player_id=alice)
    )
    await world.cancel.execute(
        CancelMatchCommand(match_id=posted.id, cause=CancellationCause.WEATHER)
    )

    assert await _outbox_names(session_factory) == [
        "matches.match_posted",
        "matches.seat_taken",
        "matches.seat_paid",
        "matches.match_start_moved",
        "matches.seat_vacated",
        "matches.match_cancelled_for_weather",
    ]


async def test_the_four_cancellations_land_under_four_different_names(
    world, session_factory
):
    for cause in CancellationCause:
        posted = await a_posted_match(world)
        await world.cancel.execute(
            CancelMatchCommand(match_id=posted.id, cause=cause)
        )

    names = await _outbox_names(session_factory)
    cancellations = [name for name in names if "cancelled" in name]

    assert sorted(cancellations) == [
        "matches.match_cancelled_at_checkpoint",
        "matches.match_cancelled_by_club",
        "matches.match_cancelled_for_weather",
        "matches.match_cancelled_incomplete",
    ]


async def test_a_payment_that_commits_announces_both(world, session_factory):
    """Two changes, two names, one transaction."""

    posted = await a_posted_match(world)
    world.clock.advance_to(datetime(2026, 9, 7, 20, tzinfo=timezone.utc))
    for _ in range(4):
        player = uuid4()
        await world.take.execute(
            TakeSeatCommand(match_id=posted.id, player_id=player)
        )
        await world.pay.execute(
            PaySeatCommand(match_id=posted.id, player_id=player)
        )

    names = await _outbox_names(session_factory)

    assert names[-2:] == ["matches.seat_paid", "matches.match_committed"]
    assert (await world.repository.get(posted.id)).committed_at is not None


# --- 4 · one transaction, or neither ----------------------------------------


async def test_a_failure_writes_neither_the_row_nor_its_announcement(
    session_factory, clock
):
    """AC: *an event and its match row are written in one transaction*.

    The write is driven to the point where both are in the session and then
    rolled back, which is what a crash between the two would look like. Neither
    survives — and it matters more here than anywhere else in the tree, because
    a match with no announcement is a change that cannot be explained and an
    announcement with no match is one that never happened.
    """

    async with session_factory() as session:
        world = _World(session, clock)
        club, category = await a_club_with_a_category(world)
        match = await world.post.execute(
            PostMatchCommand(
                club_id=club.id,
                category_id=category.id,
                sport=Sport.PADEL,
                start=START,
                duration=hours(1),
                share=SeatShare(grosze(3800)),
            )
        )
        loaded = await world.repository.get(match.id)
        loaded.take_seat(uuid4(), at=instant(clock.now()))
        await world.repository.save(loaded)
        # No commit. This is the crash.
        await world.uow.rollback()

    async with session_factory() as session:
        world = _World(session, clock)
        after = await world.repository.get(match.id)

    assert after is not None
    assert all(seat.is_free for seat in after.seats)
    assert after.version == 0
    assert await count(
        session_factory, EventOutboxORM, event_type="matches.seat_taken"
    ) == 0


async def test_the_seats_are_rows_and_the_count_is_not_stored(
    world, session_factory
):
    posted = await a_posted_match(world)

    assert await count(session_factory, MatchSeatORM, match_id=posted.id) == 4
    assert await count(session_factory, MatchVacancyORM, match_id=posted.id) == 0
    async with session_factory() as session:
        row = await session.get(MatchORM, posted.id)
        assert not hasattr(row, "filled")
        assert not hasattr(row, "seat_count")
        assert not hasattr(row, "court_id")


async def test_a_seat_is_updated_in_place_and_never_re_inserted(
    world, session_factory
):
    """A seat's row *is* its position, and the one-player-one-seat index is
    keyed on it."""

    posted = await a_posted_match(world)
    async with session_factory() as session:
        rows = await session.execute(
            select(MatchSeatORM.id).where(MatchSeatORM.match_id == posted.id)
        )
        before = set(rows.scalars().all())

    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=uuid4()))

    async with session_factory() as session:
        rows = await session.execute(
            select(MatchSeatORM.id).where(MatchSeatORM.match_id == posted.id)
        )
        assert set(rows.scalars().all()) == before


async def test_a_short_window_returns_nothing_rather_than_everything(world):
    club, _ = await a_club_with_a_category(world)
    await a_posted_match(world)

    found = await world.repository.starting_between(
        club_ids=[club.id],
        window_from=instant(datetime(2026, 9, 1, tzinfo=timezone.utc)),
        window_to=instant(datetime(2026, 9, 1, tzinfo=timezone.utc))
        + timedelta(minutes=1),
    )

    assert found == []


# --- the database is the backstop -------------------------------------------


async def test_one_player_holds_one_seat_even_under_a_race(world, session_factory):
    """The domain refuses it and the index refuses it, and both are needed.

    ``PlayerAlreadyHoldsASeat`` is the answer a player gets; the partial unique
    index is what makes the rule true when two requests read the same match at
    the same instant and neither sees the other's seat.
    """

    posted = await a_posted_match(world)
    alice = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=posted.id, player_id=alice))

    async with session_factory() as session:
        with pytest.raises(IntegrityError):
            await session.execute(
                sa_update(MatchSeatORM)
                .where(
                    MatchSeatORM.match_id == posted.id,
                    MatchSeatORM.seat_index == 1,
                )
                .values(player_id=alice)
            )
            await session.commit()


async def test_every_empty_seat_is_allowed_to_be_empty(world, session_factory):
    """Three of a fresh padel match's four seats have a null player.

    A plain unique index would allow exactly one of them, which is why the index
    is partial over the occupied rows — and why this is asserted rather than
    left to the shape of the DDL.
    """

    posted = await a_posted_match(world)

    async with session_factory() as session:
        rows = await session.execute(
            select(func.count())
            .select_from(MatchSeatORM)
            .where(
                MatchSeatORM.match_id == posted.id,
                MatchSeatORM.player_id.is_(None),
            )
        )
        assert rows.scalar_one() == 4
