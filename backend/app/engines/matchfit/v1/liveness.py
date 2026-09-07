"""Stage 6 — Liveness: what reorders the list without ever entering the number.

``rank_key = fit + liveness_offset``, and **``rank_key`` is never shown and never
crosses the wire in any shape**. That separation is what lets the card's 78 stay
a fact about the pairing while the ordering still knows who answered quickly last
week — and it is why :func:`app.engines.matchfit.ranking.rank_key` returns a bare
float rather than a type something could serialise.

**Every signal goes through one funnel.** :func:`read_signals` asks the ruleset
whether a signal is printable and routes it into ``Printable`` or ``Silent``
accordingly; nothing downstream re-decides. The offset is then a derived property
of ``Liveness``, so there is no path to one that skipped the silent budget.

**How each signal is priced, and why only one of them reads a measurement.** Four
are flags — a live *Let's play*, a newcomer, a previous accept, a previous
decline — and their bounds are flat, so the bound *is* the value. Four are ramps
and arrive as a reading in ``[0, 1]``, priced linearly across the signal's own
bound: the curve from *days since they last opened the app* to a reading is a
measurement and belongs on the other side of the fence with the clock, and
putting it here would mean inventing a threshold per signal in the one file whose
whole discipline is that every number carries a falsifier. The full inbox is the
exception and is the exception **on purpose** — its three thresholds were
measured and published (§14.4), and ``docs/adr/0125`` adopted them whole. The
tenth, reciprocal asymmetry, is arithmetic over two Fits and reads nothing at
all.

**The absorption cap does not reach this stage, and the reason is which people
each thing is about.** ``NEWCOMER_ABSORPTION_CAP`` bounds how often the engine
volunteers an **experienced** player into newcomers' lists, so it binds the
thumb that selects those players — the welcoming record, one stage back. This
lift fires only for a candidate who is *themselves* inside the window, so
capping it would take the subsidy from the population the cap exists to protect
them from carrying. It is a flag over one fact and stays one.

**Points are whole numbers.** Every bound in the roster is an integer, so is
``MOVE_NOTICE``, and the printing guarantee is an inequality over them — a
fractional offset would make *moved more than six* depend on a rounding nobody
wrote down. Halves round away from zero, so the rule is the same in both
directions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.engines.matchfit.core import ChallengeLoad, LivenessSignal, SearchMode
from app.engines.matchfit.ranking import (
    Liveness,
    LivenessMove,
    Printable,
    Reciprocal,
    Silent,
)
from app.engines.matchfit.ruleset import IntentRules, LivenessRules, Ruleset
from app.engines.matchfit.scorable import LivenessFacts
from app.kernel import invariant


@final
@dataclass(frozen=True, slots=True)
class SignalReading:
    """One signal's answer, before the funnel decides whether it prints.

    Named rather than left as a tuple so that it reads like its neighbours one
    stage over — ``TermReading`` and ``ModifierPoints`` — and so that the roster
    check below asks ``reading.signal`` rather than ``outcome[0]``. ``prints`` is
    the full inbox's coarse code and is ``None`` everywhere else.
    """

    signal: LivenessSignal
    points: int
    prints: ChallengeLoad | None = None


#: A signal either moved somebody or it did not. **Not firing is spelled
#: ``None``**, the same way a term standing down is: a signal priced at zero
#: moved nobody and is not a reason anybody is owed, and *we did not look* and
#: *we looked and it was neutral* are separated where the difference is
#: usable — in the recorded signal values, on the other side of the fence.
SignalOutcome = SignalReading | None


def read_signals(
    facts: LivenessFacts,
    ruleset: Ruleset,
    reciprocal: Reciprocal | None = None,
) -> Liveness:
    """Every signal's outcome, funnelled into printable and silent.

    **The funnel is here and the roster is the ruleset's.** Which signals print
    is ``SignalBound.printable``, pinned by a roster test at exactly two silent
    ones; this function never decides it, so a third silent signal is a ruleset
    decision that the roster test refuses rather than a branch somebody adds.

    ``reciprocal`` is ``None`` everywhere except the shortlist. The reverse Fit
    is computed **after the floor**, over twenty to forty rows rather than the
    whole pool, so it costs almost nothing — and a stage that ran it earlier
    would be scoring the candidates the floor is about to discard.

    **The reverse pairing is assembled by the module and not here**, and that is
    the fence rather than an omission. ``fit_ba`` is ``score()`` run with the two
    sides swapped, and swapping them needs facts about the *searcher* that do not
    cross into a ``ScorableCandidate`` — their id, their own declaration, their
    own Player Score, their area. The module holds all four because it holds the
    I/O; an engine-side wrapper would be a second name for ``score`` with nothing
    of its own to say. What is engine vocabulary is which weight vector the
    reverse runs under (:func:`reverse_mode`) and what a shortfall costs
    (:func:`reciprocal_asymmetry`), and both are here.
    """

    rules = ruleset.liveness
    outcomes: tuple[SignalOutcome, ...] = (
        _flag(
            LivenessSignal.INTEREST_RECEIVED, facts.interest_days_ago is not None, rules
        ),
        _flag(LivenessSignal.PREVIOUS_ACCEPT, facts.previously_accepted, rules),
        _ramp(LivenessSignal.ANSWER_RATE_AND_SPEED, facts.answer_rate, rules),
        _ramp(LivenessSignal.RECENT_ACTIVITY, facts.recent_activity, rules),
        _ramp(LivenessSignal.OVERLAP_PROXIMITY, facts.overlap_proximity, rules),
        challenge_load(facts.open_challenges, rules),
        reciprocal_asymmetry(reciprocal, rules),
        _flag(LivenessSignal.PREVIOUS_DECLINE, facts.previously_declined, rules),
        _flag(LivenessSignal.NEWCOMER_LIFT, facts.newcomer, rules),
        _ramp(LivenessSignal.EXPOSURE_ADJUSTMENT, facts.exposure, rules),
    )
    invariant(
        len(outcomes) == len(LivenessSignal),
        f"a liveness signal is never read: {len(outcomes)} of {len(LivenessSignal)}",
    )
    for signal, outcome in zip(LivenessSignal, outcomes, strict=True):
        invariant(
            outcome is None or outcome.signal is signal,
            f"the outcome in {signal.value}'s position answers for "
            f"{outcome.signal.value if outcome else None}",
        )
    return Liveness.of(
        (_funnel(reading, rules) for reading in outcomes if reading is not None), rules
    )


def _funnel(reading: SignalReading, rules: LivenessRules) -> LivenessMove:
    """The one place a signal becomes printable or silent.

    A ``Silent`` carries points and **no code**, which is ``docs/adr/0123``'s
    type verbatim: a signal that never prints cannot be named as the reason
    somebody moved, because there is no name on the value to name.
    """

    if rules.signals[reading.signal].printable:
        return Printable(
            signal=reading.signal, points=reading.points, load=reading.prints
        )
    invariant(
        reading.prints is None,
        f"{reading.signal.value} is silent and carries a code to print: "
        f"{reading.prints}",
    )
    return Silent(points=reading.points)


def _flag(signal: LivenessSignal, fired: bool, rules: LivenessRules) -> SignalOutcome:
    """A signal that is on or off, priced at its own flat bound.

    **Flatness is checked rather than assumed.** A ruleset that gave one of these
    a range would otherwise be read at its maximum silently — and the interest
    lift is flat for a reason ``docs/adr/0127`` argues at length: the age of the
    yes already crosses as evidence, so a taper charges one fact twice, once
    visibly and once not.
    """

    bound = rules.signals[signal]
    invariant(
        bound.points.minimum == bound.points.maximum,
        f"{signal.value} is read as a flag and bounded as a ramp: "
        f"{bound.points.minimum}…{bound.points.maximum}",
    )
    if not fired:
        return None
    return SignalReading(signal=signal, points=bound.points.maximum)


def _ramp(
    signal: LivenessSignal, reading: float | None, rules: LivenessRules
) -> SignalOutcome:
    """A signal that arrives as a reading in ``[0, 1]``, priced across its bound.

    Linear, and deliberately so: a curve here would be a second shape for the
    same fact, invented on this side of the fence where nothing could falsify it.
    What the product may tune is the bound, which is ruleset data and carries a
    falsifier.
    """

    if reading is None:
        return None
    bound = rules.signals[signal].points
    points = _rounded(bound.minimum + reading * (bound.maximum - bound.minimum))
    if points == 0:
        return None
    return SignalReading(signal=signal, points=points)


def challenge_load(open_challenges: int | None, rules: LivenessRules) -> SignalOutcome:
    """The full-inbox sink: the deepest rung this inbox reaches, and its code.

    ``docs/adr/0125`` **deleted** the withholding at eight open challenges — an
    exclusion is a gate, and the gate roster is enumerated and closed — and
    adopted §14.4's three thresholds whole as this sink, changing only the
    third's effect. The measurement is of the *candidate's* inbox while the cost
    is paid by everyone searching, and no relaxation rung reaches a gate.

    **It prints as a coarse code and never the number.** Their inbox depth is
    theirs; what a searcher is owed is *they have a lot on*.
    """

    if open_challenges is None:
        return None
    reached = [
        rung for rung in rules.challenge_load_rungs if open_challenges >= rung.at_least
    ]
    if not reached:
        return None
    deepest = reached[-1]
    return SignalReading(
        signal=LivenessSignal.CHALLENGE_LOAD,
        points=deepest.points,
        prints=deepest.prints,
    )


def reciprocal_asymmetry(
    reciprocal: Reciprocal | None, rules: LivenessRules
) -> SignalOutcome:
    """``dock = −min(bound, max(0, fit_ab − fit_ba − tolerance) × slope)``.

    A candidate whose own Fit for the searcher is far lower is a bad bet for the
    searcher, and that is priced **proportionately** rather than as a flat
    charge. The tolerance is the head start: a shortfall inside it is ordinary
    asymmetry — availability's denominator is the searcher's grid and distance
    runs against the searcher's ring, so the two directions never agree exactly.

    **The standalone radius dock is struck rather than kept beside this.** The
    searcher being outside the candidate's ring is already inside ``fit_ba``,
    through the candidate's own distance term against the candidate's own radius,
    and charging it again here was the same fact priced twice.
    """

    if reciprocal is None:
        return None
    bound = rules.signals[LivenessSignal.RECIPROCAL_ASYMMETRY].points
    shortfall = max(
        0.0, reciprocal.fit_ab - reciprocal.fit_ba - rules.asymmetry_tolerance
    )
    points = _rounded(max(float(bound.minimum), -(shortfall * rules.asymmetry_slope)))
    if points == 0:
        return None
    return SignalReading(signal=LivenessSignal.RECIPROCAL_ASYMMETRY, points=points)


def reverse_mode(
    searcher: SearchMode, declared_intent: str | None, intent: IntentRules
) -> SearchMode:
    """Which weight vector the candidate's own Fit for the searcher runs under.

    A candidate who declared the kind of evening one of the modes reads as *its
    own* is judged under that mode. **Everybody else inherits the searcher's** —
    which is the whole of ``NO_PREFERENCE``'s rule: it is indifferent about the
    kind of evening, so the game being proposed is the game it would be judging.
    ``NO_PREFERENCE`` never selects a weight vector, it inherits one, and
    ``SearchMode`` having two values while a declaration has three is what makes
    that a type error rather than a paragraph.

    The mapping is read from ``IntentRules.same_evening`` rather than by
    comparing two enums' spellings, because the two enums are deliberately
    different types and a shared spelling is a coincidence the arithmetic must
    not lean on.
    """

    for mode, declaration in intent.same_evening.items():
        if declaration == declared_intent:
            return mode
    return searcher


def _rounded(points: float) -> int:
    """A signal's points as a whole number, halves away from zero.

    Away from zero in both directions rather than to even, so that *moved more
    than the notice threshold* means one thing whichever way somebody moved.
    """

    return int(points + 0.5) if points >= 0 else -int(-points + 0.5)
