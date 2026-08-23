"""A club, through the use cases and back out of six tables.

Everything here runs against the ordinary SQLite fixture, which is deliberate and
is ADR-0077's own point: *"a club has exactly one open row per series, so the
constraint is a partial unique index, which both engines support — the guarantee
therefore holds in the fast tests as well as in production."* The three
partial unique indexes are declared for SQLite too, so a second open row is
refused here at millisecond cost. `tests/integration/test_club_series.py` asserts
the same shapes against a real PostgreSQL, for what SQLite cannot speak for.

Nothing in this file writes a table. Every state is reached by running the use
case a request would run, wired from the composition root, so a stored club has
the rows a real one has.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.bootstrap.composition import build_club_repository, build_unit_of_work
from app.infrastructure.clock import SystemClock
from app.kernel import (
    Cover,
    CardAllowance,
    CardCoversShare,
    NoCard,
    Sport,
    hours,
    minutes,
    percent,
    zloty,
)
from app.modules.clubs.application.add_court import AddCourt
from app.modules.clubs.application.add_court_category import AddCourtCategory
from app.modules.clubs.application.change_club_policy import ChangeClubPolicy
from app.modules.clubs.application.change_payout_destination import (
    ChangePayoutDestination,
)
from app.modules.clubs.application.commands import (
    AddCourtCategoryCommand,
    AddCourtCommand,
    ChangeClubPolicyCommand,
    ChangePayoutDestinationCommand,
    MoveCourtCommand,
    RegisterClubCommand,
    RetireCourtCategoryCommand,
    RetireCourtCommand,
)
from app.modules.clubs.application.get_club import GetClub, ListClubs
from app.modules.clubs.application.move_court import MoveCourt
from app.modules.clubs.application.register_club import RegisterClub
from app.modules.clubs.application.retire_court import RetireCourt
from app.modules.clubs.application.retire_court_category import RetireCourtCategory
from app.modules.clubs.domain.errors import (
    ClubNameAlreadyUsed,
    ClubNotFound,
    ConcurrentClubModification,
)
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    SYSTEM_ACTOR,
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)
from app.modules.clubs.infrastructure import (
    sqlalchemy_club_repository as club_repository_module,
)
from app.modules.clubs.infrastructure.sqlalchemy_club_models import (
    ClubCardOffsetORM,
    ClubCourtCatalogueORM,
    ClubCourtCategoryORM,
    ClubPayoutDestinationORM,
    ClubPolicyORM,
)

PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)
SECOND_PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL27114020040000300201355387"
)


def a_command(**overrides) -> RegisterClubCommand:
    defaults = dict(
        name=ClubName("Zabłocie Sport"),
        address=StreetAddress(
            line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
        ),
        point=GeoPoint(
            latitude=Decimal("50.048100"), longitude=Decimal("19.958500")
        ),
        timezone="Europe/Warsaw",
        policy=ClubPolicy(),
        payout=PAYOUT,
        pricing=ClubPricing(),
    )
    defaults.update(overrides)
    return RegisterClubCommand(**defaults)


class _Clubs:
    """Every Clubs use case over one session, wired from the composition root."""

    def __init__(self, session, clock):
        clubs = build_club_repository(session)
        uow = build_unit_of_work(session)
        self.repository = clubs
        self.uow = uow
        self.register = RegisterClub(clubs, uow, clock)
        self.change_policy = ChangeClubPolicy(clubs, uow, clock)
        self.change_payout = ChangePayoutDestination(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.retire_category = RetireCourtCategory(clubs, uow, clock)
        self.add_court = AddCourt(clubs, uow, clock)
        self.move_court = MoveCourt(clubs, uow, clock)
        self.retire_court = RetireCourt(clubs, uow, clock)
        self.get = GetClub(clubs)
        self.list = ListClubs(clubs)


@pytest.fixture
def clock():
    return SystemClock()


@pytest.fixture
async def clubs(session_factory, clock):
    async with session_factory() as session:
        yield _Clubs(session, clock)


async def count(session_factory, model, **where):
    async with session_factory() as session:
        statement = select(func.count()).select_from(model)
        for column, value in where.items():
            statement = statement.where(getattr(model, column) == value)
        return (await session.execute(statement)).scalar_one()


# --- the round trip ---------------------------------------------------------


async def test_a_registered_club_reads_back_whole(clubs):
    pricing = ClubPricing(
        price_multiplier=percent(90),
        slot_discount=percent(85),
        card_offsets={
            Sport.PADEL: CardAllowance(zloty(15)),
            Sport.TENNIS: CardCoversShare(),
        },
    )
    created = await clubs.register.execute(
        a_command(
            pricing=pricing,
            policy=ClubPolicy(
                window=hours(6),
                join_cut=minutes(45),
                max_hold_age=minutes(0),
                prob_hold=True,
                rebooking_credit=True,
                free_cancel_hours=12,
                turnaround_min=minutes(15),
                counts_cash=False,
            ),
        )
    )

    club = await clubs.get.execute(created.id)

    assert club.name == ClubName("Zabłocie Sport")
    assert club.address.city == "Kraków"
    assert club.point == GeoPoint(
        latitude=Decimal("50.048100"), longitude=Decimal("19.958500")
    )
    assert str(club.timezone) == "Europe/Warsaw"
    assert club.pricing.price_multiplier == percent(90)
    assert club.pricing.slot_discount == percent(85)
    assert club.pricing.card_for(Sport.PADEL) == CardAllowance(zloty(15))
    assert club.pricing.card_for(Sport.TENNIS) == CardCoversShare()
    assert club.pricing.card_for(Sport.SQUASH) == NoCard()
    assert club.payout_now == PAYOUT


async def test_all_eight_policy_fields_survive_the_round_trip(clubs):
    """Including the two with no reader. Dark is not absent."""

    policy = ClubPolicy(
        window=hours(6),
        join_cut=minutes(45),
        max_hold_age=minutes(0),
        prob_hold=True,
        rebooking_credit=True,
        free_cancel_hours=12,
        turnaround_min=minutes(15),
        counts_cash=False,
    )
    created = await clubs.register.execute(a_command(policy=policy))

    club = await clubs.get.execute(created.id)

    assert club.policy_now == policy


async def test_none_and_zero_hold_caps_are_told_apart_by_the_store(clubs):
    """NULL is *never stale*; 0 is *this club does not hold speculatively*. A
    column that collapsed them would be a platform floor by accident."""

    never_stale = await clubs.register.execute(
        a_command(name=ClubName("Never stale"), policy=ClubPolicy(max_hold_age=None))
    )
    never_holds = await clubs.register.execute(
        a_command(
            name=ClubName("Never holds"),
            policy=ClubPolicy(max_hold_age=minutes(0)),
        )
    )

    assert (await clubs.get.execute(never_stale.id)).policy_now.max_hold_age is None
    assert (await clubs.get.execute(never_holds.id)).policy_now.max_hold_age == 0
    assert (
        await clubs.get.execute(never_holds.id)
    ).policy_now.holds_speculatively is False


async def test_registering_the_same_name_twice_is_refused(clubs):
    await clubs.register.execute(a_command())

    with pytest.raises(ClubNameAlreadyUsed):
        await clubs.register.execute(a_command())


async def test_an_unknown_club_is_a_refusal(clubs):
    with pytest.raises(ClubNotFound):
        await clubs.get.execute(uuid.uuid4())


# --- the series, on disk ----------------------------------------------------


async def test_a_policy_change_closes_one_row_and_opens_another(
    clubs, session_factory
):
    created = await clubs.register.execute(
        a_command(policy=ClubPolicy(max_hold_age=hours(48)))
    )

    await clubs.change_policy.execute(
        ChangeClubPolicyCommand(
            club_id=created.id, policy=ClubPolicy(max_hold_age=hours(6))
        )
    )

    assert await count(session_factory, ClubPolicyORM, club_id=created.id) == 2
    assert (
        await count(
            session_factory, ClubPolicyORM, club_id=created.id, valid_to=None
        )
        == 1
    )
    club = await clubs.get.execute(created.id)
    assert club.policy_now.max_hold_age == hours(6)
    assert club.policy.versions[0].value.max_hold_age == hours(48)
    assert club.policy.versions[0].valid_to is not None


async def test_four_policy_changes_leave_four_closed_rows_and_one_open(
    clubs, session_factory
):
    created = await clubs.register.execute(a_command())

    for cap in (hours(48), hours(24), hours(6), minutes(0)):
        await clubs.change_policy.execute(
            ChangeClubPolicyCommand(
                club_id=created.id, policy=ClubPolicy(max_hold_age=cap)
            )
        )

    assert await count(session_factory, ClubPolicyORM, club_id=created.id) == 5
    assert (
        await count(
            session_factory, ClubPolicyORM, club_id=created.id, valid_to=None
        )
        == 1
    )
    club = await clubs.get.execute(created.id)
    assert [v.value.max_hold_age for v in club.policy] == [
        None,
        hours(48),
        hours(24),
        hours(6),
        minutes(0),
    ]


async def test_the_three_series_are_independent_on_disk(clubs, session_factory):
    created = await clubs.register.execute(a_command())

    await clubs.change_policy.execute(
        ChangeClubPolicyCommand(
            club_id=created.id, policy=ClubPolicy(max_hold_age=hours(6))
        )
    )

    assert await count(session_factory, ClubPolicyORM, club_id=created.id) == 2
    assert (
        await count(session_factory, ClubPayoutDestinationORM, club_id=created.id) == 1
    )

    await clubs.change_payout.execute(
        ChangePayoutDestinationCommand(
            club_id=created.id, destination=SECOND_PAYOUT
        )
    )

    assert (
        await count(session_factory, ClubPayoutDestinationORM, club_id=created.id) == 2
    )
    assert await count(session_factory, ClubPolicyORM, club_id=created.id) == 2

    club = await clubs.get.execute(created.id)
    assert club.payout_now == SECOND_PAYOUT
    assert club.payout.versions[0].value == PAYOUT


async def test_every_versioned_row_carries_an_actor_and_it_reads_system(
    clubs, session_factory
):
    created = await clubs.register.execute(a_command())
    await clubs.change_policy.execute(
        ChangeClubPolicyCommand(club_id=created.id, policy=ClubPolicy())
    )
    await clubs.change_payout.execute(
        ChangePayoutDestinationCommand(club_id=created.id, destination=SECOND_PAYOUT)
    )
    category = await clubs.add_category.execute(
        AddCourtCategoryCommand(
            club_id=created.id,
            name=CategoryName("Padel · Mondo, indoor"),
            sport=Sport.PADEL,
            cover=Cover.INDOOR,
            rate=zloty(120),
        )
    )
    await clubs.add_court.execute(
        AddCourtCommand(
            club_id=created.id,
            category_id=category.id,
            label=CourtLabel("Court 1"),
        )
    )

    async with session_factory() as session:
        actors = set()
        for model in (
            ClubPolicyORM,
            ClubPayoutDestinationORM,
            ClubCourtCatalogueORM,
        ):
            rows = (await session.execute(select(model.changed_by))).scalars().all()
            assert rows, f"{model.__tablename__} has no rows to check"
            actors.update(rows)
    assert actors == {SYSTEM_ACTOR}


# --- the partial unique index, on SQLite ------------------------------------


async def test_a_second_open_policy_row_is_refused_by_the_database(
    clubs, session_factory
):
    """The index, not the code. This is what ADR-0077 keeps beside the version:
    the version stops a race, the index stops the invariant violation.
    """

    created = await clubs.register.execute(a_command())

    async with session_factory() as session:
        session.add(
            ClubPolicyORM(
                id=uuid.uuid4(),
                club_id=created.id,
                window_minutes=1440,
                join_cut_minutes=30,
                max_hold_age_minutes=None,
                prob_hold=False,
                rebooking_credit=False,
                free_cancel_hours=None,
                turnaround_minutes=0,
                counts_cash=True,
                valid_from=datetime.now(timezone.utc),
                valid_to=None,
                changed_by=SYSTEM_ACTOR,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()


# --- the court catalogue ----------------------------------------------------


async def a_padel_club(clubs):
    created = await clubs.register.execute(a_command())
    mondo = await clubs.add_category.execute(
        AddCourtCategoryCommand(
            club_id=created.id,
            name=CategoryName("Padel · Mondo, indoor"),
            sport=Sport.PADEL,
            cover=Cover.INDOOR,
            rate=zloty(120),
        )
    )
    wall = await clubs.add_category.execute(
        AddCourtCategoryCommand(
            club_id=created.id,
            name=CategoryName("Padel · Wall, outdoor"),
            sport=Sport.PADEL,
            cover=Cover.OUTDOOR,
            rate=zloty(108),
        )
    )
    courts = [
        await clubs.add_court.execute(
            AddCourtCommand(
                club_id=created.id, category_id=category, label=CourtLabel(label)
            )
        )
        for category, label in (
            (mondo.id, "Court 1"),
            (mondo.id, "Court 2"),
            (wall.id, "Court 3"),
        )
    ]
    return created.id, mondo, wall, courts


async def test_the_catalogue_reads_back_with_its_categories_and_courts(clubs):
    club_id, mondo, wall, _ = await a_padel_club(clubs)

    club = await clubs.get.execute(club_id)

    assert {c.name.value for c in club.live_categories} == {
        "Padel · Mondo, indoor",
        "Padel · Wall, outdoor",
    }
    assert club.category(mondo.id).rate == zloty(120)
    assert club.category(wall.id).rate == zloty(108)
    assert len(club.courts_in(mondo.id)) == 2
    assert {c.label.value for c in club.live_courts} == {
        "Court 1",
        "Court 2",
        "Court 3",
    }


async def test_a_category_reads_back_under_the_roof_it_was_authored_with(clubs):
    """ADR-0090's whole point: the fact is stored, not spelled in a name.

    Two categories at one club, one of each cover, so a store that wrote a
    constant — or that read every row back as the first one it saw — is red
    rather than accidentally right about a single-valued fixture.
    """

    club_id, mondo, wall, _ = await a_padel_club(clubs)

    club = await clubs.get.execute(club_id)

    assert club.category(mondo.id).cover is Cover.INDOOR
    assert club.category(wall.id).cover is Cover.OUTDOOR


async def test_the_stored_cover_is_the_authored_one_and_never_read_off_the_name(
    clubs,
):
    """The name and the fact are allowed to disagree, and the fact wins.

    A club may call a category anything (ADR-0079), so a store that fell back to
    parsing the name would be right about every category in the seeds and wrong
    about the first one a real club authors. Named to say the opposite of what
    it is, which is the only way to tell the two readings apart.
    """

    created = await clubs.register.execute(a_command())
    misleading = await clubs.add_category.execute(
        AddCourtCategoryCommand(
            club_id=created.id,
            name=CategoryName("Padel · indoor"),
            sport=Sport.PADEL,
            cover=Cover.OUTDOOR,
            rate=zloty(120),
        )
    )

    club = await clubs.get.execute(created.id)

    assert club.category(misleading.id).cover is Cover.OUTDOOR


async def test_a_cover_cannot_be_changed_by_saving_the_club_again(
    clubs, session_factory
):
    """ADR-0090: the cover never changes; a court that gains a roof **moves**.

    `_update_categories` writes a category's name, rate and retirement in place
    and deliberately writes neither of the two facts the platform constrains. So
    a category mutated in memory and saved comes back as it was authored — which
    is what makes *the club roofed Court 3* impossible to spell as *every court
    in this category has always had a roof*.

    Reached through the aggregate's own field rather than through an operation,
    because there is no operation: this asserts that adding one to the writer
    without adding one to the model is not enough.
    """

    club_id, mondo, _, _ = await a_padel_club(clubs)

    club = await clubs.repository.get(club_id)
    assert club is not None
    club.category(mondo.id).cover = Cover.OUTDOOR
    club.reprice_category(mondo.id, zloty(130))
    await clubs.repository.save(club)
    await clubs.uow.commit()

    reread = await clubs.get.execute(club_id)
    assert reread.category(mondo.id).rate == zloty(130)
    assert reread.category(mondo.id).cover is Cover.INDOOR


async def test_a_retired_court_keeps_its_history_and_leaves_the_live_set(
    clubs, session_factory
):
    club_id, mondo, _, courts = await a_padel_club(clubs)

    await clubs.retire_court.execute(
        RetireCourtCommand(club_id=club_id, court_id=courts[0].id)
    )

    club = await clubs.get.execute(club_id)
    retired = club.court(courts[0].id)
    assert retired.is_retired
    assert retired.catalogue.versions[0].value.label == CourtLabel("Court 1")
    assert len(club.live_courts) == 2
    assert await count(session_factory, ClubCourtCatalogueORM, club_id=club_id) == 3


async def test_moving_a_court_writes_a_second_catalogue_row(clubs, session_factory):
    club_id, mondo, wall, courts = await a_padel_club(clubs)

    await clubs.move_court.execute(
        MoveCourtCommand(
            club_id=club_id, court_id=courts[2].id, category_id=mondo.id
        )
    )

    assert await count(session_factory, ClubCourtCatalogueORM, club_id=club_id) == 4
    assert (
        await count(
            session_factory, ClubCourtCatalogueORM, club_id=club_id, valid_to=None
        )
        == 3
    )
    club = await clubs.get.execute(club_id)
    court = club.court(courts[2].id)
    assert court.category_id == mondo.id
    assert court.catalogue.versions[0].value.category_id == wall.id
    assert len(club.courts_in(mondo.id)) == 3


async def test_retiring_a_category_retires_its_courts_and_keeps_the_row(
    clubs, session_factory
):
    club_id, mondo, _, _ = await a_padel_club(clubs)

    await clubs.retire_category.execute(
        RetireCourtCategoryCommand(club_id=club_id, category_id=mondo.id)
    )

    assert await count(session_factory, ClubCourtCategoryORM, club_id=club_id) == 2
    club = await clubs.get.execute(club_id)
    assert club.category(mondo.id).is_retired
    assert club.courts_in(mondo.id) == ()
    assert len(club.live_courts) == 1


async def test_the_card_offsets_are_rewritten_rather_than_versioned(
    clubs, session_factory
):
    created = await clubs.register.execute(
        a_command(
            pricing=ClubPricing(card_offsets={Sport.PADEL: CardAllowance(zloty(15))})
        )
    )

    assert await count(session_factory, ClubCardOffsetORM, club_id=created.id) == 1

    club = await clubs.get.execute(created.id)
    club.reprice(ClubPricing(card_offsets={Sport.TENNIS: CardCoversShare()}))
    await clubs.repository.save(club)
    await clubs.uow.commit()

    assert await count(session_factory, ClubCardOffsetORM, club_id=created.id) == 1
    reloaded = await clubs.get.execute(created.id)
    assert reloaded.pricing.card_for(Sport.PADEL) == NoCard()
    assert reloaded.pricing.card_for(Sport.TENNIS) == CardCoversShare()


# --- the version ------------------------------------------------------------


async def test_the_version_moves_on_every_save(clubs):
    created = await clubs.register.execute(a_command())
    assert created.version == 0

    await clubs.change_policy.execute(
        ChangeClubPolicyCommand(club_id=created.id, policy=ClubPolicy())
    )

    assert (await clubs.get.execute(created.id)).version == 1


async def test_a_stale_writer_is_refused_and_never_merged(clubs):
    """Two readers, one writer. The loser is told, not merged: two writers
    interleaving on a policy row would produce a version nobody authored."""

    created = await clubs.register.execute(a_command())
    first = await clubs.get.execute(created.id)
    second = await clubs.get.execute(created.id)

    first.rename(ClubName("Renamed once"))
    await clubs.repository.save(first)
    await clubs.uow.commit()

    second.rename(ClubName("Renamed twice"))
    with pytest.raises(ConcurrentClubModification):
        await clubs.repository.save(second)

    assert (await clubs.get.execute(created.id)).name.value == "Renamed once"


async def test_listing_clubs_returns_each_one_whole(clubs):
    await clubs.register.execute(a_command())
    await clubs.register.execute(a_command(name=ClubName("Kortowo")))

    listed = await clubs.list.execute()

    assert [club.name.value for club in listed] == ["Kortowo", "Zabłocie Sport"]
    assert all(club.policy_now is not None for club in listed)


# --- rebuilding a series in the order it was written ------------------------


class _FrozenClock:
    """One instant, handed out however many times it is asked for.

    The point is not convenience: it is the only way to reach *two changes at one
    clock reading* deliberately. `SystemClock` has microsecond resolution, so the
    rest of this file never produces the state below by accident — which is
    exactly why it went unnoticed.
    """

    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


def _descending_uuids(monkeypatch) -> None:
    """Mint the series' row ids counting **down**, so every later row sorts first.

    `new_uuid` is `uuid4`, so which of two rows sharing an instant came back first
    was a coin flip decided when they were written. Replacing it with a descending
    counter picks the losing side of that flip every time, which turns a test that
    would fail half the runs into one that fails all of them.

    Patched in the repository's own namespace because that is where the name is
    bound — `from app.shared.ids import new_uuid` copies the reference, so
    patching `app.shared.ids` would change nothing here.
    """

    remaining = iter(range(2**32, 0, -1))
    monkeypatch.setattr(
        club_repository_module,
        "new_uuid",
        lambda: uuid.UUID(int=next(remaining)),
    )


@pytest.fixture
async def frozen_clubs(session_factory, monkeypatch):
    _descending_uuids(monkeypatch)
    async with session_factory() as session:
        yield _Clubs(
            session,
            _FrozenClock(datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)),
        )


async def test_two_changes_at_one_instant_reload_in_the_order_they_were_written(
    frozen_clubs, session_factory
):
    """A version that was never in force must not make the club a coin flip.

    Two changes at one clock reading close a row at the instant it opened, so two
    rows of one series share a `valid_from` — and the ORDER BY that rebuilds the
    series has to break that tie. It broke it on `id`, and `new_uuid` is `uuid4`:
    half the draws put the **open** row first, which `Series` refuses to hold,
    because an open row is the last one by definition. The club loaded, or did
    not, depending on a random number chosen when it was written — and the
    failure reads as a broken database rather than as an ambiguous ordering.
    Measured at 29 failures in 60 real draws before `_series_order` existed.

    Read back through a **new session**, so this is a re-read from the tables
    rather than the identity map handing back the object that was just saved.
    """

    created = await frozen_clubs.register.execute(
        a_command(policy=ClubPolicy(max_hold_age=hours(48)))
    )
    await frozen_clubs.change_policy.execute(
        ChangeClubPolicyCommand(
            club_id=created.id, policy=ClubPolicy(max_hold_age=hours(6))
        )
    )

    async with session_factory() as session:
        club = await GetClub(build_club_repository(session)).execute(created.id)

    assert [version.value.max_hold_age for version in club.policy.versions] == [
        hours(48),
        hours(6),
    ]
    assert club.policy_now.max_hold_age == hours(6)
    assert club.policy.versions[0].valid_to == club.policy.versions[1].valid_from


async def test_the_same_holds_for_the_payout_and_catalogue_series(
    frozen_clubs, session_factory
):
    """One ordering serves all three series, so all three are asserted.

    A tie-break correct for policies and wrong for the catalogue would be the
    same bug with a smaller blast radius, and nothing else in this file would
    notice: a court whose two rows came back the wrong way round is a court that
    reads as retired while its category still sells it.
    """

    created = await frozen_clubs.register.execute(a_command())
    await frozen_clubs.change_payout.execute(
        ChangePayoutDestinationCommand(club_id=created.id, destination=SECOND_PAYOUT)
    )
    category = await frozen_clubs.add_category.execute(
        AddCourtCategoryCommand(
            club_id=created.id,
            name=CategoryName("Padel · indoor"),
            sport=Sport.PADEL,
            cover=Cover.INDOOR,
            rate=zloty(120),
        )
    )
    court = await frozen_clubs.add_court.execute(
        AddCourtCommand(
            club_id=created.id, category_id=category.id, label=CourtLabel("Court 1")
        )
    )
    await frozen_clubs.move_court.execute(
        MoveCourtCommand(
            club_id=created.id,
            court_id=court.id,
            category_id=category.id,
            label=CourtLabel("Court 1A"),
        )
    )

    async with session_factory() as session:
        club = await GetClub(build_club_repository(session)).execute(created.id)

    assert [version.value for version in club.payout.versions] == [
        PAYOUT,
        SECOND_PAYOUT,
    ]
    assert club.payout_now == SECOND_PAYOUT

    stored_court = club.court(court.id)
    assert [
        version.value.label.value for version in stored_court.catalogue.versions
    ] == ["Court 1", "Court 1A"]
    assert stored_court.is_retired is False
    assert stored_court.label == CourtLabel("Court 1A")
