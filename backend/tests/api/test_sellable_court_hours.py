"""The court hours a club can sell through Raketa — **derived, never stored**:
its weekly pattern, less its exceptions, less what bookings hold (#535,
``docs/adr/0189`` §5, the mechanics §5.4 and §16).

What a desk sets is written over HTTP, as the club website writes it; what the
club can sell is read through ``SellableCourtHours``, the port the proposer and
posting will read it through, built by the composition root over the same
database. Nothing reads it over HTTP.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**, so every hour
below is a literal the calendar can check: the sixth is a Tuesday, the tenth a
Saturday.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.api.dependencies import get_clock
from app.bootstrap.composition import (
    build_club_courts_repository,
    build_domain_event_store,
    build_event_publisher,
    build_sellable_court_hours,
)
from app.kernel import Sport, instant
from app.modules.clubs.domain.raketa_terms import WayOfWorking
from app.modules.clubs.infrastructure.club_courts_sellable_hours import (
    ClubCourtsSellableHours,
)
from tests.api.club_courts_world import (
    EXCEPTIONS,
    BookedCourts,
    a_desk,
    adds_a_court,
    chooses,
    PAYMENTS_LINK,
    confirms_settings,
    connects_payments,
    court_path,
    sets_hours,
    sets_prices,
)
from tests.unit.fake_clock import MovableClock

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int, month: int = 10) -> datetime:
    """An hour in Kraków in 2026, as the instant the port answers in."""

    return instant(datetime(2026, month, day, hour, tzinfo=WARSAW))


MONDAY_MORNING = warsaw(5, 8)


@pytest.fixture
def clock(app):
    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


def padel_prices() -> list[dict]:
    """120 zł, and 140 zł on weekday evenings: 30 zł and 35 zł each."""

    return [
        {
            "sport": "PADEL",
            "price_grosze": 120_00,
            "bands": [
                {
                    "days": "WEEKDAYS",
                    "from_hour": 17,
                    "until_hour": 22,
                    "price_grosze": 140_00,
                }
            ],
        }
    ]


async def a_live_club(
    client, *, way: str = "INSTANT", name: str = "Bonarka Arena", **settings
) -> tuple[str, dict, dict]:
    """A club selling one padel court on Tuesday 18:00–20:00 and Saturday 09:00
    — its id, its desk, and the court."""

    club_id, desk = await a_desk(
        client, name=name, email=f"desk@{name.split()[0].lower()}.pl", sports=("PADEL",)
    )
    await chooses(client, desk, way)
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(2, 18), (2, 19), (6, 9)])
    await sets_prices(client, desk, padel_prices())
    await confirms_settings(client, desk, **settings)
    await connects_payments(client, desk)
    return club_id, desk, court


async def sellable(session_factory, club_ids, *, days: int = 14, now=MONDAY_MORNING):
    async with session_factory() as session:
        return await build_sellable_court_hours(session).between(
            [UUID(club_id) for club_id in club_ids],
            start=now,
            end=now + timedelta(days=days),
            now=now,
        )


def starts_and_prices(offer) -> list[tuple[datetime, int, int]]:
    return [(hour.start, hour.price_grosze, hour.share_grosze) for hour in offer.hours]


async def test_a_live_club_sells_its_pattern_for_the_fortnight_priced_by_the_hour(
    client, clock, session_factory
):
    club_id, _, court = await a_live_club(client)

    offers = await sellable(session_factory, [club_id])

    offer = offers[UUID(club_id)]
    assert offer.way is WayOfWorking.INSTANT
    assert offer.taking_new_cards is True
    assert starts_and_prices(offer) == [
        (warsaw(6, 18), 140_00, 35_00),
        (warsaw(6, 19), 140_00, 35_00),
        (warsaw(10, 9), 120_00, 30_00),
        (warsaw(13, 18), 140_00, 35_00),
        (warsaw(13, 19), 140_00, 35_00),
        (warsaw(17, 9), 120_00, 30_00),
    ]
    first = offer.hours[0]
    assert (first.court_id, first.court_name, first.sport, first.indoor) == (
        UUID(court["id"]),
        "Court 1",
        Sport.PADEL,
        True,
    )
    # Instant: the start less the minimum notice, two hours by default.
    assert first.book_by == warsaw(6, 16)


async def test_the_hours_are_by_start_then_by_the_club_s_order_of_courts(
    client, clock, session_factory
):
    club_id, desk, one = await a_live_club(client)
    two = await adds_a_court(client, desk, name="Court 2")
    await sets_hours(client, desk, [two["id"]], [(2, 18)])

    offer = (await sellable(session_factory, [club_id], days=2))[UUID(club_id)]

    assert [(hour.start, hour.court_name) for hour in offer.hours] == [
        (warsaw(6, 18), "Court 1"),
        (warsaw(6, 18), "Court 2"),
        (warsaw(6, 19), "Court 1"),
    ]


async def test_an_exception_closes_what_it_covers_and_nothing_else(
    client, clock, session_factory
):
    club_id, desk, court = await a_live_club(client)
    for body in (
        {
            "court_ids": None,
            "first_day": "2026-10-10",
            "last_day": "2026-10-10",
            "from_hour": None,
            "until_hour": None,
            "reason": "Tournament",
        },
        {
            "court_ids": [court["id"]],
            "first_day": "2026-10-13",
            "last_day": "2026-10-13",
            "from_hour": 19,
            "until_hour": 20,
            "reason": "Repair",
        },
    ):
        assert (
            await client.post(EXCEPTIONS, json=body, headers=desk)
        ).status_code == 201

    offer = (await sellable(session_factory, [club_id]))[UUID(club_id)]

    assert [hour.start for hour in offer.hours] == [
        warsaw(6, 18),
        warsaw(6, 19),
        warsaw(13, 18),
        warsaw(17, 9),
    ]


async def test_an_hour_a_booking_holds_is_not_sold_again(
    client, clock, session_factory
):
    club_id, _, court = await a_live_club(client)
    booked = BookedCourts()
    booked.book(court["id"], warsaw(6, 19))

    async with session_factory() as session:
        offers = await ClubCourtsSellableHours(
            courts=build_club_courts_repository(
                session,
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ),
            bookings=booked,
        ).between(
            [UUID(club_id)],
            start=MONDAY_MORNING,
            end=MONDAY_MORNING + timedelta(days=2),
            now=MONDAY_MORNING,
        )

    assert [hour.start for hour in offers[UUID(club_id)].hours] == [warsaw(6, 18)]


async def test_an_hour_past_its_book_by_is_no_longer_sold(
    client, clock, session_factory
):
    club_id, _, _ = await a_live_club(client, minimum_notice_hours=3)

    # Tuesday 15:30: 18:00 is inside the three hours' notice, 19:00 is not.
    offer = (
        await sellable(
            session_factory, [club_id], now=warsaw(6, 15) + timedelta(minutes=30)
        )
    )[UUID(club_id)]

    assert offer.hours[0].start == warsaw(6, 19)
    assert offer.hours[0].book_by == warsaw(6, 16)


async def test_an_only_raketa_club_sells_until_its_release_lead(
    client, clock, session_factory
):
    """Unsold hours go back to the club the release lead before the game:
    three days by default, so Tuesday's hours are already the club's."""

    club_id, _, _ = await a_live_club(client, way="ONLY_RAKETA")

    offer = (await sellable(session_factory, [club_id]))[UUID(club_id)]

    assert offer.way is WayOfWorking.ONLY_RAKETA
    assert [hour.start for hour in offer.hours] == [
        warsaw(10, 9),
        warsaw(13, 18),
        warsaw(13, 19),
        warsaw(17, 9),
    ]
    assert offer.hours[0].book_by == warsaw(7, 9)


async def test_a_switched_off_court_sells_nothing(client, clock, session_factory):
    club_id, desk, one = await a_live_club(client)
    two = await adds_a_court(client, desk, name="Court 2")
    await sets_hours(client, desk, [two["id"]], [(2, 18)])
    await client.put(
        court_path(two["id"]),
        json={"name": "Court 2", "sport": "PADEL", "indoor": True, "offered": False},
        headers=desk,
    )

    offer = (await sellable(session_factory, [club_id], days=2))[UUID(club_id)]

    assert {hour.court_name for hour in offer.hours} == {"Court 1"}


async def test_a_paused_club_still_sells_what_its_cards_need_and_deals_nothing_new(
    client, clock, session_factory
):
    """A paused club's cards keep their court until their book-by and can still
    book (the mechanics §16.15), so its hours stay derivable; it takes no new
    cards."""

    club_id, _, _ = await a_live_club(client, paused=True)

    offer = (await sellable(session_factory, [club_id]))[UUID(club_id)]

    assert offer.taking_new_cards is False
    assert len(offer.hours) == 6


async def test_a_club_that_is_not_live_sells_nothing_and_is_absent(
    client, clock, session_factory
):
    live_id, _, _ = await a_live_club(client)
    half_id, desk = await a_desk(
        client, name="Wisła Park", email="desk@wisla.pl", sports=("TENNIS",)
    )
    court = await adds_a_court(client, desk, name="Court 1", sport="TENNIS")
    await sets_hours(client, desk, [court["id"]], [(2, 18)])

    offers = await sellable(session_factory, [half_id, live_id, str(uuid4())])

    assert list(offers) == [UUID(live_id)]


async def test_a_club_whose_payments_are_not_ready_sells_nothing(
    client, clock, session_factory, payments
):
    """**The club is the seller** (#537): four steps done and an account the
    provider does not yet call ready is a club that cannot take a share, so
    none of its hours is for sale."""

    club_id, desk = await a_desk(client, sports=("PADEL",))
    await chooses(client, desk, "INSTANT")
    court = await adds_a_court(client, desk, name="Court 1")
    await sets_hours(client, desk, [court["id"]], [(2, 18)])
    await sets_prices(client, desk, padel_prices())
    await confirms_settings(client, desk)
    linked = await client.post(PAYMENTS_LINK, headers=desk)
    assert linked.status_code == 200, linked.text

    assert await sellable(session_factory, [club_id]) == {}


async def test_a_club_s_hours_are_its_wall_clock_across_the_autumn_change(
    client, clock, session_factory
):
    """Clocks go back in the small hours of Sunday 25 October. Saturday 09:00 is
    07:00 UTC before it and Saturday 31st's 09:00 is 08:00 UTC after it."""

    club_id, _, _ = await a_live_club(client)

    offer = (await sellable(session_factory, [club_id], now=warsaw(22, 8), days=10))[
        UUID(club_id)
    ]

    saturdays = [
        hour.start
        for hour in offer.hours
        if hour.start.astimezone(WARSAW).isoweekday() == 6
    ]
    assert saturdays == [
        datetime(2026, 10, 24, 7, tzinfo=timezone.utc),
        datetime(2026, 10, 31, 8, tzinfo=timezone.utc),
    ]
