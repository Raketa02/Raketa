"""Assembling a ``MatchSnapshot``, and reading a badge off what comes back.

The engines are pure, versioned and take a snapshot; a shelf has a scoring
context and a viewer. This module is the one place the two meet, and it is in
the application layer rather than in ``infrastructure/`` because every line of it
is a **rule** — which profile a player who has declared nothing has, what phase
the assembler states, which of the pairing engine's two answers is precise
enough to print — and none of it reads a database.

**Nothing in ``app/engines/`` changes.** The shipped ``matchfit`` engine with its
ten ``TermCode``s is the fixed point (ADR-0036, and the fit-model delta's own
*"backend/app/engines/ — not one line"*). Everything decided here is decided on
this side of the input contract.

**Two engines, one pairing.** ADR-0026: the caller runs Pairing and hands the
result to Match Fit, so the score and the *aimed at* Level printed beside it come
from one analysis by construction. An engine free to build its own forecast could
score a match against a pairing nobody was shown.

**Travel is unmeasured and the sentinel is bounded by a property, not a
comment.** ``ClubSnapshot.travel_minutes`` is required with no default —
deliberately, because *"a default of zero minutes is a court next door"* — and
the platform holds no player location at all: ADR-0063 makes the anchor optional
and *precision follows the anchor*, so ``distance_km`` is absent for every viewer
(``Raketa02/Raketa#102``). The three ways out were a sentinel, an optional field,
and deriving a distance from a city; the third ADR-0063 refuses by name, the
second changes an engine input's type that ADR-0026 fences, and the first is what
ships — **because the travel term is a constraint term.** An undeclared radius is
genuinely *no limit*, so the term scores full marks whatever the number beside it
is, and no player can declare a radius today: the preferences editor has no
screen and no contract (``Raketa02/Raketa#105``), so ``PlayerProfile`` is built
empty here. That makes the sentinel provably unable to move a score, and
``tests/unit/test_now_scoring.py`` asserts the *property* — the same match scored
against two wildly different sentinels produces the identical
``MatchFitScore`` — rather than the reasoning. The day a radius reaches the
profile, that test goes red, which is the day the sentinel stops being safe.

**Crowding is computed and never fabricated**, and the asymmetry with travel is
the whole point: crowding is read by the **viability** term as *evidence* — it
multiplies straight into the score — so a default of nothing is an empty club,
the most flattering answer available and exactly the observation ADR-0027 exists
to remove. It is a real query over the club's live courts and the reservations
touching the match's window, paid once per ``matchId : recordVersion`` because it
is the same number for everybody looking at that match.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.engines.fit import (
    MatchFitEngine,
    MatchFitScore,
    ScoredTerm,
    TermCode,
)
from app.engines.forecast import BalanceForecastEngine, PairingAnalysis
from app.engines.matchmaking import (
    ClubSnapshot,
    CourtHold,
    LadderQualification,
    MatchPhase,
    MatchSnapshot,
    Occupant,
    PlayerProfile,
    SeatSnapshot,
    SeatState,
)
from app.kernel import (
    Instant,
    Minutes,
    Ok,
    Payable,
    Seat,
    SeatShare,
    grosze,
    court_hold,
    deadlines,
    instant,
    invariant,
    is_terminal,
    minutes,
)

from app.modules.now.domain.funnel import MatchScoringContext, clamp_badge
from app.modules.now.domain.screen import Fit, FitReason

#: What a snapshot carries for travel when the platform cannot locate the
#: player, which is every player today. **Not a measurement and not a claim.**
#:
#: Ninety minutes rather than zero, and the choice of number is itself the
#: argument: zero is the one value that would be *flattering* if the term ever
#: read it, so the sentinel is deliberately pessimistic — if the guard below
#: ever failed and a declared radius met this number, the match would score
#: worse rather than better, and a suggestion that is quietly too cautious is
#: recoverable where one that is quietly too generous is a wasted evening.
TRAVEL_UNMEASURED: Minutes = minutes(90)

#: How many reasons ride on a card. The engine ranks every scored term by
#: contribution; the card takes the strongest three, which is the specification's
#: number and the delta's.
REASON_CAP = 3


@final
class Unscorable(Exception):
    """The scorer could not answer for this match. **The degrade signal.**

    Raised rather than returned, and caught once per screen rather than once per
    card: a shelf ordered from a scoring pass that half ran is a shelf whose
    order means nothing, and *"a feed with no ranking is better than no feed"*
    only holds when the whole feed is unranked. ADR-0069's degrade is a per-shelf
    kill switch, so this is what throws it.
    """


def profile_for(player_id: UUID) -> PlayerProfile:
    """What this player declared about how she wants to play. **Nothing, yet.**

    ``PlayerProfile()`` — every field absent — is the honest launch state and the
    engine says so in as many words: such a player has no price problem, no
    travel problem and no match-type problem, so those terms score full marks,
    keep their weight, and Coverage is untouched.

    It is a function of the player rather than a constant, so the day the
    preferences editor exists (``Raketa02/Raketa#105``) this is the signature
    that gains a port and not thirty call sites. An **empty declaration is
    refused rather than read as absence** by the profile itself — no declared day
    is silence, an empty set of days means *no day works* — so a future adapter
    cannot spell one as the other by accident.
    """

    return PlayerProfile()


def snapshot_for(
    context: MatchScoringContext,
    *,
    viewer: Occupant,
    now: Instant,
) -> MatchSnapshot:
    """One match as the engines are given it, for one viewer, at one instant.

    **The phase is stated and not derived, and that is a decision with a cost.**
    ``MatchSnapshot`` refuses anything but ``FORMING`` — its error message reads
    *"only a forming match is a candidate"* — and the matchmaking projection
    ``MATCH_PHASE_OF`` maps a **full** match to ``LOCKED``, so deriving the phase
    would make shelf 2 unscorable and the *Full, but worth waiting for* shelf
    could never compose at all. The two are asking different questions: the
    projection asks *is this roster fixed*, and the snapshot's guard asks *is
    this a candidate*. **Eligibility is what answers the second**, exhaustively
    and before this function is ever called — ``NotCancelled``,
    ``StartsInFuture`` and ``BeforeJoinCutoff`` are three of its eight common
    rules — so the guard is held, one layer up, by the pass that owns it.
    **Stating the phase gives up the snapshot's own guard, so the guard is
    reinstated here.** The field's docstring says what it is for — *"stating it
    is what turns a cancelled match in a home list into a loud failure at the
    point that assembled it"* — and a constant would have made that fact
    unfalsifiable. So this refuses a terminal match and one that has already
    started, in Now's own words, through ``invariant``: the ``Unscorable`` around
    it turns the refusal into a degraded shelf rather than a 500 on a home
    screen, and eligibility means it can only fire on a caller's bug.

    **Both instants are truncated to the minute**, because the snapshot requires
    it and nothing upstream rounds a start. Truncation is monotone, so
    ``join_cutoff <= start`` survives it — the ordering the snapshot also checks
    cannot be broken by the rounding that satisfies its neighbour.
    """

    record = context.record
    invariant(
        not is_terminal(record),
        f"a cancelled match reached the scorer: {context.match_id}",
    )
    invariant(
        record.start > now,
        f"a match that has started reached the scorer: {context.match_id}",
    )
    return MatchSnapshot(
        sport=record.sport,
        seats=tuple(_seat(seat, occupant) for seat, occupant in _pairs(context)),
        current_player=viewer,
        start=_to_the_minute(record.start),
        counted=context.counted,
        # ``payable == share`` for every player in v1: nothing in the product
        # reduces what one player owes below her part of the court, and the
        # money kernel's ``payable_from`` is the chain that would. Both are sent
        # because the engine reads the **payable** and a card struck through the
        # share needs the other — a snapshot whose share moves and whose payable
        # does not scores identically, which the engines assert rather than say.
        seat_share=_share(context),
        payable=Payable(_share(context)),
        club=ClubSnapshot(
            travel_minutes=TRAVEL_UNMEASURED,
            zone=context.club.zone,
            crowding=context.club.crowding,
        ),
        # No context owns ladders — the word is not in the shared glossary and
        # ``LadderQualification`` says so itself. A player in no ladder has no
        # ladder problem, which is what the constraint rule means: the term
        # scores full marks, keeps its weight, and Coverage is untouched. The
        # alternative, ``OUTSIDE``, would be the platform docking every match on
        # a ladder nobody has entered.
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=_hold(context, now),
        join_cutoff=_to_the_minute(deadlines(record).join_cut),
    )


def _pairs(
    context: MatchScoringContext,
) -> tuple[tuple[Seat, Occupant | None], ...]:
    """The record's seats beside the context's occupants, one pair per seat.

    **Strict**, so a context whose people have drifted out of step with the
    record's seats is refused rather than silently reconciled. Zipping loosely
    would truncate a *longer* occupant list to the right number of seats, which
    the snapshot's own seat-count check could then never see — one seat's rating
    attached to the wrong person, on the largest term in the fit table. The
    ``ValueError`` lands inside ``Unscorable``, so it degrades a shelf rather
    than 500-ing a home screen.
    """

    return tuple(zip(context.record.seats, context.occupants, strict=True))


def _seat(seat: Seat, occupant: Occupant | None) -> SeatSnapshot:
    """One seat, with its state and its occupant made to agree.

    The record carries the commitment and never a person; the context carries
    the person and never a commitment. The snapshot refuses a seat where the two
    disagree, so this is the one place they are put together — an occupant on a
    seat the record calls empty is a caller's bug and arrives as one.
    """

    if not seat.taken:
        # Passed through rather than dropped, so the snapshot refuses the
        # disagreement. Dropping it here would make every count downstream
        # quietly wrong instead of loudly.
        return SeatSnapshot(state=SeatState.EMPTY, occupant=occupant)
    return SeatSnapshot(
        state=SeatState.PAID if seat.paid else SeatState.HELD, occupant=occupant
    )


def _share(context: MatchScoringContext) -> SeatShare:
    return SeatShare(grosze(int(context.share.amount)))


def _hold(context: MatchScoringContext, now: Instant) -> CourtHold:
    """The kernel's composed hold, in the engines' own three-value vocabulary.

    Two enums with the same three members and no shared declaration, because one
    is the kernel's answer and the other is an engine's input contract; they meet
    here, by value, in one line. That is the mapper ADR-0022 permits between two
    layers that may not import each other, rather than the second spelling of one
    fact it refuses inside one.
    """

    return CourtHold(court_hold(context.record, now).kind.value)


def _to_the_minute(moment: Instant) -> Instant:
    return instant(moment.replace(second=0, microsecond=0))


@final
class MatchScorer:
    """Pairing, then Match Fit, then the badge. One analysis, one score.

    Holds the two engine **abstractions** and never a version, so swapping
    ``matchfit/v1`` for a later lineage — or for an implementation behind HTTP —
    is a line in the composition root (ADR-0015).
    """

    def __init__(
        self, *, pairing: BalanceForecastEngine, matchfit: MatchFitEngine
    ) -> None:
        self._pairing = pairing
        self._matchfit = matchfit

    def score(
        self,
        context: MatchScoringContext,
        *,
        viewer: Occupant,
        now: Instant,
    ) -> tuple[MatchFitScore, PairingAnalysis]:
        """Score one match, or raise ``Unscorable`` and let the shelf degrade.

        Every failure the engines can produce is one shape here — a broken
        precondition, a snapshot the assembler built wrongly, an arithmetic
        error — because a shelf cannot render *some* of a ranking. Narrowing this
        to particular exception types would let a new one through as a 500 on a
        home screen, which is the one place a scorer's outage must not land.
        """

        # **The engines are given the minute and the kernel is given the
        # instant**, and that is not tidiness. Both engines refuse a ``now``
        # carrying seconds — *"a coordinate read off an instant carrying seconds
        # is silently one minute early"* — and a composed screen's clock is
        # ``SystemClock``, which reads microseconds. Left alone, every live
        # compose raises, every raise is an ``Unscorable``, and **every screen in
        # the product degrades** with a badge-less shelf and nothing on the wire
        # saying so. It is invisible to a unit suite, whose fixtures are all
        # minute-aligned by construction.
        moment = _to_the_minute(now)
        try:
            snapshot = snapshot_for(context, viewer=viewer, now=now)
            analysis = self._pairing.analyse(snapshot=snapshot, now=moment)
            score = self._matchfit.score(
                snapshot=snapshot,
                profile=profile_for(context.match_id),
                analysis=analysis,
                now=moment,
            )
        except Exception as failure:  # noqa: BLE001 — the degrade signal
            raise Unscorable(str(failure)) from failure
        return score, analysis


def badge_from(
    score: MatchFitScore,
    analysis: PairingAnalysis,
    *,
    rated: bool,
    travel_measured: bool,
) -> Fit | None:
    """The pill, its reasons and its aim — or nothing at all.

    **Omitted for a viewer with no rating in that sport**, which is ADR-0037's
    rule with its key corrected: the specification keyed on a null score the
    engine never returns, and an unrated viewer scores 91 at 62 % coverage in a
    good match. Skill overlap is the largest term in the table and is the one
    thing missing for her, so printing 91 is the flattery-through-absence
    ADR-0027 exists to remove. **The score still ranks her list** — only the
    claim is withheld.

    ``unsure`` is the engine's own warning restated as a boolean. The threshold
    is not spelled here: the engine fires the warning on the *raw* value of the
    lowest contributor, so a retune moves the card and the score together.

    **Coverage is not on the returned value and never is.** It ranks, it gates
    emphasis, and it may become words in a reason line; it never becomes a
    second gauge on a card that has to be decidable at a glance.

    **A travel reason is withheld while travel is unmeasured**, and that is the
    line the sentinel above may not cross. Being a constraint term, travel scores
    full marks for every candidate whatever ``TRAVEL_UNMEASURED`` is, so it moves
    no score and no order — which is what makes ranking with it honest. A
    *reason* is a different thing: it is a number printed on a card, and *"20
    minutes away"* drawn from a sentinel is a claim about a journey nobody
    measured. So the term keeps its weight and loses its voice, and the day
    ``distance_km`` has a source (#102, ADR-0063) this argument becomes one
    boolean at one call site.
    """

    if not rated:
        return None
    reasons = tuple(
        term
        for term in score.reasons
        if travel_measured or term.code is not TermCode.TRAVEL
    )
    return Fit(
        score=clamp_badge(score.fit),
        unsure=score.warning is not None,
        reasons=tuple(_reason(term) for term in reasons[:REASON_CAP]),
        target=_target(analysis),
    )


def _reason(term: ScoredTerm) -> FitReason:
    """One reason, carrying the engine's own fact object and nothing added.

    The fact is passed through by identity rather than copied, which is what
    makes the card's *"38 zł, under your 45 zł ceiling"* provably the price the
    score was computed from — the engine asserts the same thing with ``is`` one
    layer down, and a copy here would break the chain quietly.
    """

    return FitReason(code=term.code, fact=term.fact)


def _target(analysis: PairingAnalysis) -> float | None:
    """The aimed-at Level, **only when it is precise**.

    The seat target is the exact Level that would even this match and exists only
    while one seat is open; the target band is the fallback and is nearly always
    the viewer's own band restated. Printing a band would be the card telling her
    what she already knows in the voice of a measurement, so only the first
    crosses — and the fallback is not reached rather than being reached and
    dropped, which is why this reads the one result and never the other.
    """

    seat_target = analysis.seat_target
    return float(seat_target.value) if isinstance(seat_target, Ok) else None
