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

from app.engines.matchmaking import Occupant
from app.kernel import Instant, Outcome, Sport

from app.modules.now.domain.arrivals import ArrivalKey, NewClub, NewPlayer
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.funnel import MatchScoringContext
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

    async def for_player(self, player_id: UUID) -> frozenset[Sport]: ...

    async def holds(self, *, player_id: UUID, sport: Sport) -> bool:
        """Whether this player holds a rating at **one** sport.

        The same subject asked at one sport rather than at all of them, and it is
        a second method rather than a caller filtering ``for_player`` because the
        cost is not the same: a rating stream is keyed by ``(player, sport)``, so
        this is one lookup where the set is a replay of every rating she holds.
        The sport bar's busiest path is a named chip, and that path now has a
        question to ask — *is she rated here, or is she owed a door* — which it
        should not pay a full replay to answer.
        """
        ...


@runtime_checkable
class EnrolledMatches(Protocol):
    """The matches this viewer is committed to, and what each card prints.

    One port and one method, where shelves 4 and 5 took two: the split there is
    ADR-0068's cache boundary — *who is new here* is the same answer for a whole
    city and *what a card prints* is not — and there is no such boundary here.
    An enrolled strip is **one player's own matches**, so nothing about it is
    shared with anybody and there is nothing to cache; ADR-0068 deletes the
    player feed cache by name, and *"every ask pays the full funnel"* is the
    same sentence read from this side.

    **Ordered by ``start``, which the composer relies on and does not redo.**
    A chronological region whose order is fixed at composition is the whole
    point of the region: a card that moved as the player reached for it is the
    one defect it exists to avoid.

    The cost is stated rather than hidden, on the precedent ``ArrivalRows`` set:
    the rows are bounded by *this player's own matches*, which is a handful, and
    the adapter pays a reservation read per row to learn which court a match
    holds. A player who outgrows that wants a projection, and this port is where
    one lands.
    """

    async def for_player(
        self, *, player_id: UUID, now: Instant
    ) -> tuple[Enrolment, ...]:
        """Her matches, soonest first, including the ones she has left."""
        ...

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        """This one match, if this viewer is anything to it at all.

        The read behind an action off Now (ADR-0074, ADR-0086) and behind the one
        card an action hands back. It is a second method rather than the caller
        filtering ``for_player``, because filtering would read every match she
        holds to answer a question about one — on a write path, per tap.

        **Its membership is wider than the strip's by exactly one case.** A seat
        or a departure is what ``for_player`` answers; this also resolves for a
        viewer holding a **live seat claim**, who holds no seat yet (ADR-0081)
        and whose route must therefore still open and say *no*. Anybody else is
        a stranger and gets nothing — authorisation, which ADR-0074 makes the one
        place a different shape is right.
        """
        ...


@runtime_checkable
class ParkedRuns(Protocol):
    """Whether a sport's questionnaire is already part-answered and waiting.

    The one thing the door needs beyond the absence of a rating: ADR-0084 gives
    it two sentences, and which one it shows is *has she started this already*.

    A boolean and not the run itself. Now composes a code from it and could do
    nothing with an aggregate — and a port answering with one would invite a
    later session to read a transcript on the home screen's path.

    **A parked run never expires**, so this is a question about existence and
    never about freshness: the questionnaire carries its own control for walking
    back through answers (ADR-0020), so a run stopped on a tram in March is still
    the run the door reopens in August.
    """

    async def parked_at(self, *, player_id: UUID, sport: Sport) -> bool:
        """False for a player who has never started this sport's run."""
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


@runtime_checkable
class CityMatches(Protocol):
    """The matches a viewer could be shown, and everything scoring one needs.

    **Retrieval, and the whole of it.** The delta's stage ① is *index only* —
    predicates a database can answer, high recall, low precision — so this port
    takes a window and a sport filter and nothing about the viewer at all. Every
    judgement about *this* player is eligibility's and scoring's, one layer up,
    where it can be exercised without a database.

    What comes back is the **scoring context**, not the match: the club's
    saturation and the seated players' ratings are the expensive half, they are
    the same for everybody looking at the match, and ADR-0068 files them under
    ``matchId : recordVersion``. **The cache is behind this port**, which is the
    opposite of where that ADR puts the new-arrivals one — and its own line is
    why: *"the key is a fact about the viewer and the port's question is not"*
    holds there and inverts here, because this key carries nothing about the
    asker. Above the port it would mean building every context and then throwing
    it away for the copy already held.
    """

    async def contexts(
        self, *, sports: frozenset[Sport], window_from: Instant, window_to: Instant
    ) -> tuple[MatchScoringContext, ...]:
        """Contexts for every match in the window, in any order.

        Silently short on a club this read cannot see, the way ``ArrivalRows``
        is: a candidate whose venue is unknown could only become a card naming a
        place it cannot name.
        """
        ...


@runtime_checkable
class ScoringContexts(Protocol):
    """The context cache: one entry per ``matchId : recordVersion``.

    **Never stale, and that is a property of the key rather than of a policy.**
    A seat payment bumps the match's version, so the next ask files under a key
    that was never written and pays a real read. There is no TTL, no reverse
    index and no ``forget`` — the invalidation ADR-0068 asks for is the version
    already in the key.

    It is the one cache on this screen that can be *asked for the whole batch*,
    because retrieval knows every candidate's version before it needs any
    context: ``known`` is one call for a screen rather than one per card, and it
    is asked **before** anything expensive happens — a warm ask pays no
    reservation query and no rating replay at all.
    """

    async def known(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> Mapping[tuple[UUID, int], MatchScoringContext]:
        """Whatever of these is already held. Absent keys are simply missing."""
        ...

    async def remember(self, contexts: Sequence[MatchScoringContext]) -> None:
        """File each context under its own match and version."""
        ...


@runtime_checkable
class Commitments(Protocol):
    """What the viewer is already doing — the two facts eligibility reads.

    Her own matches as *identity* and as *hours*, which are two different rules:
    ``NotAlreadyMine`` keeps a match she has left off the shelf, and
    ``NoScheduleConflict`` keeps a different match at the same hour off it. A
    match she left is hers by the first and its hours are hers by the second.

    A second port beside ``EnrolledMatches`` rather than a widening of it, on the
    membership-against-row split ADR-0068 already draws twice: that one answers
    *what a card prints* and pays five contexts for it, and this one answers
    three columns. The cost is stated rather than hidden — a compose reads her
    own matches twice — and it is the cheaper of the two reads, over a set
    bounded by a player's own diary.
    """

    async def held_by(
        self, player_id: UUID
    ) -> tuple[tuple[UUID, Instant, Instant], ...]:
        """``(match_id, start, end)`` for every match she holds or has left."""
        ...


@runtime_checkable
class StandbyPlaces(Protocol):
    """Which matches this viewer is queued for. **Ships dark.**

    ``NotOnStandby`` is one of the delta's eight common rules and it needs a set
    to test against. Standby has no store anywhere in the product — the queue is
    a membership the departure cascade will create (``Raketa02/Raketa#81``,
    ``#82``) — so today every answer is empty and the rule passes for every
    candidate.

    It is a **port with an empty answer** rather than a rule left out, because
    the two are different the day the store lands: a missing rule is a screen
    suggesting a player the match she is already queued for, found by somebody
    reading the pipeline, and an empty port is one line in the composition root.
    """

    async def for_player(self, player_id: UUID) -> frozenset[UUID]:
        """Empty for every player today, and honestly so."""
        ...


@runtime_checkable
class Ratings(Protocol):
    """One player's rating at one sport, in the engines' own vocabulary.

    Distinct from ``Levels``, which answers the **card's** Level and its quiet
    marker: this answers the *engine's* ``Occupant`` — a Level, an Uncertainty
    and a Confidence arriving together or not at all — because a forecast reads
    σ and a card never does. Two shapes of one stored fact, and neither is
    derivable from the other without inventing the half it drops.
    """

    async def occupant(self, *, player_id: UUID, sport: Sport) -> Occupant | None:
        """Her rating at that sport, or nothing at all."""
        ...


@runtime_checkable
class Departures(Protocol):
    """The one write behind an action off Now, in Now's words.

    Now owns no aggregate and this does not give it one: what is behind this
    port is ``Match.depart``, which already refuses everything that has to be
    refused — a started match, a terminal one, a seat she does not hold,
    ADR-0046's lock, and a quote the live outcome has fallen below. A second
    implementation of any of them here would be a second answer to a question
    that already has one.

    It is a port of **Now's own** with its adapter in ``now/infrastructure/``,
    which is the shape ``money.Seats`` already takes over the same aggregate. The
    alternative — the composer importing ``matches.application`` — would put
    another context in Now's application layer and, worse, point the module graph
    both ways at once: ``now`` reads ``matches`` everywhere in this tree.

    **It does not commit**, and the ticket rests on that: the departure, its
    vacancy, the hold ladder's answer, both outbox rows *and* the command-log
    row close together or they do not close at all.
    """

    async def depart(
        self, *, match_id: UUID, player_id: UUID, quote: Outcome, at: Instant
    ) -> Outcome:
        """Leave, and answer the outcome she was actually quoted at.

        The answer is the aggregate's own recomputed outcome rather than the
        label that crossed the wire: equal or better applies (ADR-0033), so a
        forfeit quoted against a reversal goes through and what is recorded is
        the forfeit. That is the value the command log remembers, because a
        replay must return *what happened* and not *what was asked for*.
        """
        ...
