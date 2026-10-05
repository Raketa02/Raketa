"""The posting grid and its slot sheet — the rules that need no I/O (#546; the
mechanics §9.1 steps 5–6; the screens A5.2–A5.3; Q77, Q92, Q93).

A member posting a game sees **two weeks, one at a time, as 7 days × 3 ranges**
— Morning 07–12, Afternoon 12–17, Evening 17–23, the ranges the overlap grid
groups hours in — and picks a court and an hour from a cell's sheet. Five rules
shape it.

**A cell's number is the poster's best fits free together with them, at one
hour** (Q92): the **best hour in its range that has a free court**, and with no
court there, the best hour of the range. Never people who overlap the poster at
different hours — four people free on a Saturday evening at four different
hours cannot play on Saturday evening, which is the overlap grid's own rule.

**The poster's week picks the hour first.** An hour they are free for beats an
hour with more fits; a range their week does not cover at all is *outside your
hours* — still counted, at its best hour regardless, and still pickable.

**A best fit is somebody the post could be dealt to then**: who it is for
(``PostedFor``) and fitting the poster — the caller's, read once — and, hour by
hour, the proposer's own *may play*: rated, wanting the kind, free for the whole
hour, no game then, a week under their cap, and the court's share within their
*most I'll pay* (with no court, there is no share to ask
about). A full game's worth is the seats besides the poster — on *Mixed pairs*,
the men and the women beside them a mixed game needs, never three of one.

**A free court is one a new card may be made at**: at one of the clubs the
pool plays at, taking new cards, before its book-by — what ``MakeProposal``
would accept. Each sheet row is one club and hour, **with its own count** (Q77),
the home club first.

**Earlier today is past**: a range whose every hour has started, with no court
still ahead in it. **Already happening** marks a cell with a rescue or a post
still filling the poster could join (Q93); which, is the sheet's.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, invariant
from app.modules.clubs.domain.court_hours import (
    CLUB_ZONE,
    hour_start,
    local_day,
    local_hour,
)
from app.modules.player_profile.domain.gender import Gender
from app.modules.player_profile.domain.weekly_hours import (
    DAY_RANGES,
    DAYS_IN_THE_GRID,
    free_for_the_hour,
)
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import Who, stand_together
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing
from app.modules.proposals.domain.proposer import (
    CourtHourOnSale,
    Member,
    PoolClubs,
    admitted,
    capped_weeks_of,
    may_play,
)

#: The posting grid's two weeks, one at a time: the first starts today.
WEEKS: Final = (1, 2)


@final
@dataclass(frozen=True, slots=True)
class GridCell:
    """One day's range, as the poster reads it."""

    day: date
    range: DayRange
    #: How many of the poster's best fits are free together with them at
    #: ``best_start``.
    fits_free: int
    #: The hour the number is read at — the best hour in the range with a free
    #: court, else the best of the range — and ``None`` when none is ahead.
    best_start: Instant | None
    court_free: bool
    #: A full game's worth of fits: the seats besides the poster.
    full_game: bool
    #: The poster's own week covers no hour of it that the number could be
    #: read at.
    outside_your_hours: bool
    #: Earlier today.
    past: bool
    #: A rescue or a post still filling the poster could join is there.
    happening: bool


@final
@dataclass(frozen=True, slots=True)
class FreeCourt:
    """One row of a sheet's *Free courts*: a club and hour where the post could
    be made, and how many fits are free then."""

    hour: CourtHourOnSale
    fits_free: int
    #: The pool's home club.
    home: bool


@final
@dataclass(frozen=True, slots=True)
class _Counted:
    start: Instant
    fits: tuple[Member, ...]
    poster_free: bool


def range_of(start: Instant) -> DayRange | None:
    """The range a court hour starting at ``start`` is in, on the club's clock —
    ``None`` for an hour outside the grid."""

    hour = local_hour(start)
    return next(
        (DayRange(name) for name, hours in DAY_RANGES.items() if hour in hours), None
    )


def open_to_join(
    proposal: Proposal,
    member: Member,
    *,
    unfit: Collection[frozenset[UUID]],
    genders: Mapping[UUID, Gender | None],
    now: Instant,
) -> bool:
    """Whether a post still filling is one this member could join from the
    sheet — *already happening here* (Q79, Q93): somebody else's post with a
    seat open, which they have not answered no to, which is for them, which
    they could be dealt then as its fits are, and whose people In they fit.
    ``unfit`` every pair among them and the people In that may not share a
    court; ``genders`` the people In's."""

    player = member.player_id
    return (
        proposal.origin is Origin.POST
        and proposal.standing_at(now) is Standing.FILLING
        and proposal.open_seats > 0
        and player not in proposal.yeses
        and player not in proposal.declined
        and admitted(proposal.posted_for, member)
        and may_play(
            member,
            proposal.kind,
            start=proposal.start,
            share_grosze=proposal.share_grosze,
            capped=capped_weeks_of(member, now=now),
        )
        and not any(frozenset((player, there)) in unfit for there in proposal.yeses)
        and stand_together(
            proposal.who,
            {**genders, player: member.gender},
            (*proposal.yeses, player),
            seats=proposal.seats,
        )
    )


@final
class PostingGrid:
    """One poster's grid at one instant: their best fits and the court hours
    the pool's clubs sell, read once, and every cell and sheet answered from
    them."""

    def __init__(
        self,
        *,
        poster: Member,
        fits: Sequence[Member],
        who: Who,
        kind: SearchMode,
        sport: Sport,
        hours: Sequence[CourtHourOnSale],
        clubs: PoolClubs,
        happening: Sequence[Instant],
        now: Instant,
    ) -> None:
        """``fits`` are the members the post is for who fit the poster, in the
        pool's order; ``hours`` what the pool's clubs sell in the sport;
        ``happening`` when each game the poster could join starts."""

        invariant(
            all(fit.player_id != poster.player_id for fit in fits),
            "the poster among their own fits",
        )
        self._poster = poster
        self._fits = tuple(fits)
        self._who = who
        self._kind = kind
        self._seats = SPORT_SPECS[sport].players
        self._clubs = clubs
        self._now = now
        self._capped = {fit.player_id: capped_weeks_of(fit, now=now) for fit in fits}
        self._hours = tuple(
            sorted(
                (
                    hour
                    for hour in hours
                    if hour.sport is sport
                    and hour.taking_new_cards
                    and now < hour.book_by
                    and clubs.rank_of(hour.club_id) is not None
                ),
                key=lambda hour: (clubs.rank_of(hour.club_id), hour.start),
            )
        )
        self._happening = tuple(happening)
        self._today = local_day(now)

    @property
    def open_seats(self) -> int:
        """The seats besides the poster: three in doubles, one in singles."""

        return self._seats - 1

    # ------------------------------------------------------------------ grid

    def days(self, week: int) -> tuple[date, ...]:
        """The seven days of week ``week`` — the first starts today."""

        invariant(week in WEEKS, f"week {week} of the posting grid")
        first = self._today + timedelta(days=DAYS_IN_THE_GRID * (week - 1))
        return tuple(first + timedelta(days=n) for n in range(DAYS_IN_THE_GRID))

    def week(self, week: int) -> tuple[GridCell, ...]:
        """Twenty-one cells, day by day and, within a day, morning first."""

        return tuple(
            self.cell(day, range_) for day in self.days(week) for range_ in DayRange
        )

    def cell(self, day: date, range_: DayRange) -> GridCell:
        courts = self._courts_in(day, range_)
        best = self._best(day, range_, courts)
        return GridCell(
            day=day,
            range=range_,
            fits_free=0 if best is None else len(best.fits),
            best_start=None if best is None else best.start,
            court_free=bool(courts),
            full_game=best is not None and self._a_full_game(best.fits),
            outside_your_hours=best is not None and not best.poster_free,
            past=not courts and not self._hours_ahead(day, range_),
            happening=any(
                local_day(start) == day and range_of(start) is range_
                for start in self._happening
            ),
        )

    # ----------------------------------------------------------------- sheet

    def fits_free_at(self, cell: GridCell) -> tuple[Member, ...]:
        """The poster's best fits free at the cell's best hour, in the pool's
        order — the sheet's *n of your best fits free then*."""

        if cell.best_start is None:
            return ()
        courts = self._courts_in(cell.day, cell.range)
        return self._count(cell.best_start, courts).fits

    def free_courts(self, day: date, range_: DayRange) -> tuple[FreeCourt, ...]:
        """Every club and hour in the cell a post could be made at, home club
        first and then by hour, each with its own count."""

        return tuple(
            FreeCourt(
                hour=hour,
                fits_free=len(self._free_at(hour.start, hour.share_grosze)),
                home=hour.club_id == self._clubs.home_club_id,
            )
            for hour in self._courts_in(day, range_)
        )

    def court_hour(self, club_id: UUID, start: Instant) -> CourtHourOnSale | None:
        """The court hour a post at this club and hour would be made at — one
        the grid offers — or ``None``."""

        return next(
            (
                hour
                for hour in self._hours
                if (hour.club_id, hour.start) == (club_id, start)
            ),
            None,
        )

    def fits_free_for(self, hour: CourtHourOnSale) -> tuple[Member, ...]:
        """The poster's best fits free at this court hour, in the pool's order."""

        return self._free_at(hour.start, hour.share_grosze)

    # --------------------------------------------------------------- reading

    def _a_full_game(self, fits: Sequence[Member]) -> bool:
        """Whether these fits can fill the seats beside the poster — on *Mixed
        pairs*, with two of each gender in all."""

        if self._who is not Who.MIXED_PAIRS:
            return len(fits) >= self.open_seats
        per_gender = self._seats // 2
        return all(
            sum(1 for fit in fits if fit.gender is gender)
            + (1 if self._poster.gender is gender else 0)
            >= per_gender
            for gender in (Gender.MAN, Gender.WOMAN)
        )

    def _courts_in(self, day: date, range_: DayRange) -> tuple[CourtHourOnSale, ...]:
        return tuple(
            hour
            for hour in self._hours
            if local_day(hour.start) == day and range_of(hour.start) is range_
        )

    def _hours_ahead(self, day: date, range_: DayRange) -> tuple[Instant, ...]:
        """Every hour of the range that has not started yet."""

        return tuple(
            start
            for start in (hour_start(day, hour) for hour in DAY_RANGES[range_.value])
            if start > self._now
        )

    def _best(
        self, day: date, range_: DayRange, courts: Sequence[CourtHourOnSale]
    ) -> _Counted | None:
        starts = (
            sorted({hour.start for hour in courts})
            if courts
            else self._hours_ahead(day, range_)
        )
        counted = [self._count(start, courts) for start in starts]
        # The first among equals is the earliest: ``max`` keeps it.
        return max(
            counted,
            key=lambda count: (count.poster_free, len(count.fits)),
            default=None,
        )

    def _count(self, start: Instant, courts: Sequence[CourtHourOnSale]) -> _Counted:
        # The cheapest court free then: a fit who can afford a court at the
        # hour is free for it.
        shares = [hour.share_grosze for hour in courts if hour.start == start]
        return _Counted(
            start=start,
            fits=self._free_at(start, min(shares) if shares else None),
            poster_free=free_for_the_hour(
                self._poster.week, start=start, zone=CLUB_ZONE
            ),
        )

    def _free_at(self, start: Instant, share_grosze: int | None) -> tuple[Member, ...]:
        return tuple(
            fit
            for fit in self._fits
            if may_play(
                fit,
                self._kind,
                start=start,
                share_grosze=share_grosze,
                capped=self._capped[fit.player_id],
            )
        )
