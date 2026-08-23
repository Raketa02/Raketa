"""``NewArrivals``, ``ArrivalRows`` and ``Levels`` over Users, Rating and Clubs.

The one file in Now that knows *new on Raketa* means an account row's creation
stamp, that being rated at a sport is a stream that exists, and that a club sells
a sport when it has a live court in a live category for it. What is asserted here
is exactly those three translations, plus the two that decide who is *not* on a
shelf: a disabled account, and a club whose courts have all been retired.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID, uuid4

from app.engines.assessment import STATUS_INITIAL_ESTIMATE
from app.kernel import Cover, Instant, Sport, instant, zloty
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
    zone_named,
)
from app.modules.now.infrastructure.levels import LevelsFromSkillRatings
from app.modules.now.infrastructure.new_arrivals import ArrivalsFromUsersAndClubs
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    Email,
    HashedPassword,
    Nickname,
)

AT: Instant = instant(datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc))
THIRTY_DAYS_BACK: Instant = instant(AT - timedelta(days=30))

ADDRESS = StreetAddress(line="ul. Zabłocie 25", city="Kraków", postal_code="30-701")
POINT = GeoPoint(latitude=Decimal("50.048100"), longitude=Decimal("19.958500"))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


# -- hand-written stubs over the three ports --------------------------------


def a_user(
    *, nickname: str, joined: Instant, active: bool = True, who: UUID | None = None
) -> User:
    user = User(
        id=who or uuid4(),
        email=Email(f"{nickname}@example.com"),
        nickname=Nickname(nickname),
        password_hash=HashedPassword("x" * 60),
        is_active=active,
        created_at=joined,
    )
    user.pull_events()
    return user


class FakeUsers:
    """Enough of ``UserRepository`` for the two reads this adapter makes."""

    def __init__(self, *users: User) -> None:
        self._users = list(users)
        self.since_asks: list[datetime] = []

    async def add(self, user: User) -> User:  # pragma: no cover — never called
        raise AssertionError

    async def get_by_id(self, user_id: UUID) -> Optional[User]:  # pragma: no cover
        raise AssertionError

    async def get_by_email(self, email: str) -> Optional[User]:  # pragma: no cover
        raise AssertionError

    async def get_by_nickname(
        self, nickname: str
    ) -> Optional[User]:  # pragma: no cover
        raise AssertionError

    async def project_registered(
        self, event: UserRegistered
    ) -> User:  # pragma: no cover
        raise AssertionError

    async def find_registered_since(self, moment: datetime) -> list[User]:
        self.since_asks.append(moment)
        return sorted(
            (
                user
                for user in self._users
                if user.created_at is not None and user.created_at >= moment
            ),
            key=lambda user: (-user.created_at.timestamp(), user.nickname.value),
        )

    async def find_by_ids(self, user_ids: Sequence[UUID]) -> list[User]:
        wanted = set(user_ids)
        return [user for user in self._users if user.id in wanted]


class FakeRatings:
    """Enough of ``SkillRatingRepository`` for the pair read and the existence."""

    def __init__(self, *ratings: SkillRating) -> None:
        self._held = {(one.player_id, one.sport): one for one in ratings}
        self.pair_asks: list[tuple[UUID, Sport]] = []

    async def save(self, rating: SkillRating) -> None:  # pragma: no cover
        raise AssertionError

    async def exists_for(self, *, player_id: UUID, sport: Sport) -> bool:
        return (player_id, sport) in self._held

    async def find_for(self, *, player_id: UUID, sport: Sport) -> Optional[SkillRating]:
        self.pair_asks.append((player_id, sport))
        return self._held.get((player_id, sport))

    async def find_all_for(
        self, *, player_id: UUID
    ) -> list[SkillRating]:  # pragma: no cover
        raise AssertionError


class FakeClubs:
    """Enough of ``ClubRepository`` for the two reads this adapter makes."""

    def __init__(self, *clubs: Club) -> None:
        self._clubs = list(clubs)

    async def find_all(self) -> list[Club]:
        return sorted(self._clubs, key=lambda club: club.name.value)

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        wanted = set(club_ids)
        return sorted(
            (club for club in self._clubs if club.id in wanted),
            key=lambda club: club.name.value,
        )

    async def get(self, club_id: UUID) -> Optional[Club]:  # pragma: no cover
        raise AssertionError

    async def get_by_name(self, name: ClubName) -> Optional[Club]:  # pragma: no cover
        raise AssertionError

    async def add(self, club: Club) -> Club:  # pragma: no cover
        raise AssertionError

    async def save(self, club: Club) -> Club:  # pragma: no cover
        raise AssertionError


def a_club(
    *,
    name: str,
    joined: Instant,
    sports: Sequence[Sport] = (Sport.PADEL,),
    courts: bool = True,
    retire_courts: bool = False,
) -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName(name),
        address=ADDRESS,
        point=POINT,
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PAYOUT,
        at=joined,
    )
    for index, sport in enumerate(sports):
        category = club.add_category(
            category_id=uuid4(),
            name=CategoryName(f"{sport.value} {index}"),
            sport=sport,
            cover=Cover.INDOOR,
            rate=zloty(80),
        )
        if courts:
            court = club.add_court(
                court_id=uuid4(),
                category_id=category.id,
                label=CourtLabel(f"Court {index + 1}"),
                at=joined,
            )
            if retire_courts:
                club.retire_court(court.id, at=joined)
    club.created_at = joined
    return club


def a_rating(
    *, player_id: UUID, sport: Sport, mu: float, status: str = STATUS_INITIAL_ESTIMATE
) -> SkillRating:
    return SkillRating(
        id=uuid4(),
        player_id=player_id,
        sport=sport,
        mu=mu,
        sigma=0.9,
        confidence=25,
        range_low=max(1.0, mu - 0.9),
        range_high=min(5.0, mu + 0.9),
        band_name="Developing",
        band_lower=1.6,
        band_upper=2.6,
        status=status,
        engine_version="racketskill-v3",
        updated_at=AT,
    )


def _arrivals(
    *, users: FakeUsers, ratings: FakeRatings, clubs: FakeClubs
) -> ArrivalsFromUsersAndClubs:
    return ArrivalsFromUsersAndClubs(users=users, ratings=ratings, clubs=clubs)


# -- who is new here ---------------------------------------------------------


async def test_a_new_player_is_one_registered_inside_the_window_and_rated() -> None:
    nadia = a_user(nickname="nadia", joined=instant(AT - timedelta(days=3)))
    users = FakeUsers(nadia)
    arrivals = _arrivals(
        users=users,
        ratings=FakeRatings(a_rating(player_id=nadia.id, sport=Sport.PADEL, mu=2.5)),
        clubs=FakeClubs(),
    )

    assert await arrivals.player_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == (
        nadia.id,
    )
    assert users.since_asks == [THIRTY_DAYS_BACK]


async def test_a_rating_is_a_fact_filter_and_never_an_imputed_one() -> None:
    # A badminton-only player has no Level at squash, so putting her on a squash
    # shelf would print a number the platform imputed rather than one it holds.
    nadia = a_user(nickname="nadia", joined=instant(AT - timedelta(days=3)))
    arrivals = _arrivals(
        users=FakeUsers(nadia),
        ratings=FakeRatings(
            a_rating(player_id=nadia.id, sport=Sport.BADMINTON, mu=2.5)
        ),
        clubs=FakeClubs(),
    )

    assert await arrivals.player_ids(sport=Sport.SQUASH, since=THIRTY_DAYS_BACK) == ()


async def test_a_disabled_account_is_not_somebody_to_meet() -> None:
    gone = a_user(nickname="gone", joined=instant(AT - timedelta(days=3)), active=False)
    arrivals = _arrivals(
        users=FakeUsers(gone),
        ratings=FakeRatings(a_rating(player_id=gone.id, sport=Sport.PADEL, mu=2.5)),
        clubs=FakeClubs(),
    )

    assert await arrivals.player_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == ()
    assert await arrivals.players(player_ids=[gone.id]) == ()


async def test_a_club_sells_a_sport_when_it_has_a_live_court_in_a_live_category() -> (
    None
):
    club = a_club(name="Zabłocie", joined=instant(AT - timedelta(days=5)))
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(club)
    )

    assert await arrivals.club_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == (
        club.id,
    )


async def test_a_category_whose_courts_are_all_retired_sells_nothing() -> None:
    # Retire every court in a category and it survives as a group nothing can be
    # assigned in, so a shelf that counted it would send a player to a club with
    # nothing to book.
    empty = a_club(
        name="Empty", joined=instant(AT - timedelta(days=5)), retire_courts=True
    )
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(empty)
    )

    assert await arrivals.club_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == ()


async def test_a_club_with_no_courts_at_all_sells_nothing() -> None:
    bare = a_club(name="Bare", joined=instant(AT - timedelta(days=5)), courts=False)
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(bare)
    )

    assert await arrivals.club_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == ()


async def test_a_club_that_arrived_before_the_window_is_not_new() -> None:
    old = a_club(name="Old", joined=instant(AT - timedelta(days=90)))
    fresh = a_club(name="Fresh", joined=instant(AT - timedelta(days=2)))
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(old, fresh)
    )
    sixty_back = instant(AT - timedelta(days=60))

    assert await arrivals.club_ids(sport=Sport.PADEL, since=sixty_back) == (fresh.id,)


async def test_a_padel_chip_never_surfaces_a_squash_only_club() -> None:
    squash_only = a_club(
        name="Squash only",
        joined=instant(AT - timedelta(days=5)),
        sports=(Sport.SQUASH,),
    )
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(squash_only)
    )

    assert await arrivals.club_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == ()


async def test_the_membership_answer_is_newest_first() -> None:
    older = a_club(name="Older", joined=instant(AT - timedelta(days=20)))
    newer = a_club(name="Newer", joined=instant(AT - timedelta(days=2)))
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(older, newer)
    )

    assert await arrivals.club_ids(sport=Sport.PADEL, since=THIRTY_DAYS_BACK) == (
        newer.id,
        older.id,
    )


# -- the rows ----------------------------------------------------------------


async def test_a_player_row_is_a_nickname_and_when_she_joined() -> None:
    joined = instant(AT - timedelta(days=3))
    nadia = a_user(nickname="nadia", joined=joined)
    arrivals = _arrivals(
        users=FakeUsers(nadia), ratings=FakeRatings(), clubs=FakeClubs()
    )

    rows = await arrivals.players(player_ids=[nadia.id])
    assert [(row.nickname, row.joined_at) for row in rows] == [("nadia", joined)]


async def test_a_club_row_carries_no_distance_because_there_is_no_anchor() -> None:
    # A distance is measured from the glossary's Distance anchor, the anchor is
    # optional, and precision follows it (ADR-0063). Absent, and never a zero.
    club = a_club(name="Zabłocie", joined=instant(AT - timedelta(days=5)))
    arrivals = _arrivals(
        users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs(club)
    )

    rows = await arrivals.clubs(club_ids=[club.id])
    assert [(row.name, row.distance_km) for row in rows] == [("Zabłocie", None)]


async def test_a_row_read_is_silently_short_on_a_stranger() -> None:
    # The caller holds a set that may be fifteen minutes old, so an account that
    # has gone since is an ordinary outcome and not a reason to fail a screen.
    arrivals = _arrivals(users=FakeUsers(), ratings=FakeRatings(), clubs=FakeClubs())

    assert await arrivals.players(player_ids=[uuid4()]) == ()
    assert await arrivals.clubs(club_ids=[uuid4()]) == ()


# -- the Level ---------------------------------------------------------------


async def test_a_level_is_the_ratings_mu_at_that_sport() -> None:
    who = uuid4()
    levels = LevelsFromSkillRatings(
        FakeRatings(a_rating(player_id=who, sport=Sport.PADEL, mu=2.71))
    )

    answer = await levels.at(sport=Sport.PADEL, players=[who])
    assert answer[who].value == 2.71


async def test_a_questionnaire_derived_level_carries_the_quiet_marker() -> None:
    who = uuid4()
    levels = LevelsFromSkillRatings(
        FakeRatings(
            a_rating(
                player_id=who,
                sport=Sport.PADEL,
                mu=2.71,
                status=STATUS_INITIAL_ESTIMATE,
            )
        )
    )

    answer = await levels.at(sport=Sport.PADEL, players=[who])
    assert answer[who].provisional is True


async def test_a_level_a_counted_match_has_moved_carries_no_marker() -> None:
    who = uuid4()
    levels = LevelsFromSkillRatings(
        FakeRatings(
            a_rating(player_id=who, sport=Sport.PADEL, mu=2.71, status="Calibrating")
        )
    )

    answer = await levels.at(sport=Sport.PADEL, players=[who])
    assert answer[who].provisional is False


async def test_a_player_with_no_rating_at_that_sport_is_absent_never_a_zero() -> None:
    who = uuid4()
    levels = LevelsFromSkillRatings(
        FakeRatings(a_rating(player_id=who, sport=Sport.TENNIS, mu=2.71))
    )

    assert await levels.at(sport=Sport.PADEL, players=[who]) == {}


async def test_one_player_asked_for_twice_is_read_once() -> None:
    who = uuid4()
    ratings = FakeRatings(a_rating(player_id=who, sport=Sport.PADEL, mu=2.71))
    levels = LevelsFromSkillRatings(ratings)

    await levels.at(sport=Sport.PADEL, players=[who, who])
    assert ratings.pair_asks == [(who, Sport.PADEL)]


async def test_the_viewer_and_a_candidate_get_their_level_the_same_way() -> None:
    # The shelf's whole order is one subtraction between two answers, and two
    # ways of getting a Level is how the two sides of a subtraction come to
    # disagree.
    viewer, candidate = uuid4(), uuid4()
    levels = LevelsFromSkillRatings(
        FakeRatings(
            a_rating(player_id=viewer, sport=Sport.PADEL, mu=3.0),
            a_rating(player_id=candidate, sport=Sport.PADEL, mu=3.4),
        )
    )

    answer = await levels.at(sport=Sport.PADEL, players=[viewer, candidate])
    assert set(answer) == {viewer, candidate}
