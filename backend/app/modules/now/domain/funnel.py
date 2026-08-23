"""The ranked funnel: retrieve → eligibility → score → floor → order → diversity → cap.

Shelves 1 and 2 are the only two on Now that are *ranked*, and everything in this
module is the half of that ranking which can be written down without a clock, a
repository or an engine: what disqualifies a candidate, what order the survivors
are in, what a shelf is allowed to keep, and the one pass that may reorder them.

**Two shelves, one funnel.** ADR-0051 gives them different floors and different
caps and the *same* pipeline, because the only thing that separates them is one
eligibility rule — ``HasFreeSeat`` against ``IsFull`` — and two constants. The
spec delta's own finding is why they may never be merged into one ordered list:
a full match **outranks the joinable version of itself**, so a single list would
be topped by matches nobody can join.

**Eligibility is exhaustive and never short-circuited.** ``exclusions`` returns
the set of rules a candidate *failed*, not a boolean, so nothing here can be
written as a chain of ``and``s that stops at the first ``False``. That is the
spec's operational argument made structural: *"nine candidates, seven of them
already full"* is a different story from *"nine candidates, seven of them too
far"*, and a short-circuit throws the difference away. ``WithinTravelCeiling`` is
in **neither** shelf's rule set — travel is a weight-8 term that never excludes
at any distance — and ``!m.forced`` is not a rule, because ``forced`` was the
prototype's demo hatch.

**``FEED_ORDER`` is the total base order and every later pass is a named delta
over it.** ``[desc(fit), asc(start), asc(dist), asc(id)]``, with the fourth
comparator load-bearing rather than decorative: without a guaranteed-total final
key the order falls back on retrieval order, which is the query plan, and two
identical requests reshuffle the shelf under the player's thumb.

**Diversity may reorder and may never shorten.** The prototype's
``MaxPerClubHour`` *dropped* a blocked candidate and returned fewer than the cap
with cards still waiting, which the delta calls a defect by name. This one
**defers**: a blocked candidate goes to the back of the queue rather than out of
it, so the pass is a permutation and the cap is the only thing that ever removes
a card.

**Nothing here is random.** No seed, no draw, nothing recorded for replay —
exploration was dropped and discovery is shelves 4 and 5 (ADR-0051).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence, final
from uuid import UUID

from app.engines.matchmaking import Occupant
from app.kernel import (
    Cover,
    Instant,
    MatchRecord,
    Ratio,
    Sport,
    Zone,
    deadlines,
    invariant,
    is_full,
    is_terminal,
    match_end,
)

from app.modules.now.domain.screen import Fit, Money, Shelf
from app.modules.now.domain.vocabulary import ShelfCode

#: How far ahead retrieval looks. A ranking-layer policy and deliberately not a
#: kernel constant, on the precedent ``NEW_PLAYER_WINDOW`` set: no aggregate
#: anywhere behaves differently because a match is thirty-one days out.
#:
#: **Thirty days, and the number is bounded from below by when a match is
#: posted.** The seeded world posts one a *fortnight* before it is played
#: (``app/seeds/matches.py``'s ``POSTED``), so a fourteen-day horizon would make
#: a match invisible on the day it goes up — the one day its club most wants it
#: seen. That was this constant's first value, and running the seeds is what
#: found it: the whole demo week sat outside the window.
#:
#: It is still a *suggestion* horizon and not the whole table. A match five
#: months away is a real match and a bad recommendation, and the retrieval's own
#: specification asks for high recall against an index — *"a predicate that
#: occasionally drops a good match is worse than one that returns 50 extra
#: rows"* — with ``CANDIDATE_LIMIT`` below as the actual bound on cost.
CANDIDATE_HORIZON_DAYS = 30

#: The safety valve on retrieval, and **not** a product decision: it exists so a
#: misconfigured filter cannot pull a city into memory. It sits far above what
#: survives eligibility on any realistic screen, which is what makes reaching it
#: a signal rather than a routine truncation.
CANDIDATE_LIMIT = 300

#: The floors. 70 on the joinable shelf and 80 on the waitlist shelf, and the
#: gap is the whole of ADR-0051's argument: asking somebody to **wait** for a
#: match is a bigger ask than asking her to join one, so it has to be genuinely
#: good or the shelf teaches her to scroll past it.
BEST_FIT_FLOOR = 70
FULL_FLOOR = 80

#: The caps. ADR-0085 cut shelf 1 from 10 and holds shelf 2 at 3, which puts the
#: fullest realistic screen at **23 cards across four lanes** — the number both
#: the payload ceiling and the latency gate are measured against.
BEST_FIT_CAP = 6
FULL_CAP = 3

#: How many cards from one club in one hour may sit next to each other before
#: the rest are deferred. The prototype's number, kept; what changed is that
#: being over quota now costs a card its **place** and never its seat.
MAX_PER_CLUB_HOUR = 2

#: What the badge is clamped to at display time. The engine keeps its true
#: 0–100 range and that value ranks the list; the pill never prints 8 and never
#: prints 100, because *a score of 3 is not more useful than a score of 20 —
#: both mean no*, and certainty is never warranted (ADR-0037). It is the same
#: rule the rating context already holds for Confidence.
BADGE_FLOOR = 20
BADGE_CEILING = 99


class Lane(Enum):
    """Which of the two ranked shelves a funnel run is for.

    Two members and not a boolean: ``OPEN`` and ``FULL`` name the *shelf*, and
    the seat rule, the floor and the cap all read off it. A boolean called
    ``full`` would put the shelf's identity inside one of its three consequences.
    """

    OPEN = "open"
    FULL = "full"


class Exclusion(Enum):
    """Why one candidate did not reach a shelf. **Every rule, every candidate.**

    The values are the rule names from the delta's own list, spelled as it
    spells them, so the set here and the set there can be compared by reading.
    ``WithinTravelCeiling`` is absent on purpose and asserted absent.

    This is a diagnosis vocabulary and **crosses no wire** — a plain ``Enum``
    rather than a ``str`` one, like ``ArrivalKind``: no client has ever seen a
    reason a card was not shown, and *"seven of them already full"* is an
    operational sentence rather than a player's.
    """

    NOT_ALREADY_MINE = "notAlreadyMine"
    STARTS_IN_FUTURE = "startsInFuture"
    BEFORE_JOIN_CUTOFF = "beforeJoinCutoff"
    NOT_CANCELLED = "notCancelled"
    SPORT_MATCHES_FILTER = "sportMatchesFilter"
    NO_SCHEDULE_CONFLICT = "noScheduleConflict"
    NOT_SUPPRESSED = "notSuppressed"
    NOT_ON_STANDBY = "notOnStandby"
    HAS_FREE_SEAT = "hasFreeSeat"
    IS_FULL = "isFull"


#: The rules both shelves share, in the delta's order. The lane rule —
#: ``HAS_FREE_SEAT`` or ``IS_FULL`` — is the only difference between the two
#: sets, and it is appended rather than listed twice.
COMMON_RULES: tuple[Exclusion, ...] = (
    Exclusion.NOT_ALREADY_MINE,
    Exclusion.STARTS_IN_FUTURE,
    Exclusion.BEFORE_JOIN_CUTOFF,
    Exclusion.NOT_CANCELLED,
    Exclusion.SPORT_MATCHES_FILTER,
    Exclusion.NO_SCHEDULE_CONFLICT,
    Exclusion.NOT_SUPPRESSED,
    Exclusion.NOT_ON_STANDBY,
)

#: Which seat rule each shelf adds. A total mapping over ``Lane``, asserted
#: exhaustive at module load, so a third shelf cannot be added without saying
#: what it does about seats.
LANE_RULE: dict[Lane, Exclusion] = {
    Lane.OPEN: Exclusion.HAS_FREE_SEAT,
    Lane.FULL: Exclusion.IS_FULL,
}

invariant(set(LANE_RULE) == set(Lane), "a lane with no seat rule")


def rules_for(lane: Lane) -> tuple[Exclusion, ...]:
    """Every rule this shelf evaluates, in order. Never a subset of itself."""

    return (*COMMON_RULES, LANE_RULE[lane])


@final
@dataclass(frozen=True)
class ClubFacts:
    """The club, as much of it as ranking a match needs — and no viewer in it.

    ``crowding`` is the club's saturation at the time the match starts, in 0..1,
    and it is here rather than on the match because every match at that club and
    that hour shares it. It is the one **evidence** number on this value that a
    default would fabricate: an empty club is the most flattering answer
    available, which is the observation ADR-0027 exists to remove.

    ``distance`` is deliberately **not** here. How far away a club is, is a fact
    about a club *and a viewer* — ``ClubSnapshot`` says so in as many words —
    and a viewer-relative number inside a value cached across viewers is the one
    mistake this split exists to make unreachable.
    """

    club_id: UUID
    name: str
    zone: Zone
    cover: Cover
    crowding: Ratio


@final
@dataclass(frozen=True)
class MatchScoringContext:
    """One match, as everybody looking at it sees it. **The cached unit.**

    ADR-0068's cache, keyed ``matchId : recordVersion`` and therefore *never
    stale*: a seat payment bumps the version and the next ask misses. There is
    no TTL, no reverse index and no invalidation hook, because the key **is**
    the version — the same property the new-arrivals cache buys with fifteen
    minutes of lag, bought here for nothing.

    What is in it is exactly what is expensive and viewer-independent: the
    club's saturation, which is a window query, and the seated players' ratings,
    which are a stream replay each. What is *not* in it is everything the viewer
    supplies — her own rating, how far she would travel, whether the match
    counts for her ladder — because a viewer-relative field on a shared value is
    an answer to somebody else's question with this viewer's name on it.

    ``occupants`` is one entry per seat, in the seats' fixed order, ``None``
    where nobody is on it. It parallels ``record.seats``, which carries the
    commitment state and never a person, so the two are read together and
    neither can drift: an occupant on a seat the record says is empty is a
    caller's bug the snapshot refuses at the door.
    """

    match_id: UUID
    version: int
    record: MatchRecord
    club: ClubFacts
    share: Money
    court_total: Money
    occupants: tuple[Occupant | None, ...]

    #: Whether the match counts towards ratings and ladders. On the aggregate
    #: rather than on ``MatchRecord``, because no rung of the situation ladder
    #: reads it — so it arrives here beside the record rather than inside it.
    counted: bool = True


@final
@dataclass(frozen=True)
class Viewer:
    """What the funnel needs about the person asking, and nothing else.

    ``mine`` and ``busy`` are two readings of one fact — her own matches — kept
    apart because they answer different rules: ``NotAlreadyMine`` is about
    identity and ``NoScheduleConflict`` is about the clock, and a match she left
    is hers by the first rule while its hours are still hers by the second.

    ``rating`` is her Occupant at the sport being ranked, absent when she holds
    none. The badge is withheld for such a viewer (ADR-0037) and the score still
    ranks her list — *"only the claim is withheld"*.
    """

    player_id: UUID
    mine: frozenset[UUID] = frozenset()
    busy: tuple[tuple[Instant, Instant], ...] = ()
    on_standby: frozenset[UUID] = frozenset()


def exclusions(
    context: MatchScoringContext,
    *,
    viewer: Viewer,
    sports: frozenset[Sport],
    lane: Lane,
    now: Instant,
) -> frozenset[Exclusion]:
    """Every rule this candidate failed. Empty means eligible.

    **All of them are evaluated.** The dictionary below is built whole before
    anything is filtered out of it, which is what makes *"do not short-circuit"*
    a property of the shape rather than a comment somebody has to keep true. A
    caller wanting a histogram gets one for free; a caller wanting a boolean
    asks whether the set is empty.
    """

    record = context.record
    free_seat = not is_full(record)
    verdicts: dict[Exclusion, bool] = {
        Exclusion.NOT_ALREADY_MINE: context.match_id not in viewer.mine,
        Exclusion.STARTS_IN_FUTURE: record.start > now,
        Exclusion.BEFORE_JOIN_CUTOFF: now < deadlines(record).join_cut,
        # The four cancellations, read through the kernel rather than off the
        # five booleans: a second reading of them here would be a second ladder
        # over the record, which ADR-0040 exists to refuse.
        Exclusion.NOT_CANCELLED: not is_terminal(record),
        Exclusion.SPORT_MATCHES_FILTER: record.sport in sports,
        Exclusion.NO_SCHEDULE_CONFLICT: not _clashes(context, viewer.busy),
        # The v2 slot, deliberately empty at launch. Impression capping,
        # dismissals and *stop showing me this club* all land here, and
        # declaring it now means adding them later is one rule rather than a
        # refactor of the pipeline. It is **evaluated** — it is in the set, it
        # runs, and it passes — because a slot nobody evaluates is a slot
        # somebody has to remember to wire up.
        Exclusion.NOT_SUPPRESSED: True,
        Exclusion.NOT_ON_STANDBY: context.match_id not in viewer.on_standby,
    }
    verdicts[LANE_RULE[lane]] = free_seat if lane is Lane.OPEN else not free_seat

    return frozenset(rule for rule, held in verdicts.items() if not held)


def _clashes(
    context: MatchScoringContext, busy: Sequence[tuple[Instant, Instant]]
) -> bool:
    """Whether this match's court booking overlaps one the viewer already holds.

    Half-open on both sides, so a match starting exactly as another ends does
    not clash: a court booking already carries the club's turnaround, and two
    abutting bookings are two games she can play.
    """

    start = context.record.start
    end = match_end(context.record)
    return any(
        start < other_end and other_start < end for other_start, other_end in busy
    )


@final
@dataclass(frozen=True)
class Scored:
    """One eligible candidate with its score, before any shelf has kept it.

    ``fit`` and ``coverage`` are the engine's **true** numbers, 0–100 each and
    neither clamped: the badge's 20–99 is a display rule and applying it here
    would make two genuinely different matches rank equal. ``badge`` is the
    clamped card value and is composed from ``fit`` in one place.

    ``coverage`` is carried although it crosses no wire, because emphasis reads
    it (fit ≥ 90 · coverage ≥ 80 % · a seat open) and emphasis is a property of
    the **composed screen** rather than of one shelf — so the pass that reads it
    is one ticket further on and needs the number to still be here when it runs.
    """

    context: MatchScoringContext
    fit: int
    coverage: int
    badge: Fit
    has_free_seat: bool

    @property
    def match_id(self) -> UUID:
        return self.context.match_id

    @property
    def start(self) -> Instant:
        return self.context.record.start


def clamp_badge(fit: int) -> int:
    """The engine's 0–100 as the pill draws it: 20–99, at display time."""

    return max(BADGE_FLOOR, min(BADGE_CEILING, fit))


def feed_key(
    scored: Scored, *, distance_km: int | None
) -> tuple[int, float, bool, int, str]:
    """``FEED_ORDER`` as a sort key: ``[desc(fit), asc(start), asc(dist), asc(id)]``.

    The fit is negated rather than the sort reversed, so all four components run
    in one direction and a reader does not have to hold two.

    An unknown distance sorts **last** among equal fits and starts, not first: a
    club the platform cannot place is not thereby the nearest one. It is spelled
    as its own boolean rather than as a large stand-in number, because a stand-in
    is a distance that a real club could one day exceed. Every viewer has an
    unknown distance today (#102, ADR-0063), so this component is presently
    constant — which is exactly why it must be *stated* rather than dropped, or
    the day it has a source the order changes without a diff.

    The fourth comparator is total: two distinct candidates can never compare
    equal through the whole chain, so the order does not fall back on the query
    plan.
    """

    return (
        -scored.fit,
        scored.start.timestamp(),
        distance_km is None,
        distance_km or 0,
        str(scored.match_id),
    )


def hour_bucket(moment: Instant) -> int:
    """Which whole hour of the epoch a start falls in. Diversity's second key."""

    return int(moment.timestamp()) // 3600


def diversify(
    ranked: Sequence[Scored], *, maximum: int = MAX_PER_CLUB_HOUR
) -> tuple[Scored, ...]:
    """Push a club's third card in one hour down the shelf. **Never out of it.**

    A permutation and not a filter: the returned tuple holds exactly the same
    candidates as the one handed in, which is asserted rather than described.
    The prototype dropped an over-quota candidate and could return fewer than
    the cap with cards still waiting — a shelf shorter than it needed to be, for
    a variety rule that had already got its way.

    Deferred candidates keep their relative order among themselves, so the pass
    is deterministic and a second run over its own output is a no-op.
    """

    kept: list[Scored] = []
    deferred: list[Scored] = []
    seen: dict[tuple[UUID, int], int] = {}

    for candidate in ranked:
        key = (candidate.context.club.club_id, hour_bucket(candidate.start))
        if seen.get(key, 0) >= maximum:
            deferred.append(candidate)
            continue
        seen[key] = seen.get(key, 0) + 1
        kept.append(candidate)

    return (*kept, *deferred)


def floor_for(lane: Lane, *, retitled: bool) -> int | None:
    """The floor this shelf applies, or ``None`` when it has dropped its own.

    Shelf 1 **never goes silent**: when nothing clears 70 it is retitled to
    *Same level* and the floor goes with the title, because the retitled shelf
    makes a different claim — *these are near your Level* rather than *these are
    the best for you* — and a floor is a claim about quality.

    **The order does not change with the title**, and that is a decision rather
    than an omission. The delta describes the retitled shelf as *"matches closest
    to the viewer's Level"*, and that is what ``desc(fit)`` already leads on:
    skill overlap is the largest term in the table at 24 of 100, and it is the
    only term that reads the distance between her Level and the match's. A second
    order computed from one term of a ten-term score would be a second ranking of
    the same list, disagreeing with the badge printed beside it.
    """

    if lane is Lane.FULL:
        return FULL_FLOOR
    return None if retitled else BEST_FIT_FLOOR


def cap_for(lane: Lane) -> int:
    return FULL_CAP if lane is Lane.FULL else BEST_FIT_CAP


def code_for(lane: Lane, *, retitled: bool) -> ShelfCode:
    """Which of the three codes this shelf carries.

    Two codes for one shelf, and the client's table turns each into its title.
    The server owns which one because it owns whether the floor was met, and the
    phone holds no rules (ADR-0053).
    """

    if lane is Lane.FULL:
        return ShelfCode.FULL_WORTH_WAITING
    return ShelfCode.SAME_LEVEL if retitled else ShelfCode.BEST_FIT


def keep(candidates: Iterable[Scored], *, cap: int) -> tuple[Scored, ...]:
    """The cap, and the only pass in the funnel that removes a card."""

    return tuple(candidates)[:cap]


@final
@dataclass(frozen=True)
class Ranked:
    """What the ranked funnel answers: its shelves, and what it knew about them.

    The shelves are the region's; ``scores`` is what the funnel already computed
    and would otherwise throw away at its own edge. Emphasis reads ``fit``,
    ``coverage`` and ``has_free_seat``, and all three are on ``Scored`` — so the
    alternative to carrying them out was recomputing a score the composer had
    just discarded, on a screen whose whole cost is scoring.

    Only the cards a shelf **kept** are here. A candidate the floor, the cap or a
    lane rule removed is not on the screen, so it cannot be the emphatic card,
    and carrying it would let a later pass emphasise something nobody can see.

    ``scores`` is empty under degrade, and that is the honest shape rather than a
    marker: the scorer answered nothing, so there is nothing to emphasise, and a
    degraded screen loses its badges and its one loud card together.
    """

    shelves: tuple[Shelf, ...] = ()
    scores: tuple[Scored, ...] = ()
