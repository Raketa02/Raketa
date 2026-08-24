"""The invitation ladder: who is told a seat has freed, in what order, and when.

ADR-0061, amending ADR-0052. Everything in this module is the half of the
cascade that can be written down without a repository, an engine or a clock of
its own: which facts disqualify a player, which rung she stands on, what order
the rungs are in, when each of the two dispatches is due, and how late in the
night one may land.

**One pool, one order, two dispatches.** ADR-0061 replaced ADR-0052's exclusive
offer — and with it the one-hour hold, the three-offer cap and the twelve-hour
backstop — with a single open call at every distance from the match. What is
left of exclusivity is the seat claim, which belongs to the money chain
(ADR-0081). So there is no per-candidate process here and nothing to reconcile
when a seat fills mid-walk: *"all-at-once puts every piece of state on the
vacancy — an eligible set computed once, two dispatch jobs, first-to-accept
wins."*

**The pool is a fact filter and the band is a wall.** ``exclusions_for``
mirrors ``funnel.exclusions`` deliberately — same shape, same *evaluate all,
never short-circuit* discipline, same answer type — because they are the same
question asked from opposite ends: the funnel asks *which matches may reach this
player*, and this asks *which players may reach this match*. ADR-0027 governs
both: candidate generation excludes on **facts**, never on preferences.

**The order is the expensive part and it is written once.** The seven rungs are
fixed here even though three of them have no source in v1, because ADR-0061's
whole argument is that a rung turns on when its feature ships and adding one
later is a re-sort rather than a new stage. A rung with no source ships **dark**
— declared, empty, and named as empty — rather than being left out and
renumbering the six that remain.

**Nothing here is random and nothing here is a preference.** Distance, price and
level are never exclusions (ADR-0027) — the one apparent exception is the band,
and it is not a preference at all: it is the game the players who stayed bought.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, final
from uuid import UUID

from app.engines.matchmaking import Level

from app.kernel import (
    Instant,
    MatchRecord,
    OfferKind,
    SeatShare,
    Minutes,
    MinuteOfDay,
    Ok,
    Zone,
    deadlines,
    elapsed_minutes,
    exhaustive,
    hours,
    invariant,
    is_full,
    is_terminal,
    day_offset,
    match_end,
    minute_of_day,
    minutes,
    shifted,
    slot_start,
)


class Rung(Enum):
    """Where a candidate stands in the invitation ladder. **Seven, in order.**

    The values are the rungs' positions rather than names, because the position
    *is* the specification: ADR-0061's table is an ordering and the numbers are
    what a reader compares against it. ``Rung.STANDBY`` sorts first because it
    is 1, not because it is declared first — a distinction that matters the day
    somebody rearranges the declarations for readability.

    Three of the seven have no source in v1 and are named in ``DARK_RUNGS``
    below rather than left out: renumbering the survivors would make the table
    here and the table in the ADR two different documents.
    """

    #: Asked for **this** match. The standby queue, and the only rung in the
    #: first dispatch — *"one head start is not an optimisation, it is the
    #: standby promise."*
    STANDBY = 1
    #: A standing rule matched this match. **Dark**: the alerts feature is
    #: unbuilt, and ADR-0061 records that when it ships it *auto-joins standby*,
    #: so it will feed rung 1 rather than appear here at all.
    STANDING_RULE = 2
    #: Offered an earlier vacancy on **this** match and did not get the seat.
    #: Reads the offers this cascade itself writes, which is what makes it a
    #: rung with a source rather than a rung waiting for a feature.
    ASKED_BEFORE = 3
    #: Viewed or followed the match. **Dark**: ADR-0085 ships the *Recently
    #: viewed* store dark and `Raketa02/Raketa#53` was closed without building
    #: it, so there is nothing to read. *Follow* does not exist at all.
    VIEWED = 4
    #: Plays at this club often. Read as play history at the club — a seat held
    #: at a match there, before now.
    CLUB_REGULAR = 5
    #: Everyone else inside the band. ADR-0061's *"ships degraded — the level
    #: band only"*: **reliable** is recorded nowhere and **nearby** has no
    #: source, so the tail rung is everyone in the band anywhere. The ADR calls
    #: that the ladder behaving correctly rather than a gap — it lands exactly
    #: on ADR-0052's *"then everyone else eligible"*.
    IN_THE_BAND = 6
    #: Marked available at this hour. **Dark**, the same effort as rung 2.
    MARKED_AVAILABLE = 7


#: The rungs with no source in v1. **Named rather than omitted**, and asserted
#: against the ladder's own producers: a rung nothing populates and nothing
#: declares empty is indistinguishable from a rung whose query is broken.
#:
#: ADR-0061 ships 2 and 7 dark by name. **Rung 4 joins them here and the ADR
#: does not say so**, because the signal it was to be built on — ADR-0085's
#: *Recently viewed* — shipped dark itself and `Raketa02/Raketa#53` closed
#: without a store. That is a deviation from the ticket's own acceptance
#: criterion, which names only 2 and 7, and it is recorded rather than papered
#: over.
DARK_RUNGS: frozenset[Rung] = frozenset(
    {Rung.STANDING_RULE, Rung.VIEWED, Rung.MARKED_AVAILABLE}
)


class Wave(Enum):
    """Which of the two dispatches a rung is told in.

    Two, and not seven. ADR-0061: *"seven staged rungs is what this product
    becomes when volume earns it; adding delays to an ordering that already
    exists is the whole migration. Today each rung below the first holds two or
    three people, so six delays buy nothing but a seat still walking the ladder
    an hour later."*
    """

    #: Rung 1, immediately.
    FIRST = 1
    #: Rungs 2–7, ten minutes later.
    SECOND = 2


#: Which dispatch each rung rides in. A **total** mapping over ``Rung``,
#: asserted exhaustive at module load, so an eighth rung cannot be added
#: without saying when it is told.
WAVE_OF: dict[Rung, Wave] = {
    Rung.STANDBY: Wave.FIRST,
    Rung.STANDING_RULE: Wave.SECOND,
    Rung.ASKED_BEFORE: Wave.SECOND,
    Rung.VIEWED: Wave.SECOND,
    Rung.CLUB_REGULAR: Wave.SECOND,
    Rung.IN_THE_BAND: Wave.SECOND,
    Rung.MARKED_AVAILABLE: Wave.SECOND,
}

invariant(set(WAVE_OF) == set(Rung), "a rung with no dispatch")


def rungs_in(wave: Wave) -> tuple[Rung, ...]:
    """Every rung told in this dispatch, in ladder order."""

    return tuple(rung for rung in Rung if WAVE_OF[rung] is wave)


#: How long rungs 2–7 wait behind rung 1. **The whole of what joining a standby
#: queue buys**, and ADR-0061 is candid that it is not much: *"a standby
#: player's head start is ten minutes, and nothing shows it."* Told in the same
#: instant as strangers, joining a waitlist buys nothing at all — which is the
#: exact failure ADR-0052 named when it refused pure fit ranking.
HEAD_START: Minutes = minutes(10)

#: The fit floor above ``FLOOR_HORIZON``, and there is none below it. *"We
#: suggest matches over 70"* is a promise about **suggestions**; *"a seat just
#: opened at half price"* is a different sentence, and inside a day the
#: alternative to telling a 55 is a dead seat.
#:
#: The number is ``funnel.BEST_FIT_FLOOR``'s and is deliberately **not**
#: imported from it: a shelf floor and a rescue floor sharing a home is how one
#: comes to be tuned by somebody moving the other, which is the argument
#: ``composition.py`` already makes for the two emphasis floors.
CASCADE_FLOOR = 70

#: When the floor stops applying. Keyed on the **clock** and not on a mode name,
#: because ADR-0061 replaced the modes with one open call and a floor keyed on a
#: mode would be a rule with nothing left to read.
FLOOR_HORIZON: Minutes = hours(24)

#: The local hour before which nothing is delivered. ADR-0052's rule, one of the
#: two ADR-0061 keeps untouched: *"a free seat does not wake anybody at 03:00."*
QUIET_UNTIL: MinuteOfDay = minute_of_day(8 * 60)

#: How close to the start a match has to be for the quiet hours to be spent on
#: it. Inside twelve hours the seat is nearly dead and waking somebody is the
#: lesser harm.
QUIET_EXEMPT_WITHIN: Minutes = hours(12)


class PoolExclusion(Enum):
    """Why one player is not in the pool for this seat. **Every rule, every
    player.**

    A diagnosis vocabulary that **crosses no wire**, exactly as
    ``funnel.Exclusion`` is: no player has ever seen a reason she was not told
    about a seat, and *"eleven of them are playing that evening already"* is an
    operational sentence rather than a player's.

    The set is ADR-0061's fact filter, spelled as it spells it, plus the wall.
    Distance and price are absent because ADR-0027 forbids them as exclusions,
    and the absence is asserted rather than merely true.
    """

    #: A rating exists at the match's sport. **The addition ADR-0061 makes to
    #: the feed's filter**, and it is legal under ADR-0027 because it excludes
    #: on a *missing fact* rather than on a low score: the fit engine imputes a
    #: level where no rating exists, so without this a badminton-only player is
    #: "eligible" for every squash cancellation in the city at an invented one.
    RATED_AT_SPORT = "ratedAtSport"
    #: There is a seat to give.
    HAS_FREE_SEAT = "hasFreeSeat"
    #: Joining has not closed.
    BEFORE_JOIN_CUTOFF = "beforeJoinCutoff"
    #: The match still has its court and has not ended in any of the five ways.
    #: ADR-0061's *"live inventory"*, read through ``is_terminal`` rather than
    #: off the flags, because a second reading of them would be a second ladder
    #: over the record (ADR-0040).
    LIVE_INVENTORY = "liveInventory"
    #: She is not already playing something that overlaps this.
    NO_SCHEDULE_CONFLICT = "noScheduleConflict"
    #: The match is not already hers — a seat, a live claim, or a departure she
    #: made herself. Two readings of one fact and one rule, unlike the funnel's
    #: split: there is no *suggestion* here to keep apart from a *conflict*.
    NOT_ALREADY_MINE = "notAlreadyMine"
    #: **The wall.** ADR-0061: *"'everyone else eligible' means everyone inside
    #: the band the players who stayed signed up for"*, and reaching outside it
    #: is `3.1` Stage 3 and remains unanimous-consent. A badminton rating does
    #: not qualify anyone for squash cancellations and the game the stayers
    #: bought is the game played.
    INSIDE_THE_BAND = "insideTheBand"


#: Every rule, in ADR-0061's own order. A tuple rather than the enum's
#: declaration order for the reason ``funnel.COMMON_RULES`` is one: the order is
#: read against the record and a reader must not have to trust that two
#: declarations agree.
POOL_RULES: tuple[PoolExclusion, ...] = (
    PoolExclusion.RATED_AT_SPORT,
    PoolExclusion.HAS_FREE_SEAT,
    PoolExclusion.BEFORE_JOIN_CUTOFF,
    PoolExclusion.LIVE_INVENTORY,
    PoolExclusion.NO_SCHEDULE_CONFLICT,
    PoolExclusion.NOT_ALREADY_MINE,
    PoolExclusion.INSIDE_THE_BAND,
)

invariant(set(POOL_RULES) == set(PoolExclusion), "a pool rule with no place")

#: The rules that are facts about **the seat**, answerable from the record, the
#: clock and whether this match is already hers. They are the whole of what the
#: offers region asks a second time (``Raketa02/Raketa#83``): the cascade decides
#: *who is told*, and the region decides *whether the seat is still there* — and
#: the second question is asked live on every compose because an offer is a fact
#: about the past and a seat is not.
SEAT_RULES: tuple[PoolExclusion, ...] = (
    PoolExclusion.HAS_FREE_SEAT,
    PoolExclusion.BEFORE_JOIN_CUTOFF,
    PoolExclusion.LIVE_INVENTORY,
    PoolExclusion.NOT_ALREADY_MINE,
)

#: The rules that need the **candidate** — her rating, her diary, her Level. The
#: offers region never asks these again: the cascade asked them when it wrote the
#: offer, and re-deciding *is she still the right person for this* on a card she
#: is already looking at would withdraw a seat by a rule she cannot see, which is
#: precisely what ADR-0061 replaced retraction with wording to avoid.
CANDIDATE_RULES: tuple[PoolExclusion, ...] = (
    PoolExclusion.RATED_AT_SPORT,
    PoolExclusion.NO_SCHEDULE_CONFLICT,
    PoolExclusion.INSIDE_THE_BAND,
)

#: A **partition**, asserted rather than described. An eighth rule lands in one
#: half or the other on the day it is written, rather than in neither — which is
#: the failure the two tuples exist to make impossible: a rule about the seat
#: that the region never asks is a card offering a seat that is gone.
invariant(
    set(SEAT_RULES) | set(CANDIDATE_RULES) == set(PoolExclusion),
    "a pool rule that is neither about the seat nor about the candidate",
)
invariant(
    not (set(SEAT_RULES) & set(CANDIDATE_RULES)),
    "a pool rule counted as both a seat fact and a candidate fact",
)


@final
@dataclass(frozen=True)
class Band:
    """The Level range a match is aimed at, as the wall reads it.

    ``low`` and ``high`` come from the pairing engine's ``TargetBand``, which is
    *the mean of the seated Levels* either side of one constant half-width —
    **the players who stayed**, in ADR-0061's own words, computed from the
    roster rather than stored on the match. There is no level-band column and
    this is why there does not need to be one: a band derived from the seats is
    a band that moves when the seats do, and a stored one would be a second
    answer to *what game is this* that nothing keeps in step.

    Inclusive on both ends, because the band's edges are already blunt: a
    half-width is a rounding of a claim, and excluding a player who lands
    exactly on it would be reading precision the number does not carry.
    """

    low: Level
    high: Level

    def admits(self, level: Level) -> bool:
        return self.low <= level <= self.high


@final
@dataclass(frozen=True)
class PoolCandidate:
    """One player weighed against one seat, before anything is ranked.

    ``level`` is present exactly when ``rating`` is — a candidate with no rating
    at the sport fails ``RATED_AT_SPORT`` and never reaches the band — so the
    wall always has a number to compare against rather than a rule about
    absence.
    """

    player_id: UUID
    rung: Rung
    level: Level | None
    busy: tuple[tuple[Instant, Instant], ...] = ()
    already_mine: bool = False


def exclusions_for(
    candidate: PoolCandidate,
    record: MatchRecord,
    *,
    band: Band | None,
    now: Instant,
) -> frozenset[PoolExclusion]:
    """Every rule this player failed for this seat. Empty means she is in the pool.

    **All of them are evaluated**, on ``funnel.exclusions``'s shape and for its
    reason: the dictionary is built whole before anything is filtered out of it,
    so *do not short-circuit* is a property of the shape rather than a comment
    somebody has to keep true. A caller wanting a histogram of *why nobody was
    reachable* gets one for free, and that is the operational question a dead
    seat raises.

    ``band`` is ``None`` when the match has no band to be outside of — nobody is
    seated, or nobody seated holds a Level here. **That is no wall rather than a
    wall nobody clears.** The band is a fact about the seated Levels, so with no
    seated Level there is no *outside* it; refusing everybody on a missing fact
    would turn a match whose last rated player left into a seat that can never
    be filled, which is the dead seat the floor rule is dropped inside a day to
    avoid.
    """

    verdicts: dict[PoolExclusion, bool] = {
        PoolExclusion.RATED_AT_SPORT: candidate.level is not None,
        PoolExclusion.NO_SCHEDULE_CONFLICT: not _clashes(record, candidate.busy),
        PoolExclusion.INSIDE_THE_BAND: (
            band is None
            or candidate.level is None
            or band.admits(candidate.level)
        ),
    }
    return frozenset(
        rule for rule, held in verdicts.items() if not held
    ) | seat_exclusions(record, already_mine=candidate.already_mine, now=now)


def seat_exclusions(
    record: MatchRecord, *, already_mine: bool, now: Instant
) -> frozenset[PoolExclusion]:
    """The four rules that are about **the seat** rather than about a person.

    Written once and read from both ends. The cascade asks it inside
    ``exclusions_for`` when it decides who to tell; the offers region asks it
    again on every compose, because ``Offers.held_by`` *"answers offers and never
    live offers"* — whether the seat is still there is a question about the
    match, and an offer written an hour ago cannot answer it.

    Two readings of these four facts is the failure this exists to remove, and it
    is not a hypothetical one: a region that decided *the match is full* by its
    own arithmetic would eventually disagree with the pool that wrote the offer,
    and the visible symptom is a card offering a seat the aggregate refuses.

    ``already_mine`` is the same three memberships the pool means by it — a seat,
    a live claim, or a departure she made herself — and it is a fact about the
    pair rather than about the record, which is why it is a parameter and not
    read off ``record``.
    """

    verdicts: dict[PoolExclusion, bool] = {
        PoolExclusion.HAS_FREE_SEAT: not is_full(record),
        PoolExclusion.BEFORE_JOIN_CUTOFF: now < deadlines(record).join_cut,
        PoolExclusion.LIVE_INVENTORY: not is_terminal(record),
        PoolExclusion.NOT_ALREADY_MINE: not already_mine,
    }
    return frozenset(rule for rule, held in verdicts.items() if not held)


def seat_expires_at(record: MatchRecord) -> Instant:
    """The moment an open seat in this match stops being takeable.

    **The join cutoff, and there is nothing else it could be.** ADR-0061 retired
    the exclusive offer's one-hour hold along with the offer itself, so an open
    call has no clock of its own — what expires is the *seat*, and
    ``Match.open_claim`` enforces exactly this instant and no other: *"nobody may
    start buying a seat once joining has closed."*

    It is derived on every read rather than stored beside the offer, on the band's
    own argument: a club that moves its cutoff, or a match that moves its hour,
    moves this with it, where a copy taken at the dispatch would be a second
    answer to *when does this seat die* that nothing keeps in step.

    A seat can also stop being takeable because somebody took it, and that is not
    a moment — which is why the region **filters** on ``seat_exclusions`` and
    only **orders** on this.
    """

    return deadlines(record).join_cut


def _clashes(
    record: MatchRecord, busy: Sequence[tuple[Instant, Instant]]
) -> bool:
    """Whether this match's court booking overlaps one she already holds.

    Half-open on both sides, exactly as ``funnel._clashes`` is and for the same
    reason: a court booking already carries the club's turnaround, and two
    abutting bookings are two games she can play. The two implementations are
    deliberately not shared — the funnel's reads a scoring context and this one
    reads a record, and a helper taking both would be a parameter answering
    *which caller am I*.
    """

    start = record.start
    end = match_end(record)
    return any(
        start < other_end and other_start < end for other_start, other_end in busy
    )


def floor_at(record: MatchRecord, now: Instant) -> int | None:
    """The fit floor for a seat freeing now, or ``None`` for no floor.

    ADR-0061: *"above 24 h to the match, a fit floor of 70; inside 24 h, no
    floor."* Measured as **elapsed** minutes to the start rather than by
    subtracting wall clocks, because the kernel's own rule is that a
    twelve-hour rule means twelve elapsed hours and subtracting from a
    wall-clock hour is wrong twice a year.

    A match that has already started has no floor either, which is arithmetic
    rather than a third case: ``elapsed_minutes`` of a start behind us is not
    greater than a day. Nothing reaches here in that state — ``LIVE_INVENTORY``
    and ``BEFORE_JOIN_CUTOFF`` are both ahead of it — so it is the safe answer
    to a question that is not asked rather than a branch with a meaning.
    """

    return CASCADE_FLOOR if elapsed_minutes(now, record.start) > FLOOR_HORIZON else None


@final
@dataclass(frozen=True)
class Invitation:
    """One player, her rung and her fit — the unit the ladder orders.

    ``fit`` is the engine's **true** 0–100 score and not the badge's clamp, for
    ``funnel.Scored``'s reason: two genuinely different matches must not rank
    equal because a display rule flattened them. Nothing prints this number; it
    orders a list.
    """

    player_id: UUID
    rung: Rung
    fit: int


def invitation_order(invitations: Sequence[Invitation]) -> tuple[Invitation, ...]:
    """The ladder: by rung, then by fit within a rung, then by id.

    **The rung dominates the fit, and that is the whole design.** ADR-0052
    refused pure fit ranking by name, because under it joining a standby queue
    buys nothing: a better-fitting stranger would outrank the person who asked.
    So somebody on rung 1 with a fit of 71 is told before somebody on rung 6
    with a fit of 96.

    The third comparator is load-bearing rather than decorative, exactly as
    ``FEED_ORDER``'s fourth is: without a guaranteed-total final key the order
    falls back on whatever order the pool arrived in, which is the query plan,
    and two dispatches of one wave could disagree about who was first.
    """

    return tuple(
        sorted(
            invitations,
            key=lambda one: (one.rung.value, -one.fit, str(one.player_id)),
        )
    )


def wave_due(vacated_at: Instant, wave: Wave) -> Instant:
    """When a dispatch becomes due, before the quiet hours are applied.

    Rung 1 at the vacancy; rungs 2–7 ten minutes later. ADR-0061's *"an empty
    rung costs nothing"* is not here — it is a fact about what the **first**
    dispatch found, so it belongs to whoever ran it, and this function has no
    way to know.
    """

    match wave:
        case Wave.FIRST:
            return vacated_at
        case Wave.SECOND:
            return shifted(vacated_at, HEAD_START)
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(wave)


def delivery_at(
    due: Instant, record: MatchRecord, *, zone: Zone
) -> Instant:
    """When a dispatch due at ``due`` may actually be delivered.

    **Held to 08:00 local unless the match starts within twelve hours**, which
    is one of the two ADR-0052 rules ADR-0061 keeps untouched. The zone is the
    **club's**, because the match is played there and the player the platform
    cannot locate has no zone of her own to hold delivery to (`#102`).

    The hold is applied to a moment **before** 08:00 local and to nothing else,
    which is exactly what *held to 08:00* says and knowingly narrower than
    *quiet hours* would be: a dispatch due at 23:30 local is delivered at 23:30.
    Neither ADR names an evening boundary, and inventing one here would be a
    threshold nobody wrote down sitting in the one module that decides when a
    phone lights up. It is recorded as a consequence rather than closed by
    guess.

    A local 08:00 that **does not exist** — a spring-forward gap — delivers at
    ``due`` rather than never. The gap is 02:00–03:00 in every zone that has
    one, so this cannot fire today; it is here because the alternative to
    answering is dropping a seat on the floor, and a fallback that delivers
    early is the safe direction.
    """

    if elapsed_minutes(due, record.start) < QUIET_EXEMPT_WITHIN:
        return due
    opens = slot_start(
        anchor=due, day=day_offset(0), minute=QUIET_UNTIL, zone=zone
    )
    if not isinstance(opens, Ok):
        return due
    return opens.value if opens.value > due else due


@final
@dataclass(frozen=True)
class Offer:
    """One seat, put in front of one player. **A fact, not a message.**

    ADR-0062 makes the notification *"a prompt to look, not a record"*, so this
    is the record and the push is downstream of it (`Raketa02/Raketa#84`). It
    carries no wording, no channel and no delivery receipt: what was sent is the
    sender's business, and what is true is that this seat was opened to this
    player at this instant.

    ``kind`` is always ``OfferKind.OPEN`` in v1 and is stored rather than
    assumed. ADR-0061 retired the exclusive offer along with its hold, its cap
    and its backstop, and the kernel keeps both names *"because the ladder must
    be able to say the sentence the moment an exclusive offer exists, not a
    release later"* — a column with one value today is what makes that true of
    the store as well as of the vocabulary.

    ``price`` is what she would pay taking it at the moment she was told, and it
    is stored because it is the sentence she was shown. ``kernel.seat_price``
    answers the same question live, and the two differ exactly when the rescue
    deadline passed between the telling and the tap — which is a real change she
    is entitled to see rather than a disagreement to hide.

    ``vacancy_id`` is what makes rung 3 answerable: *offered an earlier vacancy
    on this match and did not get it* is a comparison of holes, and an offer
    filed under the match alone could not tell a second hole from the first.
    """

    match_id: UUID
    vacancy_id: UUID
    player_id: UUID
    player_rung: Rung
    fit: int
    price: SeatShare
    kind: OfferKind
    offered_at: Instant


@final
@dataclass(frozen=True)
class PendingWave:
    """One dispatch waiting to happen, and when it may.

    **The state is on the vacancy and not on a candidate**, which is the whole
    of ADR-0061's *"all-at-once"* argument: one-at-a-time would need a hold, a
    clock and a cap per person, and this needs two rows per hole.

    ``due_at`` already has the quiet hours applied, so a reader comparing it
    against the clock does not need the club's zone to know whether a dispatch
    may run. That is deliberate: the hold is a decision made once, when the hole
    opened, and re-deciding it on every tick would let a dispatch that was held
    to 08:00 be re-held to tomorrow's 08:00 for ever if the tick were ever late.
    """

    match_id: UUID
    vacancy_id: UUID
    wave: Wave
    due_at: Instant
