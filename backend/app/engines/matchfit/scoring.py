"""The ``MatchFit`` Protocol, and the answer every version of it returns.

**One ``Protocol`` per engine** (``docs/adr/0015``): a module depends on this
abstraction and never on a concrete version, so swapping ``v1`` for ``v2`` is a
wiring change in the composition root like any other port rather than an edit at
every call site. ``engines/assessment.py`` is the same shape one engine over.

**What lives here is what outlives a version.** ``Fit`` is the answer every
scorer returns; ``scorable`` is what crosses the privacy fence into any of them;
``evidence`` is the closed union the API contract publishes, which
``docs/adr/0106`` makes contract precisely so that it *cannot* be a version's
private business. A version owns the arithmetic and nothing else — which is why
``v1`` holds the terms and the renormalisation and no shape at all.

**Fit and Liveness never meet in a type.** There is no field on ``Fit`` an offset
could be written to and no operation that combines the two; ranking is the only
place they meet, and the quantity it produces is neither a ``Fit`` nor
serialised. The printed Fit is the only number a player is asked to trust, and it
stops meaning what it says the moment it silently contains *"they open the app a
lot"*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable

from app.engines.matchfit.core import DegradedReason, Seat, Term
from app.engines.matchfit.evidence import Evidence
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scorable import ScorableCandidate, Searcher


@final
@dataclass(frozen=True, slots=True)
class ScoredTerm:
    """One term that produced a reading, with what it was worth here.

    ``weight`` is the **renormalised** weight — the term's share of a hundred
    over the terms that actually fired — and ``contribution`` is that weight
    times the value. Both travel, because *Why 78?* is the moment the product's
    central claim is tested and a breakdown that does not add up is the claim
    failing.
    """

    term: Term
    weight: float
    value: float
    contribution: float
    evidence: Evidence


@final
@dataclass(frozen=True, slots=True)
class StoodDown:
    """One term that produced no reading, and **whose gap that is**.

    It lives here rather than in a version because it is half of ``Fit`` — the
    renormalisation basis — and a version owns the arithmetic and nothing else.
    ``TermReading``'s opposite number: the two together are what a term function
    may answer, and there is no third value.

    **The reason has two authors and one of them is not a term function.** A term
    knows which side was empty and can never know that its provider does not
    exist, because ``absent`` is a fact about the composition root. So a term in
    ``absent`` is overwritten one layer out (``v1/floor.py``), where the same
    argument already decides ``Admission.live``.
    """

    term: Term
    reason: DegradedReason


@final
@dataclass(frozen=True, slots=True)
class Fit:
    """A candidate's Fit, and the whole of the working behind it.

    ``points`` is the printed number and the only one a player is asked to trust.
    There is deliberately no arithmetic on this type: nothing adds to it and
    nothing combines it with anything else.
    """

    points: float
    #: Every term that fired, **ranked by contribution** — the reasons, in the
    #: order the arithmetic puts them in. Uncapped; the cap is the client's.
    terms: tuple[ScoredTerm, ...]
    #: The terms that stood down, each with whose gap it is: the renormalisation
    #: basis, without which the number above cannot be read a year later. In
    #: ``Term``'s own declaration order, because a basis is a set and an order
    #: read off one is an order read off a set (``docs/adr/0105``).
    degraded_terms: tuple[StoodDown, ...]
    #: The engine's own statement that a term is genuinely weak, ranked by the
    #: points it costs.
    concerns: tuple[Term, ...]
    engine_version: str
    ruleset_version: str


@runtime_checkable
class MatchFit(Protocol):
    """A pure, versioned Match Fit scorer.

    It receives an **already-gated, already-fenced** candidate and does the
    arithmetic. Gating and candidate generation live in the module, where the I/O
    is; splitting gates by kind — identity outside, arithmetic inside — was
    rejected, because a fence with a judgement call in it is not a fence.

    Like every engine it reads no clock, draws no randomness and holds no state,
    so the same pairing under the same ruleset scores the same number forever —
    which is what makes a recorded search explainable a year later.
    """

    @property
    def version(self) -> str: ...

    def score(
        self,
        *,
        searcher: Searcher,
        candidate: ScorableCandidate,
        ruleset: Ruleset,
        seat: Seat = Seat.OPPONENT,
        stood_down: frozenset[Term] = frozenset(),
    ) -> Fit: ...
