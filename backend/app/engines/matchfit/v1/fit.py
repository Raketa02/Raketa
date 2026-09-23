"""Fit: the eight terms renormalised into one number out of a hundred.

**The renormalisation basis is part of the answer, not a diagnostic.** A term
that stands down is dropped from the sum and the survivors renormalise *per
comparison*, so a 78 built on four terms and a 78 built on seven are different
readings of the same number — and without ``degraded_terms`` beside it a Fit is
uninterpretable a year later. That is why the basis is a field on the result
rather than a line in a log.

**``score`` never learns ``absent``.** Which providers this platform has built is
a fact about the composition root, and handing it to the arithmetic would put the
ruleset-diff corpus at the mercy of which contexts exist. So a stand-down leaves
here carrying whichever side of the pairing was empty, and a term with no
provider at all is restated one layer out, in ``floor.py``.

**The engine ranks the reasons; the client picks how many to show.** The ordering
is arithmetic — contribution, descending — and is not the client's. So is
``concerns``: what counts as a genuinely weak term is a judgement about weights
and curves and belongs where the weights and curves are, and a client
thresholding a value would be that judgement in TypeScript, written differently
in every client. **The cap is the client's**: a card shows one, *Why 78?* shows
all of them.

**The printed score is Fit only.** There is no field here a Liveness offset could
be written to and no operation that combines the two — ranking is the only place
they meet, and it produces a third quantity that is never serialised. The printed
Fit stops meaning what it says the moment it silently contains *"they open the
app a lot"*.

**Ties break on a fact and never on a set** (``docs/adr/0105``). Terms sort on
contribution and then on ``Term``'s own declaration order, so two terms
contributing the same amount come back in the same order on every process,
whatever ``PYTHONHASHSEED`` is.
"""

from __future__ import annotations

from typing import Mapping, Sequence, TypeVar, final

from app.engines.matchfit.core import Seat, Term
from app.engines.matchfit.ruleset import WEIGHT_TOTAL, Ruleset
from app.engines.matchfit.scorable import ScorableCandidate, Searcher
from app.engines.matchfit.scoring import Fit, ScoredTerm, StoodDown
from app.engines.matchfit.v1.engine import ENGINE_VERSION
from app.engines.matchfit.v1.terms import TermReading, read_terms
from app.kernel import invariant

#: Where each term sits in the enum, so a tie breaks on a declaration and never
#: on a dictionary's iteration order.
_TERM_ORDER = {term: position for position, term in enumerate(Term)}

#: What a renormalisation is over. The rule below is about *a weight vector*
#: rather than about the eight terms of Fit — the group objective renormalises
#: its six the same way, and a cross reading renormalises three of Fit's own —
#: so the function is written once over whatever the vector is keyed by.
_Weighted = TypeVar("_Weighted")


def score(
    searcher: Searcher,
    candidate: ScorableCandidate,
    ruleset: Ruleset,
    seat: Seat = Seat.OPPONENT,
    *,
    stood_down: frozenset[Term] = frozenset(),
) -> Fit:
    """Score one already-gated, already-fenced candidate.

    The default seat is ``OPPONENT`` because that is what *unseated* reads as: a
    singles pairing and a doubles candidate nobody has seated yet take the more
    forgiving reading, and the harsher partner rows apply only once the line-up
    is seating somebody.

    ``stood_down`` names the terms **this search** declines to read, for every
    pairing — the deck's intent term (``docs/adr/0169`` §2). Each stands down
    by the mechanism a term already uses when it has nothing to read, so its
    weight renormalises away and a declaration moves nobody. The default is
    the empty set: a caller that stands nothing down gets exactly the Fit it
    always got, which is what keeps every pinned pairing pinned.

    Raises ``InvariantViolated`` if every term stands down. That is not a low
    Fit — it is no Fit, and returning a number for it would be the invented zero
    this engine is built to refuse. It is unreachable on today's inputs: level
    fit and distance read facts every candidate in the index has.
    """

    weights = ruleset.modes[searcher.mode].weights
    outcomes = read_terms(searcher, candidate, ruleset, seat, stood_down=stood_down)
    live: list[TermReading] = [
        outcome for outcome in outcomes if isinstance(outcome, TermReading)
    ]
    # In ``Term``'s own order, because ``read_terms`` answers in it — a basis is
    # a set and an order read off one is an order read off a set
    # (``docs/adr/0105``).
    degraded = tuple(
        outcome for outcome in outcomes if isinstance(outcome, StoodDown)
    )

    invariant(
        bool(live),
        f"every term of Fit stood down for candidate {candidate.player_id}: a Fit "
        f"over no evidence is not a low Fit, it is not a Fit",
    )
    shares = renormalised_weights(weights, tuple(reading.term for reading in live))
    scored = tuple(
        ScoredTerm(
            term=reading.term,
            weight=shares[reading.term],
            value=reading.value,
            contribution=shares[reading.term] * reading.value,
            evidence=reading.evidence,
        )
        for reading in live
    )
    return Fit(
        points=sum(term.contribution for term in scored),
        terms=_by_contribution(scored),
        degraded_terms=degraded,
        concerns=_concerns(scored, ruleset),
        engine_version=ENGINE_VERSION,
        ruleset_version=ruleset.version,
    )


def renormalised_weights(
    weights: Mapping[_Weighted, int], live: Sequence[_Weighted]
) -> Mapping[_Weighted, float]:
    """Each live term's share of a hundred, over the terms that actually fired.

    A mode's weights sum to a hundred *before* this, so a term standing down does
    not shrink the Fit — it redistributes its weight over the survivors. That is
    exactly why the basis has to travel with the answer: the same pairing scores
    differently the day a term turns on platform-wide, and nothing about the two
    people changed.

    Named and public rather than inlined into ``score`` because it is the one
    piece of this file with a property worth stating over the **whole** space
    rather than over the subsets today's inputs happen to reach: for every subset
    of the eight, in either mode, the shares sum to a hundred. Three terms cannot
    stand down on today's inputs, and a renormalisation only ever exercised on
    the subsets that can is one that breaks the day reliability turns on.

    **Generic in what the vector is keyed by**, because the rule is about a
    weight vector and not about the eight terms: the group objective renormalises
    its six the same way, and a cross reading renormalises three of Fit's own
    over their day-one basis — *"it invents no constant"* is that sentence, and a
    second copy of this function is where it would stop being true.
    """

    basis = sum(weights[term] for term in live)
    invariant(
        basis > 0,
        f"a renormalisation over no weight at all: {[str(term) for term in live]}",
    )
    return {term: weights[term] * WEIGHT_TOTAL / basis for term in live}


def _by_contribution(scored: tuple[ScoredTerm, ...]) -> tuple[ScoredTerm, ...]:
    """The reasons, ranked. Ties break on ``Term``'s declaration order."""

    return tuple(
        sorted(scored, key=lambda term: (-term.contribution, _TERM_ORDER[term.term]))
    )


def _concerns(scored: tuple[ScoredTerm, ...], ruleset: Ruleset) -> tuple[Term, ...]:
    """Which terms are weak enough to be worth a line, ranked by what they cost.

    The judgement is over **points forgone** — ``weight × (1 − value)`` — rather
    than over the raw value, because weakness is a property of the pairing and
    not of the term. A social vibe of 0.20 costs under four points of a
    competitive match and nearly twenty of a friendly, and only one of those is
    worth warning anybody about. Reading the renormalised weight makes that fall
    out of the arithmetic instead of needing a second table.

    A term that stood down is not a concern. It produced no reading, so there is
    nothing to be weak about — it is in ``degraded_terms``, which is a different
    statement and already travels.
    """

    bar = ruleset.explanation.concern_points
    forgone = [(term.weight * (1.0 - term.value), term.term) for term in scored]
    weak = [(cost, term) for cost, term in forgone if cost >= bar]
    weak.sort(key=lambda pair: (-pair[0], _TERM_ORDER[pair[1]]))
    return tuple(term for _, term in weak)


@final
class MatchFitV1:
    """Version 1 of the scorer, as the ``MatchFit`` Protocol sees it.

    A thin object over ``score`` and not a second implementation of it: the
    arithmetic stays a free function so a test can call it without constructing
    anything, and the class exists so a module can depend on the abstraction
    rather than on this directory's name (``docs/adr/0015``).
    """

    @property
    def version(self) -> str:
        return ENGINE_VERSION

    def score(
        self,
        *,
        searcher: Searcher,
        candidate: ScorableCandidate,
        ruleset: Ruleset,
        seat: Seat = Seat.OPPONENT,
        stood_down: frozenset[Term] = frozenset(),
    ) -> Fit:
        return score(searcher, candidate, ruleset, seat, stood_down=stood_down)
