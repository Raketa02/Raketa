"""``CityMatches`` over Matches, Clubs, Courts, Rating — and the cache behind it.

Every claim this adapter makes is a claim about **cost**, and a cheaper read and
a dearer one give the same screen. Nothing in the composer's suite can see any of
them: swap the cache for a no-op, ask a club for every match instead of once, or
rebuild a context that is already held, and every card in
``tests/unit/test_compose_shelves.py`` is identical.

So the fakes here refuse the read that was not supposed to happen, and count the
ones that were.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping, Sequence
from uuid import UUID, uuid4

from app.engines.matchmaking import Occupant
from app.kernel import Cover, Instant, Sport, hours, instant, minutes, shifted, zloty
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
from app.modules.courts.domain.reservation import Reservation
from app.modules.courts.domain.time_range import TimeRange
from app.modules.matches.domain.match import Match
from app.modules.now.domain.funnel import CANDIDATE_LIMIT, MatchScoringContext
from app.modules.now.infrastructure.city_matches import CityMatchesFromMatches
from app.modules.now.infrastructure.scoring_contexts import InMemoryScoringContexts
from app.modules.now.domain.screen import Money
from tests.unit.shelf_doubles import SHARE, a_club, rated

AT: Instant = instant(datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc))
PADEL = frozenset({Sport.PADEL})


def _club(*, courts: int = 4, name: str = "Zabłocie Sport") -> Club:
    club = Club.found(
        club_id=uuid4(),
        name=ClubName(name),
        address=StreetAddress(
            line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
        ),
        point=GeoPoint(latitude=Decimal("50.0481"), longitude=Decimal("19.9585")),
        timezone=zone_named("Europe/Warsaw"),
        pricing=ClubPricing(),
        policy=ClubPolicy(),
        payout=PayoutDestination(
            account_holder="Zabłocie", iban="PL61109010140000071219812874"
        ),
        at=AT,
    )
    category = club.add_category(
        category_id=uuid4(),
        name=CategoryName("Padel · hall"),
        sport=Sport.PADEL,
        cover=Cover.INDOOR,
        rate=zloty(80),
    )
    for index in range(courts):
        club.add_court(
            category_id=category.id,
            court_id=uuid4(),
            label=CourtLabel(f"Court {index + 1}"),
            at=AT,
        )
    return club


def _match(club: Club, *, starts: int = 2880, seated: tuple[UUID, ...] = ()) -> Match:
    match = Match.post(
        match_id=uuid4(),
        club_id=club.id,
        category_id=club.live_categories[0].id,
        sport=Sport.PADEL,
        start=shifted(AT, minutes(starts)),
        duration=hours(1),
        share=SHARE,
        policy=club.policy_now.hold_policy(),
        at=AT,
    )
    for player in seated:
        match.take_seat(player, at=AT)
        match.pay_seat(player, at=AT)
    return match


class CountingMatches:
    """The one read retrieval may make, counted."""

    def __init__(self, *matches: Match) -> None:
        self._matches = list(matches)
        self.window_asks: list[tuple[Instant, Instant]] = []

    async def starting_between(
        self, *, club_ids: Sequence[UUID], window_from: Instant, window_to: Instant
    ) -> list[Match]:
        self.window_asks.append((window_from, window_to))
        return [
            match
            for match in self._matches
            if match.club_id in set(club_ids)
            and window_from <= match.start <= window_to
        ]

    async def get(self, match_id: UUID) -> Match | None:  # pragma: no cover
        raise AssertionError("retrieval reads the window, never one match at a time")

    async def for_player(self, player_id: UUID) -> list[Match]:  # pragma: no cover
        raise AssertionError("retrieval knows nothing about the viewer")

    async def for_club(self, club_id: UUID) -> list[Match]:  # pragma: no cover
        raise AssertionError("a club at a time is a read per club")

    async def add(self, match: Match) -> Match:  # pragma: no cover
        raise AssertionError("Now writes nothing")

    async def save(self, match: Match) -> Match:  # pragma: no cover
        raise AssertionError("Now writes nothing")


class CountingClubs:
    """Clubs, batched into one read and never one per match."""

    def __init__(self, *clubs: Club) -> None:
        self._clubs = list(clubs)
        self.all_asks = 0

    async def find_all(self) -> list[Club]:
        self.all_asks += 1
        return list(self._clubs)

    async def get(self, club_id: UUID) -> Club | None:  # pragma: no cover
        raise AssertionError("a club at a time is a read per match")

    async def find_by_ids(self, club_ids: Sequence[UUID]) -> list[Club]:
        return [club for club in self._clubs if club.id in set(club_ids)]

    async def get_by_name(self, name: ClubName) -> Club | None:  # pragma: no cover
        raise AssertionError("retrieval never looks a club up by name")

    async def add(self, club: Club) -> Club:  # pragma: no cover
        raise AssertionError("Now writes nothing")

    async def save(self, club: Club) -> Club:  # pragma: no cover
        raise AssertionError("Now writes nothing")


class CountingReservations:
    """The saturation read, counted — one per club **and hour**, never per match."""

    def __init__(self, *live: Reservation) -> None:
        self._live = list(live)
        self.window_asks: list[TimeRange] = []

    async def overlapping(
        self, *, court_ids: Sequence[UUID], window: TimeRange
    ) -> list[Reservation]:
        self.window_asks.append(window)
        return [
            one
            for one in self._live
            if one.court_id in set(court_ids) and one.claimed.overlaps(window)
        ]

    async def get(self, reservation_id: UUID):  # pragma: no cover
        raise AssertionError("saturation is a window, never one booking")

    async def for_court(self, court_id: UUID):  # pragma: no cover
        raise AssertionError("a court's history is not what crowding asks")

    async def for_match(self, match_id: UUID):  # pragma: no cover
        raise AssertionError("a read per match is the loop this avoids")

    async def add(self, reservation: Reservation):  # pragma: no cover
        raise AssertionError("Now writes nothing")

    async def save(self, reservation: Reservation):  # pragma: no cover
        raise AssertionError("Now writes nothing")


class CountingRatings:
    """One rating per (player, sport), memoised across the whole call."""

    def __init__(self, **held: Occupant) -> None:
        self._held = {UUID(who): occupant for who, occupant in held.items()}
        self.asks: list[tuple[UUID, Sport]] = []

    async def occupant(self, *, player_id: UUID, sport: Sport) -> Occupant | None:
        self.asks.append((player_id, sport))
        return self._held.get(player_id)


class RefusingCache:
    """A cache that answers nothing and records what it was told to remember."""

    def __init__(self, *held: MatchScoringContext) -> None:
        self._held = {(one.match_id, one.version): one for one in held}
        self.asked: list[tuple[tuple[UUID, int], ...]] = []
        self.stored: list[tuple[tuple[UUID, int], ...]] = []

    async def known(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> Mapping[tuple[UUID, int], MatchScoringContext]:
        self.asked.append(tuple(keys))
        return {key: self._held[key] for key in keys if key in self._held}

    async def remember(self, contexts: Sequence[MatchScoringContext]) -> None:
        self.stored.append(tuple((one.match_id, one.version) for one in contexts))
        for one in contexts:
            self._held[(one.match_id, one.version)] = one


def _adapter(*, matches, clubs, reservations, ratings, contexts):
    return CityMatchesFromMatches(
        matches=matches,
        clubs=clubs,
        reservations=reservations,
        ratings=ratings,
        contexts=contexts,
    )


async def _contexts(adapter, *, sports=PADEL):
    return await adapter.contexts(
        sports=sports, window_from=AT, window_to=shifted(AT, minutes(20160))
    )


# --- the reads it makes -----------------------------------------------------


async def test_the_clubs_are_read_once_however_many_matches_there_are() -> None:
    club = _club()
    clubs = CountingClubs(club)
    adapter = _adapter(
        matches=CountingMatches(
            *[_match(club, starts=2880 + n * 60) for n in range(5)]
        ),
        clubs=clubs,
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    rows = await _contexts(adapter)

    assert len(rows) == 5
    assert clubs.all_asks == 1


async def test_saturation_is_one_read_per_club_and_hour_and_not_per_match() -> None:
    """A club is not crowded — it is crowded on a Tuesday evening.

    The eight matches a busy club runs at 19:00 share one answer, and paying for
    it eight times is the read this port exists to bound.
    """

    club = _club()
    reservations = CountingReservations()
    together = [_match(club, starts=2880) for _ in range(4)]
    apart = _match(club, starts=3060)
    adapter = _adapter(
        matches=CountingMatches(*together, apart),
        clubs=CountingClubs(club),
        reservations=reservations,
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    await _contexts(adapter)

    assert len(reservations.window_asks) == 2


async def test_a_seated_players_rating_is_read_once_across_the_whole_call() -> None:
    """A club's Tuesday evening is largely the same twelve people."""

    club = _club()
    regular = uuid4()
    ratings = CountingRatings(**{str(regular): rated(300)})
    adapter = _adapter(
        matches=CountingMatches(
            *[_match(club, starts=2880 + n * 60, seated=(regular,)) for n in range(4)]
        ),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=ratings,
        contexts=RefusingCache(),
    )

    await _contexts(adapter)

    assert ratings.asks == [(regular, Sport.PADEL)]


async def test_an_empty_sport_filter_costs_no_read_at_all() -> None:
    """A viewer rated at nothing is ranked against nothing.

    Asking for every match in the city in order to filter them all out is the
    most expensive way to answer the emptiest screen.
    """

    clubs = CountingClubs(_club())
    adapter = _adapter(
        matches=CountingMatches(),
        clubs=clubs,
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    assert await _contexts(adapter, sports=frozenset()) == ()
    assert clubs.all_asks == 0


async def test_the_safety_valve_bounds_what_is_built_and_keeps_the_soonest() -> None:
    """A valve *after* the assembly would have paid for every context first.

    It is not a product decision — it exists so a misconfigured filter cannot
    pull a city into memory — and a truncation that ever fires should lose the
    matches furthest out, which are the least useful end.
    """

    club = _club()
    reservations = CountingReservations()
    spread = [_match(club, starts=2880 + n) for n in range(CANDIDATE_LIMIT + 20)]
    adapter = _adapter(
        matches=CountingMatches(*spread),
        clubs=CountingClubs(club),
        reservations=reservations,
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    rows = await _contexts(adapter)

    assert len(rows) == CANDIDATE_LIMIT
    assert {one.match_id for one in rows} == {
        one.id for one in spread[:CANDIDATE_LIMIT]
    }
    # And it truncated before the expensive half rather than after it: one
    # reservation read per distinct start, and never one per candidate found.
    assert len(reservations.window_asks) == CANDIDATE_LIMIT


# --- the cache behind it ----------------------------------------------------


async def test_the_cache_is_asked_before_anything_expensive_happens() -> None:
    """The whole reason it is behind this port rather than in front of it.

    Above the port, every context would be assembled and then discarded for the
    copy already held — a cache that saves nothing at all.
    """

    club = _club()
    match = _match(club, seated=(uuid4(),))
    cache = RefusingCache()
    reservations = CountingReservations()
    ratings = CountingRatings()
    adapter = _adapter(
        matches=CountingMatches(match),
        clubs=CountingClubs(club),
        reservations=reservations,
        ratings=ratings,
        contexts=cache,
    )

    first = await _contexts(adapter)
    assert cache.asked[0] == ((match.id, match.version),)
    assert cache.stored == [((match.id, match.version),)]

    second = await _contexts(adapter)

    assert [one.match_id for one in second] == [one.match_id for one in first]
    # The warm ask paid for neither of the two expensive reads.
    assert len(reservations.window_asks) == 1
    assert len(ratings.asks) == 1


async def test_a_bumped_version_misses_and_is_rebuilt() -> None:
    """The invalidation ADR-0068 asks for **is** the key.

    A seat payment bumps the version, so the next ask files under a key that was
    never written. There is no TTL, no reverse index and no `forget`.
    """

    club = _club()
    match = _match(club)
    cache = RefusingCache()
    adapter = _adapter(
        matches=CountingMatches(match),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=cache,
    )

    await _contexts(adapter)
    match.version += 1
    await _contexts(adapter)

    assert cache.stored == [
        ((match.id, match.version - 1),),
        ((match.id, match.version),),
    ]


async def test_a_warm_context_is_the_one_that_comes_back() -> None:
    """Held under its own version, so a hit is never a stale answer."""

    club = _club()
    match = _match(club)
    cache = RefusingCache()
    adapter = _adapter(
        matches=CountingMatches(match),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=cache,
    )

    first = (await _contexts(adapter))[0]
    second = (await _contexts(adapter))[0]

    assert second is first


# --- what a context carries -------------------------------------------------


async def test_the_roof_is_read_live_off_the_category() -> None:
    club = _club()
    adapter = _adapter(
        matches=CountingMatches(_match(club)),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    row = (await _contexts(adapter))[0]

    assert row.club.cover is Cover.INDOOR
    assert row.club.name == "Zabłocie Sport"
    assert str(row.club.zone) == "Europe/Warsaw"


async def test_crowding_is_the_share_of_live_courts_committed_in_the_window() -> None:
    """A share and not a court count: two free courts is plenty at a two-court
    club and nothing at a twenty-court one."""

    club = _club(courts=4)
    match = _match(club)
    played = TimeRange(start=match.start, end=shifted(match.start, hours(1)))
    taken = [
        Reservation(
            id=uuid4(),
            club_id=club.id,
            court_id=court.id,
            category_id=club.live_categories[0].id,
            played=played,
            claimed=played,
            holder=None,
        )
        for court in club.live_courts[:1]
    ]
    adapter = _adapter(
        matches=CountingMatches(match),
        clubs=CountingClubs(club),
        reservations=CountingReservations(*taken),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    row = (await _contexts(adapter))[0]

    assert row.club.crowding == 1 / 4


async def test_a_club_with_no_live_courts_is_full_rather_than_empty() -> None:
    """There is nothing left to give, which is what the term reads crowding for.

    Zero would be the most flattering answer available and the fabricated
    observation ADR-0027 exists to remove.
    """

    club = _club(courts=0)
    adapter = _adapter(
        matches=CountingMatches(_match(club)),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    row = (await _contexts(adapter))[0]

    assert row.club.crowding == 1


async def test_an_empty_seat_carries_nobody_and_a_stranger_carries_no_rating() -> None:
    club = _club()
    stranger = uuid4()
    adapter = _adapter(
        matches=CountingMatches(_match(club, seated=(stranger,))),
        clubs=CountingClubs(club),
        reservations=CountingReservations(),
        ratings=CountingRatings(),
        contexts=RefusingCache(),
    )

    row = (await _contexts(adapter))[0]

    assert row.occupants[0] is not None
    assert row.occupants[1:] == (None, None, None)


async def test_the_in_memory_cache_sheds_its_oldest_entries_past_its_cap() -> None:
    """A context is never invalidated, so the store has to be bounded.

    Without a bound, a match played on Tuesday sits in memory until the process
    restarts — the cost of having no TTL at all.
    """

    store = InMemoryScoringContexts(cap=2)
    club = _club()
    rows = [
        MatchScoringContext(
            match_id=uuid4(),
            version=1,
            record=_match(club).as_record(),
            club=a_club(),
            share=Money(amount=SHARE),
            court_total=Money(amount=SHARE),
            occupants=(None, None, None, None),
        )
        for _ in range(3)
    ]

    for row in rows:
        await store.remember([row])
    held = await store.known([(one.match_id, one.version) for one in rows])

    assert set(held) == {(rows[1].match_id, 1), (rows[2].match_id, 1)}
