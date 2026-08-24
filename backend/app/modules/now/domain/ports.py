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
from app.modules.now.domain.cascade import Offer, PendingWave, Wave
from app.modules.now.domain.departure import AppliedDeparture
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

    async def one(self, match_id: UUID) -> MatchScoringContext | None:
        """The context for one named match, or nothing.

        **The single read beside the batch**, on the precedent
        ``EnrolledMatches.one`` set and for the same reason: the invitation
        cascade knows exactly which match lost a seat, and asking for a window
        of the city in order to pick one match out of it is the same query
        wearing a loop. It answers ``None`` for a match this read cannot see at
        all — an unknown id, or a club it cannot reach — which is the silence
        ``contexts`` already keeps about a venue it cannot name.

        It shares the cache with ``contexts`` rather than sitting beside it: the
        key is ``matchId : recordVersion`` either way, so a cascade running
        moments after a compose pays nothing, and a compose after a cascade pays
        nothing either.
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
    """Which matches this viewer is queued for. **The store landed.**

    ``NotOnStandby`` is one of the delta's eight common rules and it needs a set
    to test against. It shipped against an adapter that answered the empty set
    for everybody, because standby had no store anywhere in the product — the
    port was written first precisely so that the day the table arrived the
    change would be one line in the composition root rather than a rule somebody
    had to remember to add (``Raketa02/Raketa#81``). This is that day, and it
    was one line.

    It is a **read and only a read**, and the write beside it is a second port
    rather than a second method here: ``ComposeShelves`` takes this one, and a
    composer holding an object that can delete a player's queue place is a
    composer one autocomplete away from doing it.
    """

    async def for_player(self, player_id: UUID) -> frozenset[UUID]:
        """Every match she asked to be told about. Empty is the common answer."""
        ...


@runtime_checkable
class Standby(Protocol):
    """The second write behind an action off Now, in Now's words.

    ADR-0087's ``DELETE``, and the port is Now's own with its adapter in
    ``now/infrastructure/`` — the shape ``Departures`` and ``money.Seats``
    already take over the Matches context. The alternative, a composer importing
    ``matches.application``, would put another context in Now's application
    layer and point the module graph both ways at once.

    **It refuses nothing and reports nothing**, which is the whole of ADR-0087:
    *"a repeated delete of a standby place a player no longer holds is the state
    they asked for"*. There is no quote to fall, no lock, no money and no place
    to lose, so the only thing that can go wrong is a match that does not exist.

    **It does not commit.** The delete and the read that composes the answer are
    the use case's transaction, on the rule ``Departures`` already follows.
    """

    async def leave(self, *, match_id: UUID, player_id: UUID) -> None:
        """Take her off this match's queue, or leave it as it already is.

        Raises ``MatchNotFound`` for a match that does not exist, which is the
        only refusal in the act and is about the **address** rather than about
        the queue.
        """
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
    ) -> AppliedDeparture:
        """Leave, and answer the outcome she was quoted at **and the hole left**.

        The outcome is the aggregate's own recomputed one rather than the label
        that crossed the wire: equal or better applies (ADR-0033), so a forfeit
        quoted against a reversal goes through and what is recorded is the
        forfeit. That is the value the command log remembers, because a replay
        must return *what happened* and not *what was asked for*.

        The **hole** rides beside it because the invitation cascade is opened on
        it, in this same transaction: a vacancy with no cascade behind it is a
        seat nobody will ever be told about, and nothing re-reads old vacancies
        looking for the ones that were missed. Two fields and not one, on
        ADR-0033's own rule — a departure and the hole it leaves are independent
        facts, and a single value naming only the outcome would have made the
        caller derive the second from the first.
        """
        ...


@runtime_checkable
class Results(Protocol):
    """The result conversation's two writes, in Now's words.

    Now owns no aggregate and this does not give it one: behind it is
    ``Match.propose_score`` and ``Match.agree_result``, which already refuse
    everything ADR-0048 asks — a match not yet played, one past the entry
    deadline, a score on a table whose own deadline has run out, a side that has
    already had its turn, a teammate accepting a teammate, and anybody who was
    not on the court. A second implementation of any of them here would be a
    second answer to a question that already has one, and the route would then
    be free to disagree with the aggregate about who may speak.

    **Two writes and not three**, although ADR-0074 names three acts. Entering
    and countering are the same act at two moments — ADR-0048 caps *proposals per
    side* over both, and the aggregate decides which one a given score is from
    what is on the table. A client choosing between them would be holding the
    rule that tells them apart, which is the one thing ADR-0053 leaves the phone
    none of; the three booleans it *is* told are three labels over these two
    sends.

    **Neither commits**, on the departure route's rule: the score, its
    announcement and the recomposed answer close together or they do not close at
    all.
    """

    async def propose(
        self, *, match_id: UUID, player_id: UUID, sets: Sequence[tuple[int, int]],
        at: Instant,
    ) -> None:
        """Put this score on the table as her side's, whichever act that is.

        The sets cross as pairs of integers rather than as a Matches value
        object, so Now's application layer states a score in the units the wire
        carries and the adapter is the one place that knows what type Matches
        keeps them in.
        """
        ...

    async def accept(self, *, match_id: UUID, player_id: UUID, at: Instant) -> None:
        """Agree with what is on the table, from the opposing side only."""
        ...


@runtime_checkable
class StandbyQueue(Protocol):
    """Who asked to be told about **one match**. Rung 1, and the whole of it.

    The other direction of ``StandbyPlaces``, and a third port over the same
    table rather than a method on it — the split ``StandbyPlaces`` and
    ``Standby`` already make, for the same reason. ``ComposeShelves`` takes the
    viewer's read; the cascade takes this one; and neither holds an object that
    can answer the other's question, let alone delete a queue place.

    A set, because rung 1 is **fit-ordered within itself** (ADR-0061): the queue
    has no order for a list to imply, and ``joined_at`` is stored and read by
    nothing.
    """

    async def queued_for(self, match_id: UUID) -> frozenset[UUID]:
        """Everybody queued for this match. Empty is the ordinary answer."""
        ...


@runtime_checkable
class RatedPlayers(Protocol):
    """Everybody who holds a rating at one sport. **The pool's population.**

    ADR-0061's addition to the feed's filter, read from the only end it can be
    read from: *"a player is never offered a seat in a sport they hold no rating
    in"*, and the rule is *a rating exists at that sport* rather than *they
    answered that questionnaire*, because the two diverge the moment somebody
    adds a sport or is rated by playing.

    **The inverse of every other rating read in the product**, and that is why
    it is its own port. ``Ratings.occupant`` and ``RatedSports.holds`` both ask
    about a **named** player, and the rating streams are keyed ``(player,
    sport)`` precisely so those cost one lookup with no index. This asks the
    question the key cannot answer — *who* — so it reads the opening events
    rather than a stream, and the adapter is the one place that knows it.

    It answers **ids and nothing else**. A Level costs a stream replay each, and
    the ladder only needs one for a candidate that has already survived the
    cheap half of the pool filter.
    """

    async def at(self, sport: Sport) -> tuple[UUID, ...]:
        """Every player with a rating at this sport, oldest rating first."""
        ...


@runtime_checkable
class ClubRegulars(Protocol):
    """Who plays at one club often enough to be rung 5.

    ADR-0061's *"compatible players who use this club often"*, shipped as **play
    history at that club** — which is the only source the product has and is
    what the ADR names. *Often* is deliberately not a threshold here: a single
    past match at the club is what puts somebody on this rung, because the rung
    is an **ordering** and not a claim, and a cut-off invented in this file
    would be a number nobody wrote down deciding who hears about a seat.
    """

    async def at(self, *, club_id: UUID, before: Instant) -> frozenset[UUID]:
        """Everybody who has held a seat at a match at this club, before now."""
        ...


@runtime_checkable
class Offers(Protocol):
    """What the cascade wrote down: which seat reached whom, and when.

    **The store the offers region reads** (`Raketa02/Raketa#83`) and the one
    ``kernel.Viewer.offer`` is answered from. It is written here and read there,
    which is why it is a port of Now's own rather than a table in Matches: an
    offer is not a fact about the match — the match is unchanged by it — and
    ADR-0034's version column would be bumped by every dispatch if it were,
    invalidating the scoring-context cache each time somebody was told.

    It **announces nothing**, on ADR-0091's rule for the standby queue: the
    outbox exists so a support agent can explain a game somebody *paid for*, and
    an offer moves no money and confers no place. The push queue reads this
    table because ADR-0065 ranks *"the whole live set every dispatch"*, which is
    a query and not a subscription.
    """

    async def record(self, offers: Sequence[Offer]) -> None:
        """Write these offers. **Silent about one already made.**

        A player already offered *this* hole is left exactly as she was, rather
        than told again with a new instant — that is the whole of ADR-0061's
        *"a lapse resumes them and nobody is told twice"*, and it is answered by
        the store having nothing to do rather than by a caller remembering to
        filter. It does not commit, on ``Departures``'s rule.
        """
        ...

    async def offered_for(self, *, vacancy_id: UUID) -> frozenset[UUID]:
        """Who has already been told about this hole."""
        ...

    async def held_by(self, player_id: UUID) -> tuple[Offer, ...]:
        """Every seat put in front of this player, newest first.

        **The offers region's own read** (`Raketa02/Raketa#83`), and the seed
        catalog is its first caller — the shape ``JoinStandby`` already has.
        What it answers is the whole offer and not a set of ids, because a card
        prints the price she was quoted and the push words itself differently
        for a seat she **asked** about (ADR-0065); both are on the row.

        It answers offers and never *live* offers. Whether the seat is still
        there is a question about the **match**, asked at the instant the screen
        is composed — a store that filtered would be a second reading of the
        record, and it would answer differently a second later.
        """
        ...

    async def reached_on(self, *, match_id: UUID) -> frozenset[UUID]:
        """Who has been told about **any** hole in this match.

        Rung 3, and the reason an offer is filed under its vacancy as well as
        its match: *offered an earlier vacancy on this match and did not get it*
        is a comparison of holes, and the caller subtracts this hole's own
        offers from this answer.
        """
        ...


@runtime_checkable
class CascadeWaves(Protocol):
    """The cascade's own queue: two rows per hole, and when each may run.

    **Its own queue and not the match's schedule**, which is the same line
    `Raketa02/Raketa#84` draws for the push sends and it is drawn for a stronger
    reason here. ``next_wake`` is computed by the kernel from the record on
    every write (ADR-0076), and a dispatch is not a boundary the ladder reads —
    nothing about the match resolves differently at vacancy + 10 minutes. Adding
    one would put a threshold in the timekeeper, which ADR-0076 forbids by name
    and ``tests/unit/test_timekeeper_holds_no_thresholds.py`` reddens on.

    **Two rows per hole and no row per candidate.** That is ADR-0061's
    all-at-once shape: an eligible set computed once, two dispatch jobs,
    first-to-accept wins, and nothing to reconcile when the seat fills
    mid-walk.

    Nothing here commits: opening the waves belongs to the transaction that
    wrote the departure, and a dispatch belongs to its own.
    """

    async def open(self, waves: Sequence[PendingWave]) -> None:
        """Put these dispatches on the queue. Idempotent per ``(hole, wave)``."""
        ...

    async def due(self, *, now: Instant, limit: int) -> tuple[PendingWave, ...]:
        """Dispatches whose moment has come and which have not run, oldest first."""
        ...

    async def dispatched(
        self, *, vacancy_id: UUID, wave: Wave, at: Instant
    ) -> None:
        """Mark one dispatch done. A dispatch that reached nobody is still done."""
        ...

    async def bring_forward(
        self, *, vacancy_id: UUID, wave: Wave, to: Instant
    ) -> None:
        """Pull a pending dispatch earlier, never later.

        ADR-0061's *"an empty rung is skipped instantly, so the head start is
        not paid for an empty queue"*: a first dispatch that reached nobody has
        bought nothing, so the second stops waiting for it. Never later, because
        the only thing that may move a dispatch back is the quiet hours, and
        those were applied when the hole opened.
        """
        ...
