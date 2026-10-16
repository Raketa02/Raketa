"""Ogrody 33's desk setting its club up to sell through Raketa — the few moves
every test of courts, hours, exceptions, prices and settings makes (#535, the
mechanics §16, the screens B2–B5).

**Every assertion reads what the desk reads**: an answer on the club surface.
The one read with no route — the sellable court hours other contexts are
published — is asked through the port, as they will ask it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.kernel import instant
from app.modules.clubs.domain.ports import TakenCourtHour
from app.modules.clubs.presentation.dependencies import get_court_bookings
from app.modules.payments.presentation.dependencies import get_payment_provider
from tests.api.administration_world import club_signs_up

COURTS = "/api/v1/club/courts"
RAKETA_HOURS = "/api/v1/club/raketa-hours"
EXCEPTIONS = "/api/v1/club/exceptions"
PRICES = "/api/v1/club/prices"
RAKETA_SETTINGS = "/api/v1/club/raketa-settings"
SETUP = "/api/v1/club/setup"
PAYMENTS_LINK = "/api/v1/club/payments/onboarding-link"


def court_path(court_id: str) -> str:
    return f"{COURTS}/{court_id}"


def exception_path(exception_id: str) -> str:
    return f"{EXCEPTIONS}/{exception_id}"


async def a_desk(client, **kwargs) -> tuple[str, dict]:
    """A club signed up — tennis and padel unless told otherwise — and its
    desk's club-audience session."""

    return await club_signs_up(client, **kwargs)


async def adds_a_court(
    client, desk: dict, *, name: str, sport: str = "PADEL", indoor: bool = True
) -> dict:
    added = await client.post(
        COURTS, json={"name": name, "sport": sport, "indoor": indoor}, headers=desk
    )
    assert added.status_code == 201, added.text
    return added.json()


async def sets_hours(client, desk: dict, court_ids: list[str], cells) -> dict:
    saved = await client.put(
        RAKETA_HOURS,
        json={
            "court_ids": court_ids,
            "hours": [{"day": day, "hour": hour} for day, hour in cells],
        },
        headers=desk,
    )
    assert saved.status_code == 200, saved.text
    return saved.json()


async def sets_prices(client, desk: dict, prices: list[dict]) -> dict:
    saved = await client.put(PRICES, json={"prices": prices}, headers=desk)
    assert saved.status_code == 200, saved.text
    return saved.json()


def settings(**overrides) -> dict:
    """The settings form as the desk leaves it untouched: every default."""

    return {
        "release_lead_days": 3,
        "cut_off_hours": 24,
        "other_clubs_courts": {"offered": False, "within_km": 10},
        "paused": False,
        **overrides,
    }


async def confirms_settings(client, desk: dict, **overrides) -> dict:
    saved = await client.put(RAKETA_SETTINGS, json=settings(**overrides), headers=desk)
    assert saved.status_code == 200, saved.text
    return saved.json()


async def connects_payments(client, desk: dict) -> None:
    """The desk connects Stripe and finishes its pages in one visit — the
    checklist's first step, done (#537).

    The provider is the application's own fake, told to finish onboarding the
    moment the link is made, as a laptop's does: the read that follows every
    link then finds the account ready."""

    payments = client._transport.app.dependency_overrides[get_payment_provider]()  # noqa: SLF001
    finishing, payments.onboarding_completes = payments.onboarding_completes, True
    try:
        linked = await client.post(PAYMENTS_LINK, headers=desk)
    finally:
        payments.onboarding_completes = finishing
    assert linked.status_code == 200, linked.text


@dataclass
class BookedCourts:
    """``CourtBookings`` stood in for: the court hours a test says are booked,
    answered as the port answers them — so a club's refusals are asserted
    without filling a game (that is ``test_the_fill.py``'s, #541).

    Installed on the running application, so a refusal is asserted over HTTP
    exactly as the desk meets it."""

    taken_hours: list[TakenCourtHour] = field(default_factory=list)

    def book(self, court_id: str, at: datetime) -> str:
        booking_id = uuid4()
        self.taken_hours.append(
            TakenCourtHour(
                court_id=UUID(court_id), start=instant(at), booking_id=booking_id
            )
        )
        return str(booking_id)

    async def taken(self, club_id, *, start, end=None):
        return [
            hour
            for hour in self.taken_hours
            if hour.start >= start and (end is None or hour.start < end)
        ]


def with_bookings(app) -> BookedCourts:
    booked = BookedCourts()
    app.dependency_overrides[get_court_bookings] = lambda: booked
    return booked
