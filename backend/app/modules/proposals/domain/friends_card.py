"""The friends card — the rules that need no I/O (#750; ``docs/adr/0202`` §5;
the friends mechanics §7.3–§7.6).

**A fixed line-up, and every court it could take.** On a group's Friends tab
the reader seats friends beside them — three in doubles, one in singles — and
Rakieta answers the card: the sides, how even they are, and a court. Nothing is
dealt and nothing is recorded: it is the deck's card for people who chose each
other, built from **the deck's own parts** and no second scoring.

- **The sides** are the deck's arrangements of the line-up, the reader on their
  own side, and the deck's ``evenest`` choice among them — or **the sides sent**
  after a swap, which must be one of those ways to stand. In doubles a way to
  stand is named by the reader's partner; singles stands one way.
- **The courts** are the court source's own (``PoolClubs.offered``,
  ``docs/adr/0202`` §7): an official group's club at every hour it has a free
  court, another club only where it has none, marked so. Every free court is a
  row, **soonest first, the home club first within an hour, and the club's own
  order within a club** — the first court of an hour is the one a booking then
  is given. Each row says who of the line-up is free for the whole hour and who
  is **busy** — outside their weekly hours, never anything else.
- **An hour where one of them already has a game is left out** (call 5). A week
  whose games one of them has all booked is not: their Accept is refused then,
  with a sentence (§8.4), and the send is the sender's own week's to refuse
  (#751). Being busy is not either: friends who arrange it themselves are not
  stopped (Q36).
- **The court proposed** is the soonest row where everybody is free; failing
  that, the soonest where most of them are; failing a row at all, none.

**What does not apply** (call 10): the level window, the kind's tolerance,
gender preferences, a Play intent, *most I'll pay* — friends choose each other,
and the sender sees the price. Blocks and a level in the sport are the reads'.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import SPORT_SPECS, Instant, Sport, invariant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.player_profile.domain.weekly_hours import free_for_the_hour
from app.modules.proposals.domain.deck import (
    DECK_HORIZON,
    CardForecast,
    Sides,
    arrangements,
    evenest,
    hour_taken,
)
from app.modules.proposals.domain.errors import SidesNotOfTheLineUp, WrongLineUpSize
from app.modules.proposals.domain.proposer import (
    CourtHourOnSale,
    CourtOnSale,
    Member,
    PoolClubs,
)

#: How far ahead the card and *Find a court* look: the deck's horizon.
HORIZON = DECK_HORIZON


# --------------------------------------------------------------------------- #
# The line-up
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class LineUp:
    """The reader and the friends they seated, in the order sent."""

    reader: UUID
    friends: tuple[UUID, ...]
    sport: Sport

    @property
    def everybody(self) -> tuple[UUID, ...]:
        return (self.reader, *self.friends)

    @property
    def seats_per_side(self) -> int:
        return SPORT_SPECS[self.sport].players // 2


def friends_seated_in(sport: Sport) -> int:
    """The friends a game of ``sport`` seats beside the sender: three in
    doubles, one in singles."""

    return SPORT_SPECS[sport].players - 1


def line_up_of(reader: UUID, friends: Sequence[UUID], *, sport: Sport) -> LineUp:
    """The line-up, refused unless it is exactly the friends the sport seats,
    each once and never the reader."""

    seats = friends_seated_in(sport)
    if len(friends) != seats or len(set(friends)) != seats or reader in friends:
        raise WrongLineUpSize(friends=seats)
    return LineUp(reader=reader, friends=tuple(friends), sport=sport)


# --------------------------------------------------------------------------- #
# The sides
# --------------------------------------------------------------------------- #


def ways_to_stand(line_up: LineUp) -> tuple[Sides, ...]:
    """Every way the line-up can stand, the reader on their own side — the
    deck's arrangements, each friend as the partner in the order sent."""

    return arrangements(
        line_up.reader, line_up.friends, seats_per_side=line_up.seats_per_side
    )


def the_sides(
    line_up: LineUp,
    options: Sequence[Sides],
    forecasts: Sequence[CardForecast | None],
    *,
    partner: UUID | None,
) -> tuple[Sides, CardForecast | None]:
    """The sides the card draws and their forecast: the evenest of ``options``
    — the first among equals — or, with ``partner`` sent, the way to stand with
    them beside the reader. ``forecasts`` one per option, in their order."""

    if partner is None:
        return evenest(options, forecasts)
    for option, forecast in zip(options, forecasts, strict=True):
        if option.yours == (line_up.reader, partner):
            return option, forecast
    raise SidesNotOfTheLineUp()


# --------------------------------------------------------------------------- #
# The courts
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class CourtForFriends:
    """One row of *Find a court*: a club's court at an hour, and who of the
    line-up is free then."""

    club_id: UUID
    court: CourtOnSale
    start: Instant
    share_grosze: int
    #: Another club's court, offered because the home club has none free then
    #: — *Ogrody 33 is full at 10:00*.
    home_club_full: bool
    #: Of the line-up, in its order: free for the whole hour by their weekly
    #: hours, and the rest — *Ania busy*.
    free: tuple[UUID, ...]
    busy: tuple[UUID, ...]


def courts_for(
    people: Sequence[Member],
    hours: Iterable[CourtHourOnSale],
    clubs: PoolClubs,
    *,
    sport: Sport,
    now: Instant,
) -> tuple[CourtForFriends, ...]:
    """Every court ``people`` — the line-up, in its order — could take from now
    to the horizon under the pool's court rule: soonest first, the home club
    first within an hour, each club's courts in its own order. An hour where
    one of them has a game is left out."""

    end = now + HORIZON
    offered = sorted(
        (
            hour
            for hour in clubs.offered(hours, now=now)
            if hour.sport is sport and hour.start < end
        ),
        key=lambda hour: (hour.start, clubs.rank_of(hour.club_id)),
    )
    found: list[CourtForFriends] = []
    for hour in offered:
        if any(hour_taken(hour.start, person.booked) for person in people):
            continue
        invariant(bool(hour.free), f"the courts at {hour.start} unnamed")
        free = tuple(
            person.player_id
            for person in people
            if free_for_the_hour(person.week, start=hour.start, zone=CLUB_ZONE)
        )
        busy = tuple(
            person.player_id for person in people if person.player_id not in free
        )
        found.extend(
            CourtForFriends(
                club_id=hour.club_id,
                court=court,
                start=hour.start,
                share_grosze=hour.share_grosze,
                home_club_full=clubs.because_home_is_full(hour),
                free=free,
                busy=busy,
            )
            for court in hour.free
        )
    return tuple(found)


def proposed_court(courts: Sequence[CourtForFriends]) -> CourtForFriends | None:
    """The court the card proposes among ``courts``, in ``courts_for``'s order:
    the first where everybody is free, failing that the first where most of
    them are — ``None`` with no court at all."""

    # ``max`` keeps the first among equals, which is the soonest.
    return max(courts, key=lambda row: len(row.free), default=None)


def court_at(
    courts: Sequence[CourtForFriends], court_id: UUID, start: Instant
) -> CourtForFriends | None:
    """The row for this court at this hour — one the list offers — or
    ``None``."""

    return next(
        (row for row in courts if (row.court.court_id, row.start) == (court_id, start)),
        None,
    )
