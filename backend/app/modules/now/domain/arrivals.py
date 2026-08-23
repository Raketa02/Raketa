"""The two shelves that are not matches: who arrived, and in what order.

Shelves 4 and 5 are the only part of Now that does **not** run through the ranked
funnel. They answer *is anything happening here at all* — the question a player
in a thin city asks first — and they answer it with people and venues rather than
with matches, which is why ADR-0051 calls them the product's whole discovery
story once exploration was dropped.

**Their membership is shared and their order is not.** ADR-0068 splits them along
exactly that line: *New on Raketa* is the same set of people for everybody in a
city looking at one sport, so the set is cached; the row it becomes is ordered by
closeness to **this** viewer's Level, so the row is not. Everything in this
module is the half that can be written down — the two windows, the two caps, the
two comparators, and the key the set is filed under. Nothing here reads a clock
or a repository.

**Neither shelf has a floor**, and that is the difference between them and the
ranked shelves above. A floor is a claim about quality; these two claim only
recency, and there is no such thing as a player who is insufficiently new.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, final
from uuid import UUID

from app.kernel import MINUTES_PER_DAY, Instant, Minutes, Sport, minutes

from app.modules.now.domain.screen import Level

#: Thirty days of new players and sixty days of new clubs, as **elapsed** time
#: rather than calendar days. A player who joined on the 31st of March is not
#: made new again by April having thirty days in it.
#:
#: Ranking-layer policy and deliberately not a kernel constant: ADR-0027 puts
#: caps, order and cache policy outside the engines, and neither of these is a
#: calendar fact several contexts read — no aggregate anywhere is allowed to
#: behave differently because a player is twenty-nine days old.
NEW_PLAYER_WINDOW: Minutes = minutes(30 * MINUTES_PER_DAY)
NEW_CLUB_WINDOW: Minutes = minutes(60 * MINUTES_PER_DAY)

#: ADR-0068 cut these from 20 and 10, and the reason is worth keeping beside the
#: numbers: at 320pt a shelf card is nearly full width, so card 10 is nine swipes
#: away, and every shelf ends in a tail card into Find — the overflow has
#: somewhere to go. *New on Raketa* falls furthest because its cards are the
#: inert ones, and twenty untappable faces was the largest block of payload on
#: the screen.
NEW_PLAYERS_CAP = 8
NEW_CLUBS_CAP = 6

#: How long a shared set stays good for. Fifteen minutes against shelf clocks of
#: thirty and sixty days is lag nobody can perceive, which is what buys the
#: right to have no invalidation path at all.
ARRIVAL_SET_TTL: Minutes = minutes(15)


class ArrivalKind(Enum):
    """Which of the two sets a cache entry holds.

    A plain ``Enum`` and not a ``str`` one, because unlike everything in
    ``vocabulary.py`` this **crosses no wire**: it is the third component of a
    cache key and no client has ever seen it.
    """

    PLAYERS = "players"
    CLUBS = "clubs"


#: What the city component reads as when the platform holds no city for the
#: viewer. It is a real state today rather than a defensive branch: ADR-0063
#: makes *where you play* a declared fact about the player, and no context stores
#: one (#102). The component stays in the key rather than being dropped until it
#: has a source, because a key that gains a component later is a key whose old
#: entries silently answer the wrong city for fifteen minutes.
CITY_UNKNOWN = "?"


@final
@dataclass(frozen=True)
class ArrivalKey:
    """``city : sport : kind`` — what a shared set is filed under.

    **The city is in the key and has no source yet.** One city cannot be served
    another city's new arrivals, and that is true whether or not the field that
    would say so exists — so the key is written for the fact rather than for
    today's data, and ``CITY_UNKNOWN`` is what a viewer whose city nobody stores
    resolves to. The day #102 lands, this key needs no change and its entries
    partition on their own.

    **The sport is in the key because the sport filter applies to every shelf**,
    shelves 4 and 5 included. A padel chip must not surface a club that has only
    squash courts, and ``all`` resolving to two sports is two lookups whose
    results are merged — which is why the key is per sport rather than per
    filter.
    """

    city: str | None
    sport: Sport
    kind: ArrivalKind

    @property
    def key(self) -> str:
        """The flat form, for a store that holds strings rather than objects."""

        city = self.city if self.city else CITY_UNKNOWN
        return f"{city}:{self.sport.value}:{self.kind.value}"


@final
@dataclass(frozen=True)
class NewPlayer:
    """What the platform knows about a newly arrived player, before ordering.

    ``joined_at`` never reaches a card. It is here because the shelf's fallback
    order is *newest first*, and an order computed from a fact the row does not
    carry is an order nothing can check.
    """

    player_id: UUID
    nickname: str
    joined_at: Instant


@final
@dataclass(frozen=True)
class NewClub:
    """A newly registered club, and how far away it is when that is knowable.

    ``distance_km`` is absent for every viewer today, and that is the modelled
    answer rather than a gap: the glossary's **Distance anchor** is optional, and
    *precision follows the anchor* — with only a city there is no distance at
    all. It is a fact about what the platform knows and never a zero.
    """

    club_id: UUID
    name: str
    joined_at: Instant
    distance_km: int | None = None


@final
@dataclass(frozen=True)
class Candidate:
    """A new player, the Level that put her on the shelf, and how close it is.

    ``distance`` is the absolute gap between her Level and the viewer's **at the
    same sport**, and it is ``None`` when the viewer holds no rating there —
    which is an ordinary state, not an error: a player who taps a sport she has
    never been rated at still gets this shelf beneath her door into that
    questionnaire.
    """

    player: NewPlayer
    level: Level
    distance: float | None

    def closer_than(self, other: "Candidate") -> bool:
        """Whether this pairing is the one to keep when a player has two.

        ``all`` resolves to every sport the viewer is rated at, so one player can
        arrive on this shelf twice — once per shared sport. She is one card and
        prints one Level, so the pairing kept is the closest one, and a pairing
        the viewer cannot be compared against loses to any that she can.
        """

        if other.distance is None:
            return self.distance is not None
        return self.distance is not None and self.distance < other.distance


def by_closeness(candidates: Iterable[Candidate]) -> tuple[Candidate, ...]:
    """Closest Level first, and **never** by Level descending.

    ADR-0051 fixes the order and the delta gives the reason in four words: the
    shelf is about people she could play. Ordering by Level descending would make
    a shelf that says *new here* answer *best here* instead, which is a
    leaderboard — and a leaderboard is the one shape a discovery shelf must not
    be.

    Nobody is dropped for being far. There is no floor on this shelf, so a viewer
    the platform cannot compare anybody against still gets a shelf: those fall to
    the back, newest first, rather than out.
    """

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.distance is None,
                candidate.distance if candidate.distance is not None else 0.0,
                -candidate.player.joined_at.timestamp(),
                candidate.player.nickname,
            ),
        )
    )


def by_arrival(clubs: Iterable[NewClub]) -> tuple[NewClub, ...]:
    """Newest first, with distance breaking ties.

    ADR-0068's rule and its reason: the shelf's title is its claim, and ordering
    by distance would make a shelf that says *this is new* answer *this is near*.
    ADR-0064 forbids a radius **excluding** anything on Now; newest-first excludes
    nothing, so the two rules do not collide.

    A club whose distance is unknown sorts after one whose distance is known,
    within a tie — absent is not nearest. The last key is the club's **name** and
    not its id, for the reason ``ClubRepository.find_all`` already gives: a
    creation stamp is a server default that every club written in one transaction
    shares, so a tie broken on a random uuid is an order that changes between
    runs.
    """

    return tuple(
        sorted(
            clubs,
            key=lambda club: (
                -club.joined_at.timestamp(),
                club.distance_km is None,
                club.distance_km if club.distance_km is not None else 0,
                club.name,
            ),
        )
    )
