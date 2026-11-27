"""The source of a pool's courts, hour by hour (``docs/adr/0202`` §7; the friends
mechanics §6; #746).

**Ogrody 33 gives Rakieta its hours, Saturday 10:00 is fully booked, and Tuesday
21:00 still has a court.** Wisła Park is 4 km away and sells both hours; Tenis
Katowice is 15 km away and sells both too.

- **An official group** is offered the home club's free courts. Only at an hour
  where the home club has none, and while its switch is on, other clubs within
  the club's distance are offered too, each marked as offered because the home
  club is full. Switched off, the group plays only at its club.
- **A player group** is unchanged: the home club first, then the clubs within
  10 km, at any hour.

Read as every caller reads it: ``WherePoolsPlay.of`` — the club's switch and
distance off the offer its club publishes, the clubs around it off the Club
directory — and then the pool's clubs asked which of the hours on sale they
offer. The ports are stood in for; the rule is real.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.kernel import Instant, Sport, instant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.clubs.domain.ports import ClubListing
from app.modules.clubs.domain.rakieta_terms import OtherClubsCourts, RakietaSettings
from app.modules.clubs.domain.sellable import ClubOffer
from app.modules.matchmaking.domain.geography import KM_PER_DEGREE_OF_LATITUDE
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposer import CourtHourOnSale, PoolClubs
from app.modules.proposals.infrastructure.group_clubs import GroupClubs

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int) -> Instant:
    """An hour in Kraków in October 2026. The fifth is a Monday."""

    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


NOW = warsaw(5, 8)
#: Saturday 10:00, which Ogrody 33 has booked out.
SATURDAY_TEN = warsaw(10, 10)
#: Tuesday 21:00, where Ogrody 33 still has a court.
TUESDAY_21 = warsaw(6, 21)

OGRODY, WISLA_PARK, KATOWICE = uuid4(), uuid4(), uuid4()
GROUP = Pool(id=uuid4(), kind=PoolKind.GROUP)


def north_of_ogrody(km: float) -> tuple[float, float]:
    return 50.06 + km / KM_PER_DEGREE_OF_LATITUDE, 19.94


POINTS = {
    OGRODY: north_of_ogrody(0),
    WISLA_PARK: north_of_ogrody(4),
    KATOWICE: north_of_ogrody(15),
}


@dataclass(frozen=True)
class Listing:
    """What the court source reads of a group's listing."""

    home_club_id: UUID
    is_official: bool


@dataclass
class Groups:
    listing: Listing

    async def listings(self, group_ids):
        return {group_id: self.listing for group_id in group_ids}


class Clubs:
    """The Club directory over ``POINTS``."""

    async def listed(self, club_ids):
        return {club_id: self._listing(club_id) for club_id in club_ids}

    async def inside(self, *, south, north, west, east):
        return [
            self._listing(club_id)
            for club_id, (latitude, longitude) in POINTS.items()
            if south <= latitude <= north and west <= longitude <= east
        ]

    @staticmethod
    def _listing(club_id: UUID) -> ClubListing:
        latitude, longitude = POINTS[club_id]
        return ClubListing(
            id=club_id,
            name=str(club_id),
            district="",
            sports=(Sport.PADEL, Sport.TENNIS),
            latitude=latitude,
            longitude=longitude,
        )


@dataclass
class Sellable:
    """Ogrody 33's offer — its terms, which is all the court source reads."""

    settings: RakietaSettings = field(default_factory=RakietaSettings)

    async def between(self, club_ids, *, start, end, now):
        return {
            club_id: ClubOffer(
                club_id=club_id,
                settings=self.settings,
                taking_new_cards=True,
                zone=CLUB_ZONE,
                hours=(),
            )
            for club_id in club_ids
            if club_id == OGRODY
        }


def on_sale(
    club: UUID,
    start: Instant,
    *,
    sport: Sport = Sport.PADEL,
    taking_new_cards: bool = True,
    release_lead: timedelta = timedelta(days=1),
) -> CourtHourOnSale:
    return CourtHourOnSale(
        club_id=club,
        sport=sport,
        start=start,
        courts=1,
        share_grosze=30_00,
        book_by=start - release_lead,
        taking_new_cards=taking_new_cards,
    )


#: Saturday 10:00 is booked out at Ogrody 33; everything else is free.
THE_WEEK = [
    on_sale(OGRODY, TUESDAY_21),
    on_sale(WISLA_PARK, TUESDAY_21),
    on_sale(WISLA_PARK, SATURDAY_TEN),
    on_sale(KATOWICE, TUESDAY_21),
    on_sale(KATOWICE, SATURDAY_TEN),
]


async def the_courts_of(
    *, official: bool = True, settings: RakietaSettings | None = None
) -> PoolClubs:
    clubs = await GroupClubs(
        groups=Groups(Listing(home_club_id=OGRODY, is_official=official)),
        clubs=Clubs(),
        sellable=Sellable(settings or RakietaSettings()),
    ).of(GROUP, now=NOW)
    assert clubs is not None
    return clubs


def offered(
    clubs: PoolClubs, hours: list[CourtHourOnSale]
) -> list[tuple[UUID, Instant, bool]]:
    """Each hour offered, soonest first and nearest first: its club, its
    start, and whether it is offered because the home club is full then."""

    return sorted(
        (
            (hour.club_id, hour.start, clubs.because_home_is_full(hour))
            for hour in clubs.offered(hours, now=NOW)
        ),
        key=lambda row: (row[1], list(POINTS).index(row[0])),
    )


# --------------------------------------------------------------------------- #
# An official group
# --------------------------------------------------------------------------- #


async def test_where_the_home_club_has_a_free_court_only_the_home_club_is_offered():
    clubs = await the_courts_of()

    assert offered(clubs, [on_sale(OGRODY, SATURDAY_TEN), *THE_WEEK]) == [
        (OGRODY, TUESDAY_21, False),
        (OGRODY, SATURDAY_TEN, False),
    ]


async def test_where_the_home_club_is_full_a_club_within_its_distance_is_offered():
    clubs = await the_courts_of()

    # On by default: Wisła Park at Saturday 10:00, marked, and never at Tuesday
    # 21:00, where Ogrody 33 has a court.
    assert offered(clubs, THE_WEEK) == [
        (OGRODY, TUESDAY_21, False),
        (WISLA_PARK, SATURDAY_TEN, True),
    ]


async def test_switched_off_the_group_plays_only_at_its_club():
    clubs = await the_courts_of(
        settings=RakietaSettings(other_clubs_courts=OtherClubsCourts(offered=False))
    )

    assert offered(clubs, THE_WEEK) == [(OGRODY, TUESDAY_21, False)]


async def test_a_club_beyond_the_club_s_distance_is_never_offered():
    near = await the_courts_of(
        settings=RakietaSettings(other_clubs_courts=OtherClubsCourts(within_km=3))
    )
    far = await the_courts_of(
        settings=RakietaSettings(other_clubs_courts=OtherClubsCourts(within_km=16))
    )

    # Wisła Park is 4 km away and Tenis Katowice 15.
    assert offered(near, THE_WEEK) == [(OGRODY, TUESDAY_21, False)]
    assert offered(far, THE_WEEK) == [
        (OGRODY, TUESDAY_21, False),
        (WISLA_PARK, SATURDAY_TEN, True),
        (KATOWICE, SATURDAY_TEN, True),
    ]


async def test_full_is_read_per_sport():
    clubs = await the_courts_of()

    # Ogrody 33 still has padel at Saturday 10:00, and its tennis is booked out.
    hours = [
        on_sale(OGRODY, SATURDAY_TEN),
        on_sale(WISLA_PARK, SATURDAY_TEN),
        on_sale(WISLA_PARK, SATURDAY_TEN, sport=Sport.TENNIS),
    ]

    assert [
        (hour.club_id, hour.sport, clubs.because_home_is_full(hour))
        for hour in clubs.offered(hours, now=NOW)
    ] == [
        (OGRODY, Sport.PADEL, False),
        (WISLA_PARK, Sport.TENNIS, True),
    ]


async def test_a_home_court_no_new_card_may_be_made_at_is_no_free_court():
    clubs = await the_courts_of()

    tonight = warsaw(5, 20)

    # Paused, or past its book-by — Ogrody 33 releases tonight's hours a day
    # ahead and Wisła Park two hours ahead: no new card may be made at home,
    # so it has nothing to sell at that hour.
    assert offered(
        clubs,
        [
            on_sale(OGRODY, SATURDAY_TEN, taking_new_cards=False),
            on_sale(WISLA_PARK, SATURDAY_TEN),
        ],
    ) == [(WISLA_PARK, SATURDAY_TEN, True)]
    assert offered(
        clubs,
        [
            on_sale(OGRODY, tonight),
            on_sale(WISLA_PARK, tonight, release_lead=timedelta(hours=2)),
        ],
    ) == [(WISLA_PARK, tonight, True)]


# --------------------------------------------------------------------------- #
# A player group
# --------------------------------------------------------------------------- #


async def test_a_player_group_is_offered_every_club_within_ten_km_at_every_hour():
    clubs = await the_courts_of(official=False)

    # Its home club first at the same hour is the caller's order, not a
    # refusal: Wisła Park is offered at Tuesday 21:00 too, and marked nowhere.
    assert offered(clubs, THE_WEEK) == [
        (OGRODY, TUESDAY_21, False),
        (WISLA_PARK, TUESDAY_21, False),
        (WISLA_PARK, SATURDAY_TEN, False),
    ]
