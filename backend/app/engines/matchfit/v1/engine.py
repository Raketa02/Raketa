"""Match Fit v1 — seven of the ten terms, and the whole of the mechanism.

This version scores every term that needs nothing but the **Player profile** and the
match itself: the match's start against the days and hours the player declared, price
against a declared ceiling, travel against a declared radius, the match's type against
a declared preference, and a ladder the player entered. Beside them, the two terms
that **ship dark** — group reliability and familiarity — whose snapshot fields are
present and absent from the first commit, so exclusion, renormalisation and Coverage
are exercised by every call rather than being untested machinery waiting for a context
that does not exist.

The three terms still owed are named with their weights in
``constants.PENDING_WEIGHTS``.

The whole score, in the order it happens:

1. **One term per code in the table**, in table order, each built by whichever of
   the two builders declares its kind. A constraint reads a declaration and always
   scores; a piece of evidence reads an observation and is excluded when there is
   none. No term is skipped and none is added: the table is the score's audit trail.
2. **Renormalise over what ran** and take the weighted average. That is the fit, and
   nothing is added to it — no bonus, no penalty, no adjustment for how thin it is.
3. **Coverage**, separately: the weight that ran over the whole table's weight. It
   is never blended into the fit, because *"we do not know"* and *"it is good"* have
   to stay different kinds of number.
4. **Reasons**, ranked by contribution — weight times value, never value alone — and
   the strongest three come back as the very objects that are in the term list.
5. **A warning**, for the weakest contributor and only when its own value is below
   threshold. Last by contribution and perfectly fine in itself is the common case,
   and it earns no warning.

**No clamp at the end.** The source design clamped the score to a display range
because its modifiers pushed it outside 0–100; with every signal inside the
weighting, the fit is a weighted average of values in 0..1 and cannot leave the
range. A clamp here provably could not bind, and a guard that cannot fire is one
nobody should watch. What is asserted instead is the range itself, on the value
object, where a *caller* building a score by hand is the only thing that could
break it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, final

from app.engines.fit import (
    FamiliarityFact,
    LadderFact,
    MatchFitScore,
    MatchTypeFact,
    PriceFact,
    ReliabilityFact,
    ScoredTerm,
    Term,
    TermCode,
    TermFact,
    TimeFact,
    TravelFact,
)
from app.engines.forecast import PairingAnalysis
from app.engines.matchfit.core import (
    FULL_MARKS,
    Observed,
    constraint_term,
    decayed,
    evidence_term,
    lowest_contribution,
    measured_share,
    ranked_by_contribution,
    weighted_value,
    whole_percent,
)
from app.engines.matchfit.v1.constants import CONSTANTS, ENGINE_VERSION
from app.engines.matchmaking import (
    LadderQualification,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    PlayerRef,
    SeatSnapshot,
    Weekday,
)
from app.kernel import (
    Instant,
    Ratio,
    exhaustive,
    invariant,
    local_iso_weekday,
    local_minute_of_day,
    ratio,
)


@final
@dataclass(frozen=True)
class Scoring:
    """Everything one score is computed from, bundled so a term reads one argument.

    Every term takes all four and reads the ones it needs, which is what lets the
    table below be a mapping from a code to a function rather than six call sites
    each assembling their own arguments. Adding an input — the club's crowding, when
    viability lands — is then a field here instead of a signature change in six
    places.
    """

    snapshot: MatchSnapshot
    profile: PlayerProfile
    analysis: PairingAnalysis
    now: Instant


@final
class MatchFitEngineV1:
    """The v1 Match Fit engine. Pure: no clock, no randomness, no state."""

    @property
    def version(self) -> str:
        return ENGINE_VERSION

    def score(
        self,
        *,
        snapshot: MatchSnapshot,
        profile: PlayerProfile,
        analysis: PairingAnalysis,
        now: Instant,
    ) -> MatchFitScore:
        """One comparable score for one match, with its reasons and its coverage.

        ``analysis`` is an **input value and never a collaborator**: this engine
        cannot construct a forecast and does not import the engine that can, so the
        score and the card drawn beside it are computed from the same pairing by
        construction rather than by a caller remembering to pass the same one twice.
        In this version it is read for the pairing version the score carries; the two
        terms that read its numbers are #86's.

        ``now`` is unread by every term here — and it stays unread even now that one
        of them is about time, because *when the match is* and *when you asked* are
        different questions: the time fit term reads the match's own start, so the
        same match scores the same at breakfast and at midnight. It is still an
        explicit input, because the term this table still owes that measures the
        run-up to the join cutoff does depend on it (#85) and because a score
        reproducible from its stored inputs is the whole basis of the falsification
        programme. That it is **rounded to the minute** is a precondition and is
        checked as one: a score computed from an instant carrying seconds could never
        be cached and never be replayed.
        """

        invariant(
            now.second == 0 and now.microsecond == 0,
            f"now is not rounded to the minute: {now!r}",
        )

        scoring = Scoring(
            snapshot=snapshot, profile=profile, analysis=analysis, now=now
        )
        terms = tuple(term(scoring) for term in _TABLE.values())
        scored = tuple(term for term in terms if isinstance(term, ScoredTerm))
        weakest = lowest_contribution(scored)
        return MatchFitScore(
            fit=whole_percent(weighted_value(scored)),
            coverage=whole_percent(measured_share(terms)),
            terms=terms,
            reasons=ranked_by_contribution(scored)[: CONSTANTS.reasons_returned],
            warning=weakest if weakest.value < CONSTANTS.warning_threshold else None,
            engine_version=ENGINE_VERSION,
            # Read off the analysis rather than taken as an argument, so a score
            # cannot name a pairing version other than the one that produced the
            # forecast it was scored against.
            pairing_version=analysis.engine_version,
        )


def _time_fit(scoring: Scoring) -> Term:
    """Whether the match starts when the player said they can play.

    **When somebody can play is the first thing they filter on**, and the source
    design had no arithmetic for it at all: it labelled a term *"Time and travel"*
    and computed only the travel half, so a match at seven in the morning and one
    at seven in the evening were the same card to somebody who plays after work.

    A constraint, so the two silences are *no limit* and not *no measurement*: no
    declared days is any day, no declared hours is any hour, and a player who
    declared neither has no time problem at all — full marks, full weight, Coverage
    untouched, by the same route a missing price ceiling reaches it.

    **Both halves through the kernel's coordinates, never by date arithmetic.** A
    declaration is a claim about a clock face and an ``Instant`` is UTC, so the
    club's zone is the only thing that can join them, and both readers take it. A
    weekday read off the instant's own date would be wrong for the two hours either
    side of a Warsaw midnight — 22:30 UTC on a Sunday is already Monday — and wrong
    silently, which is why neither half is computed here.
    """

    zone = scoring.snapshot.club.zone
    start = scoring.snapshot.start
    fact = TimeFact(
        weekday=Weekday(local_iso_weekday(start, zone)),
        minute=local_minute_of_day(start, zone),
        days=scoring.profile.days,
        hours=scoring.profile.hours,
    )
    free = fact.on_a_declared_day and fact.inside_a_declared_window
    return _constraint(
        TermCode.TIME_FIT, FULL_MARKS if free else CONSTANTS.time_outside, fact
    )


def _price(scoring: Scoring) -> Term:
    """Full marks at or within the declared ceiling, then decaying beyond it.

    **Reads the Payable, never the SeatShare.** What a player weighs their ceiling
    against is what they will actually be charged, and a club card can be the whole
    difference between a match they will take and one they will not. The share is on
    the snapshot for the card to strike through and is deliberately not read here.

    A player who declared no ceiling has no price problem: full marks, full weight,
    Coverage untouched. That is the intent pool's own rule — *a missing price ceiling
    means eligible at any price* — and it retires the source design's hard-coded
    ceiling, which appeared with one value in its prose and another in its curve.
    """

    ceiling = scoring.profile.maximum_per_seat
    payable = scoring.snapshot.payable
    fact = PriceFact(payable=payable, ceiling=ceiling)
    if ceiling is None:
        return _constraint(TermCode.PRICE, FULL_MARKS, fact)
    return _constraint(
        TermCode.PRICE,
        decayed(
            ratio(max(0, payable - ceiling), 1),
            Ratio(CONSTANTS.price_decay_span * ceiling),
        ),
        fact,
    )


def _travel(scoring: Scoring) -> Term:
    """Full marks within the declared radius, then decaying beyond it.

    **Never an exclusion**, at any distance. *Nothing is ever excluded on distance*:
    a match an hour away reaches a player who declared twenty minutes as a low score
    they can overrule, not as an absence they cannot see. A player who declared no
    radius will go anywhere, and says so by having declared nothing.
    """

    away = scoring.snapshot.club.travel_minutes
    radius = scoring.profile.travel_radius
    fact = TravelFact(minutes=away, radius=radius)
    if radius is None:
        return _constraint(TermCode.TRAVEL, FULL_MARKS, fact)
    return _constraint(
        TermCode.TRAVEL,
        decayed(ratio(max(0, away - radius), 1), ratio(CONSTANTS.travel_decay_span, 1)),
        fact,
    )


def _match_type(scoring: Scoring) -> Term:
    """The match's kind against the kind the player asked for.

    Read and never assumed. The source design hard-coded a preference for counted
    matches, which is a fact the profile already carries and which it got wrong for
    every player who signed up to play with friends. A mismatch is worth a low value
    rather than zero, because the wrong kind of match is still a match.
    """

    counted = scoring.snapshot.counted
    preference = scoring.profile.match_type
    fact = MatchTypeFact(counted=counted, preference=preference)
    if preference is None:
        return _constraint(TermCode.MATCH_TYPE, FULL_MARKS, fact)
    wanted_counted = preference is MatchTypePreference.COMPETITIVE
    return _constraint(
        TermCode.MATCH_TYPE,
        FULL_MARKS if wanted_counted == counted else CONSTANTS.match_type_mismatch,
        fact,
    )


def _ladder(scoring: Scoring) -> Term:
    """Whether the match counts towards a ladder the player entered.

    **A term and not a modifier.** The source design added a flat bonus after the
    weighted sum, which has no defined meaning once the weights are renormalised —
    and which could push a score above a hundred before a clamp pulled it back.

    A player in no ladder has no ladder problem, which is the constraint rule
    applied to a fact the *match* carries: it reaches full marks by the same route a
    missing price ceiling does. The ``match`` is closed over the enum, so a fourth
    ladder state fails the build here rather than falling through to a value nobody
    chose.
    """

    qualification = scoring.snapshot.ladder
    fact = LadderFact(qualification=qualification)
    match qualification:
        case LadderQualification.QUALIFIES | LadderQualification.NOT_IN_A_LADDER:
            value = FULL_MARKS
        case LadderQualification.OUTSIDE:
            value = CONSTANTS.ladder_outside
        case _:
            exhaustive(qualification)
    return _constraint(TermCode.LADDER_QUALIFICATION, value, fact)


def _group_reliability(scoring: Scoring) -> Term:
    """How reliably the *other* people in this match turn up. **Evidence.**

    Excluded whenever nobody else on a seat carries a record, which today is always:
    the field ships dark and is absent in every snapshot the platform can assemble.
    So this term is the live proof that exclusion works — it takes 11 of the table's
    38 points out of the denominator on every score, and Coverage says so.

    **The current player's own record is not read.** You know whether you will turn
    up, and scoring your own reliability into a recommendation *to you* would make
    the platform's opinion of you a reason to show you fewer matches.

    **The least reliable member, not the average.** A match needs everybody: one
    no-show cancels it for the other three, so a group is only as dependable as its
    weakest member and an average would let three dependable players hide one who
    never comes. A product of the rates — the probability all of them turn up — is
    the other candidate and is rejected because reliability as published will be a
    *rate* rather than an independent probability, and multiplying rates would make
    a four-player match score below a two-player one by arithmetic rather than by
    evidence.
    """

    code = TermCode.GROUP_RELIABILITY
    others = _others_seated(scoring.snapshot)
    records = tuple(seat.score.reliability for seat in others if seat.score is not None)
    if not records:
        return evidence_term(code, _weight(code), None)
    least = min(records)
    return evidence_term(
        code,
        _weight(code),
        Observed(
            value=least,
            fact=ReliabilityFact(
                least_reliable=least, observed=len(records), seated=len(others)
            ),
        ),
    )


def _familiarity(scoring: Scoring) -> Term:
    """How many of the others are new to this player. **Evidence.**

    Variety rewarded and playing the same four people every week gently discouraged
    — *gently* being the weight of three, not a steep curve. The value is the share
    of the other seated players the current player has **not** played recently, which
    needs no constant of its own: what counts as *recently* is a window, and a window
    belongs to the context that will own play history rather than to an engine reading
    its conclusion.

    Excluded on two different silences, and both are real. No ``PlayHistory`` at all
    is the platform never having observed who plays with whom, which is today. Nobody
    else on a seat is a match with nobody to be familiar with — an empty court has no
    company, and *"you have never played these nobodies"* is not a good score, it is
    no observation.
    """

    code = TermCode.FAMILIARITY
    history = scoring.snapshot.history
    others = tuple(
        seat.occupant.player
        for seat in _others_seated(scoring.snapshot)
        if seat.occupant is not None
    )
    if history is None or not others:
        return evidence_term(code, _weight(code), None)
    new_faces = sum(1 for player in others if player not in history.played_recently)
    return evidence_term(
        code,
        _weight(code),
        Observed(
            value=ratio(new_faces, len(others)),
            fact=FamiliarityFact(new_faces=new_faces, others=len(others)),
        ),
    )


#: One entry per term, in the table's own order — which is descending weight, and is
#: therefore the tie-break for the reason ranking. A ``Mapping`` keyed by the code so
#: that *one term per code* is true by construction and the constants' guard over the
#: same key set is checking the same thing from the other side.
_TABLE: Mapping[TermCode, Callable[[Scoring], Term]] = {
    TermCode.TIME_FIT: _time_fit,
    TermCode.GROUP_RELIABILITY: _group_reliability,
    TermCode.TRAVEL: _travel,
    TermCode.LADDER_QUALIFICATION: _ladder,
    TermCode.PRICE: _price,
    TermCode.MATCH_TYPE: _match_type,
    TermCode.FAMILIARITY: _familiarity,
}


def _constraint(code: TermCode, value: Ratio, fact: TermFact) -> ScoredTerm:
    """A constraint term at this version's weight for it.

    Wrapped only to read the weight in one place; the *kind* comes from ``core``'s
    builder and nothing here can change it.
    """

    return constraint_term(code, _weight(code), value, fact)


def _weight(code: TermCode) -> int:
    """This term's weight, narrowed from the constants' table.

    The table is proved to cover exactly the vocabulary's codes when the constants
    are built, so this cannot fail for a code that got here — the ``invariant`` is
    what turns *cannot fail* into a type the caller can rely on.
    """

    return invariant(CONSTANTS.weights.get(code), f"no weight for {code.value}")


def _others_seated(snapshot: MatchSnapshot) -> tuple[SeatSnapshot, ...]:
    """The seats of everybody in this match except the current player.

    *Everybody except me* is what both evidence terms here are about — how reliable
    the company is, and how new it is — and it is computed once so the two cannot
    develop two ideas of who counts as company. A player looking at a match they are
    already in is not their own company.
    """

    current: PlayerRef = snapshot.current_player.player
    return tuple(
        seat
        for seat in snapshot.seats
        if seat.occupant is not None and seat.occupant.player != current
    )
