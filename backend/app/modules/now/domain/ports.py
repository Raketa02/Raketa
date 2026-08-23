"""What composing Now needs from the rest of the system.

Now is a **read**: it owns no aggregate, writes nothing and stores nothing. What
it owns is the composition — which regions exist, in what order, and what a card
carries — and everything it composes *from* belongs to another context.

That is exactly what makes the ports load-bearing here rather than ceremonial. A
use case reaching into ``MatchRepository`` or ``SkillRatingRepository`` directly
would put another context's vocabulary in the composer's constructor, and the
composer would then have to be changed every time that context reshaped a read it
never asked for. A port states what Now needs in Now's words; the adapter beside
it is the one place that knows whose question it really is.
"""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport

from app.modules.now.domain.arrivals import ArrivalKey, NewClub, NewPlayer
from app.modules.now.domain.screen import Level


@runtime_checkable
class RatedSports(Protocol):
    """Which sports a player holds a rating at.

    The definition of ``all`` on the sport bar, and it is a **rating** rather than
    a declaration on purpose: the sports picker persists nothing, so a rating is
    the only durable record that a player plays a sport at all. A shelf called
    *Best fit for you* filtered by ``all`` is then a claim about her and not about
    inventory.

    Returns a set rather than a list: nothing downstream reads an order out of it,
    and a list would invite one.
    """

    async def for_player(self, player_id: UUID) -> frozenset[Sport]:
        ...


@runtime_checkable
class NewArrivals(Protocol):
    """Who arrived recently — **the set**, and nothing a card prints.

    Split from ``ArrivalRows`` on ADR-0068's own line: the *membership* of these
    two shelves is shared by everybody in a city looking at one sport and can be
    cached, where the *row* is ordered per viewer and cannot. Two ports rather
    than four methods on one, because that is what makes the split structural:
    the cache below stores what this port returns, and what this port returns is
    identifiers.

    Both answers are ordered newest first so that a cached set is reproducible,
    but nothing downstream depends on that order — the shelf's order is computed
    from the rows, where the facts it sorts on actually are.
    """

    async def player_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        """Players who registered at or after ``since`` and are rated at ``sport``.

        The rating is a **fact filter** and not a quality one, the same rule the
        cascade's pool uses: a badminton-only player has no Level at squash, so
        putting her on a squash shelf would print a number the platform imputed
        rather than one it holds.
        """
        ...

    async def club_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        """Clubs that registered at or after ``since`` and sell ``sport``.

        The sport filter applies to every shelf, shelves 4 and 5 included, so a
        padel chip never surfaces a club with only squash courts.
        """
        ...


@runtime_checkable
class ArrivalRows(Protocol):
    """What a person card and a club card print — **the row**, never cached.

    Kept out of the cache by construction rather than by discipline: the store
    below holds ``tuple[UUID, ...]``, so a row could not be put in it if somebody
    wanted to. A nickname or a club's name changing has to reach the next screen,
    and fifteen minutes of a renamed club is fifteen minutes of a player being
    told about a venue that no longer goes by that name.
    """

    async def players(self, *, player_ids: Sequence[UUID]) -> tuple[NewPlayer, ...]:
        """The rows for these players, in any order, silently short on a stranger."""
        ...

    async def clubs(self, *, club_ids: Sequence[UUID]) -> tuple[NewClub, ...]:
        """The rows for these clubs, in any order, silently short on a stranger."""
        ...


@runtime_checkable
class Levels(Protocol):
    """Each player's Level at one sport, and whether a questionnaire made it.

    Asked of the viewer and of the candidates through the same method, because it
    is the same question: the shelf's whole order is one subtraction between two
    answers, and two ways of getting a Level is how the two sides of a
    subtraction come to disagree.
    """

    async def at(
        self, *, sport: Sport, players: Sequence[UUID]
    ) -> Mapping[UUID, Level]:
        """Absent for a player who holds no rating at that sport — never a zero."""
        ...


@runtime_checkable
class ArrivalSets(Protocol):
    """The new-arrivals cache: a set of ids under a key, for fifteen minutes.

    **There is no way to invalidate one**, and that absence is the decision
    (ADR-0068). The shelves' own clocks are 30 and 60 **days**; a quarter of an
    hour of lag is invisible against that, and a cache with no invalidation path
    is the one shape that cannot go wrong. A method to clear an entry is a method
    somebody eventually calls from a write, and then this is a second thing to
    keep in step with the truth.

    The value type is what keeps the row out. ``tuple[UUID, ...]`` cannot hold a
    nickname, so *the set and not the row* is a type error rather than a rule.
    """

    async def get(self, key: ArrivalKey) -> tuple[UUID, ...] | None:
        """The stored set, or nothing when it was never stored or has expired."""
        ...

    async def put(self, key: ArrivalKey, ids: tuple[UUID, ...]) -> None:
        """Store a set under a key, replacing whatever was there."""
        ...
