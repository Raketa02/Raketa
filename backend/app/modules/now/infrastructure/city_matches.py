"""``CityMatches`` over Matches, Clubs, Courts and Rating.

The one file in Now that knows a suggestible match is a Matches record, that a
club is where the zone, the roof and the saturation come from, that saturation is
a question about **reservations**, and that a seated player's Level is a rating
stream.

**Five ports and no session**, on the precedent ``EnrolledFromMatches`` set —
and one of them is Now's own ``Ratings`` rather than the rating repository, so the
one crossing from a stored ``float`` μ into the engines' exact ``Fraction``
happens in a single place for the whole screen.

**The context cache is *behind* this port and not in front of it**, which is the
opposite of where ADR-0068 puts the new-arrivals cache — and the ADR's own line is
why. That one is cache-aside in the composer because *"the key is a fact about the
viewer and the port's question is not"*: it is filed under the viewer's city, so a
decorator would have to be handed one. This key is ``matchId : recordVersion`` and
carries **nothing about the asker**, so the read that populates it and the read
that answers from it are the same question — and putting the cache above the port
would mean assembling every context and then discarding it for the copy already
held, which is a cache that saves nothing at all.

**It reads facts and decides nothing.** Which matches are eligible, what a card
prints, how the shelf is ordered and whether the badge is withheld are all
``ComposeShelves``'s, where they can be exercised without a database. What is
here is the reach.

**The cost is stated rather than hidden**, and it is the reason ADR-0068 puts a
cache in front of this port at all:

* one read finds every match in the window, at every club;
* the clubs are batched into one read;
* **everything after that is paid only for a cache miss** — a match already held
  under its own version costs the club lookup and stops;
* **crowding is one reservation read per (club, hour)**, not per match — a club
  is not crowded, it is crowded on a Tuesday evening, and every match at that
  club and that hour shares the answer;
* a seated player's rating is one stream load, memoised for the length of one
  call, because the same four people appear across a club's evening.

The first two are per **ask** and the rest are per **match and version**, so a
city's matches are assembled once between everybody looking at them.
"""

from __future__ import annotations

from uuid import UUID

from app.engines.matchmaking import Occupant, PlayerRef, UnratedPlayer
from app.kernel import (
    Cover,
    Instant,
    Ratio,
    Sport,
    grosze,
    ratio,
    shifted,
)

from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.time_range import TimeRange
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.modules.now.domain.funnel import (
    CANDIDATE_LIMIT,
    ClubFacts,
    MatchScoringContext,
)
from app.modules.now.domain.ports import Ratings, ScoringContexts
from app.modules.now.domain.screen import Money


class CityMatchesFromMatches:
    """Every match in the window, with everything scoring one needs."""

    def __init__(
        self,
        *,
        matches: MatchRepository,
        clubs: ClubRepository,
        reservations: ReservationRepository,
        ratings: Ratings,
        contexts: ScoringContexts,
    ) -> None:
        self._matches = matches
        self._clubs = clubs
        self._reservations = reservations
        self._ratings = ratings
        self._contexts = contexts

    async def contexts(
        self, *, sports: frozenset[Sport], window_from: Instant, window_to: Instant
    ) -> tuple[MatchScoringContext, ...]:
        if not sports:
            # A viewer rated at nothing is ranked against nothing, and asking
            # for every match in the city in order to filter them all out is the
            # most expensive way to answer the emptiest screen.
            return ()

        clubs = {club.id: club for club in await self._clubs.find_all()}
        if not clubs:
            return ()

        found = await self._matches.starting_between(
            club_ids=sorted(clubs),
            window_from=window_from,
            window_to=window_to,
        )
        wanted = [match for match in found if match.sport in sports]
        if not wanted:
            return ()
        if len(wanted) > CANDIDATE_LIMIT:
            # The safety valve, and **not** a product decision: it exists so a
            # misconfigured filter cannot pull a city into memory. It is here
            # rather than in the composer because everything below it is the
            # expensive half — truncating after the assembly would have paid for
            # every context first, which is the shape it exists to prevent.
            # Soonest first, so a truncation that ever fires loses the least
            # useful end.
            wanted.sort(key=lambda match: (match.start, str(match.id)))
            wanted = wanted[:CANDIDATE_LIMIT]

        # **The cache is asked before anything expensive happens**, in one call
        # for the whole screen: retrieval knows every candidate's version before
        # it needs any context, so a warm ask pays no reservation query and no
        # rating replay at all.
        held = await self._contexts.known(
            [(match.id, match.version) for match in wanted]
        )
        missing = [
            match for match in wanted if (match.id, match.version) not in held
        ]
        crowding = await self._crowding(missing, clubs)
        occupants: dict[tuple[UUID, Sport], Occupant | None] = {}

        rows: list[MatchScoringContext] = []
        fresh: list[MatchScoringContext] = []
        for match in wanted:
            known = held.get((match.id, match.version))
            if known is not None:
                rows.append(known)
                continue
            club = clubs.get(match.club_id)
            if club is None:
                # A match at a club this read cannot see could only become a
                # card naming a place it does not know. Dropped silently, the
                # way ``ArrivalRows`` is *"silently short on a stranger"*.
                continue
            category = _category(club, match)
            if category is None:
                # A category the club has retired since the match was posted.
                # Its ``Cover`` is a **required** field of every card's spine and
                # is read live off the category (ADR-0090), so there is nothing
                # honest to put there and the candidate goes.
                continue
            fresh.append(
                MatchScoringContext(
                    match_id=match.id,
                    version=match.version,
                    record=match.as_record(),
                    club=ClubFacts(
                        club_id=club.id,
                        name=club.name.value,
                        zone=club.timezone,
                        cover=category,
                        crowding=crowding[_bucket(match)],
                    ),
                    share=Money(amount=grosze(int(match.share))),
                    court_total=Money(
                        amount=grosze(int(match.share) * len(match.seats))
                    ),
                    occupants=tuple(
                        [
                            await self._occupant(occupants, seat.player_id, match.sport)
                            for seat in match.seats
                        ]
                    ),
                    counted=match.counted,
                )
            )
            rows.append(fresh[-1])
        if fresh:
            await self._contexts.remember(fresh)
        return tuple(rows)

    async def _crowding(
        self, matches: list[Match], clubs: dict[UUID, Club]
    ) -> dict[tuple[UUID, Instant, int], Ratio]:
        """How much of each club is committed, per club and per match window.

        **Computed and never defaulted**, and the asymmetry with travel time is
        the whole of it: crowding is read by the *viability* term as evidence and
        multiplies straight into the score, so a default of nothing is an empty
        club — the most flattering answer available, and exactly the fabricated
        observation ADR-0027 exists to remove.

        A **share** and not a court count, because *how many courts a club has*
        is a club fact an engine has no business scaling against: two free courts
        is plenty at a two-court club and nothing at a twenty-court one.

        Keyed on the window rather than on the match, so the eight matches a busy
        club runs at 19:00 on Tuesday cost one read between them.
        """

        out: dict[tuple[UUID, Instant, int], Ratio] = {}
        for match in matches:
            key = _bucket(match)
            if key in out:
                continue
            club = clubs.get(match.club_id)
            if club is None:
                out[key] = ratio(0, 1)
                continue
            courts = club.live_courts
            if not courts:
                # A club with no live courts is fully committed rather than
                # empty: there is nothing left to give, which is what the term
                # reads crowding for.
                out[key] = ratio(1, 1)
                continue
            window = TimeRange(
                start=match.start, end=shifted(match.start, match.duration)
            )
            taken = {
                reservation.court_id
                for reservation in await self._reservations.overlapping(
                    court_ids=[court.id for court in courts], window=window
                )
            }
            out[key] = ratio(min(len(taken), len(courts)), len(courts))
        return out

    async def _occupant(
        self,
        memo: dict[tuple[UUID, Sport], Occupant | None],
        player_id: UUID | None,
        sport: Sport,
    ) -> Occupant | None:
        """One seated player's rating, in the engines' vocabulary.

        ``None`` for an empty seat — the *seat* is what says nobody is on it, and
        an occupant there would be a reliability reading attached to nobody.
        ``UnratedPlayer`` for somebody the platform has never rated **at this
        sport**, which is an ordinary state: a player Established at tennis and
        unrated at padel is in it, and the forecast stands a Level in for her
        rather than refusing to run.

        Memoised across the whole call, because a club's Tuesday evening is
        largely the same twelve people.
        """

        if player_id is None:
            return None
        key = (player_id, sport)
        if key not in memo:
            memo[key] = await self._read(player_id, sport)
        return memo[key]

    async def _read(self, player_id: UUID, sport: Sport) -> Occupant:
        """Her rating, or the honest absence of one.

        Through Now's own ``Ratings`` port rather than the rating repository, so
        the crossing from that context's float into the engines' exact ratio
        happens in **one** place for the whole screen. Two spellings of *how a μ
        becomes a Level* is a rounding rule that can drift, in the one number the
        largest term in the fit table reads.
        """

        found = await self._ratings.occupant(player_id=player_id, sport=sport)
        if found is not None:
            return found
        return UnratedPlayer(player=PlayerRef(str(player_id)))


def _bucket(match: Match) -> tuple[UUID, Instant, int]:
    return (match.club_id, match.start, int(match.duration))


def _category(club: Club, match: Match) -> Cover | None:
    """The match's category's ``Cover``, read live rather than copied.

    The price was agreed when the match was posted and the roof is a fact about
    the evening she is walking into (ADR-0090). A category's cover never
    changes, so there is no history to resolve as of an instant.
    """

    for category in club.categories:
        if category.id == match.category_id:
            return category.cover
    return None
