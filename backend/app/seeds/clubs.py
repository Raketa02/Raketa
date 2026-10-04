"""The clubs: about eight Kraków clubs, each signed up by its own desk.

**A seeded club is a club that signed up** (``docs/adr/0182`` §7). Nothing in the
application names one; every club here goes through ``SignUpClub``, the use case
the club website's sign-up runs, so it has a stream, an account with a stream of
its own, a search row folded by the search's own function, and a desk that signs
in on the club surface with the seed password.

**Kraków by name, and wherever the run is centred by position.** Each club is an
offset in kilometres from ``CENTRE`` — the protagonists' own cell — rather than a
coordinate, for the reason the cohort's rings are: a developer who sets
``SEED_CENTRE`` to Kraków gets the clubs in Kraków, and one who leaves it at the
London reference still gets every distance a search will print, because every
distance is measured from where the players are. The point itself is precise, as
a club's is (``docs/adr/0182`` §6): only the protagonists' cell is rounded.

**The names are arranged for the stories the later tickets tell**, and are not
decoration. Ogrody 33 is in Grzegórzki and offers tennis and padel, as #522's desk
signs it up; padel is there for #509's official group. Four clubs — and only
four — carry a ``b`` in their folded name or district, nearest first: Centrum
Ruchu, Bonarka Arena, Zabłocie Sport and Wisła Park, which is what #504's Tomek
gets for typing ``b``. Wisła Park's district is *Błonia*, the letter Unicode will
not fold, so a search for *blonia* exercises the one row of the fold's table.

**Re-running signs nobody up twice.** Each desk's email is looked up among club
accounts first, and a club already there is left exactly as it stands — a desk
that edited its details during a walk keeps its edits.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Final, final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_club_account_repository,
    build_club_repository,
    build_domain_event_store,
    build_event_publisher,
    build_password_hasher,
    build_unit_of_work,
)
from app.core.config import Settings
from app.kernel import Instant, Sport
from app.modules.clubs.application.club_details import details_from
from app.modules.clubs.application.commands import (
    ClubDetailsInput,
    SignUpClubCommand,
)
from app.modules.clubs.application.sign_up_club import SignUpClub
from app.modules.clubs.domain.folding import fold
from app.modules.matchmaking.domain.geography import KM_PER_DEGREE_OF_LATITUDE
from app.modules.users.domain.value_objects import Email
from app.seeds.catalog import CENTRE, SEED_EMAIL_DOMAIN, SEED_PASSWORD, Centre
from app.seeds.clock import FixedClock

#: Every seeded club is in this city. A club's city is the desk's own text.
CITY: Final = "Kraków"


@final
@dataclass(frozen=True, slots=True)
class SeedClub:
    """One club as its desk would sign it up, placed as an offset from the
    centre: ``north_km`` and ``east_km``, negative for south and west."""

    name: str
    district: str
    sports: frozenset[Sport]
    north_km: float
    east_km: float


SEED_CLUBS: Final[tuple[SeedClub, ...]] = (
    SeedClub(
        "Ogrody 33",
        "Grzegórzki",
        frozenset({Sport.TENNIS, Sport.PADEL}),
        north_km=0.1,
        east_km=0.6,
    ),
    SeedClub(
        "Centrum Ruchu",
        "Dębniki",
        frozenset({Sport.PADEL, Sport.SQUASH}),
        north_km=-0.6,
        east_km=-0.8,
    ),
    SeedClub(
        "Kazimierz Padel",
        "Kazimierz",
        frozenset({Sport.PADEL}),
        north_km=-1.4,
        east_km=0.3,
    ),
    SeedClub(
        "Bonarka Arena",
        "Podgórze Duchackie",
        frozenset({Sport.PADEL, Sport.TENNIS, Sport.BADMINTON}),
        north_km=-2.3,
        east_km=0.6,
    ),
    SeedClub(
        "Zabłocie Sport",
        "Podgórze",
        frozenset({Sport.SQUASH, Sport.BADMINTON}),
        north_km=-1.8,
        east_km=2.5,
    ),
    SeedClub(
        "Prądnik Tennis",
        "Prądnik Czerwony",
        frozenset({Sport.TENNIS, Sport.SQUASH}),
        north_km=3.2,
        east_km=1.4,
    ),
    SeedClub(
        "Wisła Park",
        "Błonia",
        frozenset({Sport.TENNIS}),
        north_km=0.8,
        east_km=-3.9,
    ),
    SeedClub(
        "Nowa Huta Squash",
        "Nowa Huta",
        frozenset({Sport.SQUASH, Sport.BADMINTON}),
        north_km=1.0,
        east_km=8.5,
    ),
)


def desk_email(club: SeedClub) -> str:
    """The desk's address, **derived from the club's name** so the two cannot
    drift: ``Zabłocie Sport`` signs in as ``desk.zablocie-sport@raketa.example``,
    on the TLD no registry will sell."""

    slug = re.sub(r"[^a-z0-9]+", "-", fold(club.name)).strip("-")
    return f"desk.{slug}@{SEED_EMAIL_DOMAIN}"


def point_of(club: SeedClub, centre: Centre) -> tuple[float, float]:
    """Where the club is, ``north_km`` and ``east_km`` from ``centre``.

    A flat offset, which is exact enough over the few kilometres a city spans.
    Six decimal places is a pin's own precision — a tenth of a metre — and
    nothing is rounded to the cell a player's Location area is.
    """

    latitude = centre.latitude + club.north_km / KM_PER_DEGREE_OF_LATITUDE
    longitude = centre.longitude + club.east_km / (
        KM_PER_DEGREE_OF_LATITUDE * math.cos(math.radians(centre.latitude))
    )
    return round(latitude, 6), round(longitude, 6)


def _details_of(club: SeedClub, centre: Centre) -> ClubDetailsInput:
    latitude, longitude = point_of(club, centre)
    return ClubDetailsInput(
        name=club.name,
        district=club.district,
        city=CITY,
        sports=tuple(sport for sport in Sport if sport in club.sports),
        latitude=latitude,
        longitude=longitude,
    )


# The declaration is refused on import, through the domain's own value objects,
# as the account catalog's is: a club the website would refuse fails here rather
# than half way through a run.
for _club in SEED_CLUBS:
    details_from(_details_of(_club, CENTRE))
    Email(desk_email(_club))


@final
@dataclass(frozen=True, slots=True)
class SeededClub:
    club: SeedClub
    email: str
    #: Whether this run signed it up, or found its desk already there.
    signed_up: bool


@final
@dataclass(frozen=True, slots=True)
class SeededClubs:
    clubs: tuple[SeededClub, ...]


async def write_the_clubs(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    centre: Centre = CENTRE,
) -> SeededClubs:
    """Sign up every declared club that has not signed up yet.

    One session for the layer, and each sign-up commits through its own unit of
    work, so the probe that skips a club already there reads what the previous
    run — or the previous club — committed.
    """

    async with session_factory() as session:
        event_store = build_domain_event_store(session)
        events = build_event_publisher(session)
        accounts = build_club_account_repository(
            session, event_store=event_store, events=events
        )
        sign_up = SignUpClub(
            clubs=build_club_repository(
                session, event_store=event_store, events=events
            ),
            accounts=accounts,
            hasher=build_password_hasher(settings),
            uow=build_unit_of_work(session),
            clock=FixedClock(at=now),
        )

        seeded: list[SeededClub] = []
        for club in SEED_CLUBS:
            email = desk_email(club)
            if await accounts.get_by_email(Email(email)) is not None:
                seeded.append(SeededClub(club=club, email=email, signed_up=False))
                continue
            await sign_up.execute(
                SignUpClubCommand(
                    details=_details_of(club, centre),
                    email=email,
                    password=SEED_PASSWORD,
                )
            )
            seeded.append(SeededClub(club=club, email=email, signed_up=True))
    return SeededClubs(clubs=tuple(seeded))


def club_lines(seeded: SeededClubs) -> list[str]:
    """The report's section: every club, its desk, and what this run did."""

    new = sum(1 for club in seeded.clubs if club.signed_up)
    lines = [
        f"Clubs — {len(seeded.clubs)} in {CITY}, {new} signed up by this run. Each "
        f"desk signs in on the club website with the seed password:"
    ]
    for entry in seeded.clubs:
        sports = ", ".join(
            sport.value.capitalize() for sport in Sport if sport in entry.club.sports
        )
        state = "signed up" if entry.signed_up else "already there"
        lines.append(
            f"  {entry.club.name} · {entry.club.district} · {sports} · "
            f"{entry.email} · {state}"
        )
    return lines
