"""What stages 4 and 6 produce, and the one quantity that is never serialised.

``scoring`` holds the answer stage 3 returns. This holds the two answers that sit
either side of the quality floor — the modifier stack that adjusts the printed
number, and the Liveness offset that reorders the list without entering it — and
the ``rank_key`` the two of them meet in.

**Fit and Liveness never meet in a type.** ``Fit`` has no field an offset could be
written to and no arithmetic on it; ``Liveness`` has no ``points`` a Fit could be
added to. They meet in exactly one place, :func:`rank_key`, which returns a bare
``float`` — **a quantity with no shape is a quantity with no field**, so there is
nowhere on the wire it could be written even by somebody trying.

**Both stacks are funnels, and the funnel is the type.** ``ModifierStack``
applies the budget and ``Liveness`` applies the silent budget and the offset
bounds, and in both the applied total is a *derived property* rather than a
field: there is no constructor that takes an already-summed number, so there is
no path to a total that skipped its clamp. ``docs/adr/0123`` asks for one
constructor; a property is the same guarantee with nothing to remember.

**What a type cannot do here, and what the tests do instead.** ``|Σ silent| ≤
MOVE_NOTICE`` is a fact about a runtime sum and no type checks it, which is why
``docs/adr/0123`` splits the claim: the type enforces the separation and the
funnel, three property tests enforce the arithmetic. The neighbouring rule — that
nothing adds a Liveness offset to a Fit — *is* genuinely type-enforced, and this
one had been borrowing its credibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, final

from app.engines.matchfit.core import (
    ChallengeLoad,
    LivenessSignal,
    Modifier,
    SearchMode,
)
from app.engines.matchfit.ruleset import (
    WEIGHT_TOTAL,
    LivenessRules,
    ModifierRules,
)
from app.engines.matchfit.scoring import Fit
from app.kernel import invariant

#: Where each signal sits in the enum, so a tie between two equal contributors
#: breaks on a declaration and never on a dictionary's iteration order
#: (``docs/adr/0105``).
_SIGNAL_ORDER = {signal: position for position, signal in enumerate(LivenessSignal)}


# ---------------------------------------------------------------------------
# Stage 4 — the modifiers
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class ModifierPoints:
    """One modifier that fired, and what it was worth on this pairing.

    **Every modifier prints.** There is no printable flag here because there is
    no unprintable modifier: the two that would not have printed — language, and
    the second charge for an opposite intent — are struck rather than silent
    (``ranking-weights.md`` §7). A modifier that could move a score without
    owing a sentence would be Liveness wearing stage 4's clothes, and Liveness
    has a budget for exactly that.
    """

    modifier: Modifier
    points: float


@final
@dataclass(frozen=True, slots=True)
class ModifierStack:
    """The three modifiers inside the budget, and the one dock outside it.

    ``budget`` clamps the **summed stack** and not each modifier, so a stack of
    small positives can never lift somebody over a recent no-show. The clamp is
    applied by :attr:`budgeted` rather than by whoever builds this, which is what
    makes *the budget was applied* a property of the type instead of a step
    somebody remembers.

    **The reliability floor dock is a field of its own and not a fourth entry in
    ``fired``.** It sits outside the budget deliberately — it is a floor, not an
    adjustment, and it is allowed to dominate — and holding it in the same tuple
    would put it inside the clamp the moment anybody summed the obvious thing.
    """

    #: The budgeted modifiers that fired, in ``Modifier``'s own declaration order.
    fired: tuple[ModifierPoints, ...]
    #: The reliability floor breach, when the published Player Score is under the
    #: bar. **Outside the budget**, and derived from it as ``budget + 1``.
    floor_breach: ModifierPoints | None
    #: The budget this stack is held to. Carried so that :attr:`applied` is a
    #: function of its own fields and the ruleset that priced them, and nothing
    #: else — the same reason a ``Fit`` carries the basis it was renormalised on.
    rules: ModifierRules

    def __post_init__(self) -> None:
        invariant(
            len({entry.modifier for entry in self.fired}) == len(self.fired),
            f"a modifier fired twice: {[e.modifier.value for e in self.fired]}",
        )
        invariant(
            self.floor_breach is None
            or self.floor_breach.modifier is Modifier.RELIABILITY_FLOOR_BREACH,
            "the dock outside the budget is the reliability floor breach and "
            f"nothing else: {self.floor_breach}",
        )

    @property
    def stacked(self) -> float:
        """What the budgeted modifiers summed to **before** the budget."""

        return sum(entry.points for entry in self.fired)

    @property
    def budgeted(self) -> float:
        """The stack, held inside ``±budget``."""

        budget = float(self.rules.budget)
        return max(-budget, min(budget, self.stacked))

    @property
    def clamped(self) -> bool:
        """Whether the budget actually bound. Its own falsifier, recorded.

        If it never binds the budget is not doing the work its existence claims;
        if it binds often the modifiers are competing for a budget too small to
        hold them (``ranking-weights.md`` §7).
        """

        return self.budgeted != self.stacked

    @property
    def applied(self) -> float:
        """The whole of what stage 4 moves: the budgeted stack, plus the dock."""

        return self.budgeted + (
            0.0 if self.floor_breach is None else self.floor_breach.points
        )


@final
@dataclass(frozen=True, slots=True)
class ModifiedFit:
    """A Fit and the modifiers applied to it — the number the floor reads.

    **The terms still add up to ``fit.points``.** The modifiers are a second,
    printed list beside them rather than a term nobody weighted, which is what
    keeps *Why 78?* reconcilable: the breakdown's contributions sum to the Fit,
    and each modifier's line says what it added on top.

    **A score out of a hundred is held to a hundred, and the bound is on the
    stack rather than on the total.** A Fit at the very top of the scale plus a
    positive modifier would otherwise print a number the scale does not have —
    but clamping the *total* would leave the printed number smaller than its own
    parts, which is the one thing this stage may not do. So the stack spends what
    the scale has room for and :attr:`points` is an exact sum, always. The two
    only disagree where a pairing is already at one end of the scale, and the
    disagreement has a name — ``modifiers.applied`` against :attr:`applied` —
    rather than being a silent cut in the total.
    """

    fit: Fit
    modifiers: ModifierStack

    @property
    def applied(self) -> float:
        """What the stack actually moved this Fit, once the scale has its say."""

        return max(
            -self.fit.points,
            min(WEIGHT_TOTAL - self.fit.points, self.modifiers.applied),
        )

    @property
    def points(self) -> float:
        """The printed number, after stage 4. **Exactly** the Fit plus the stack."""

        return self.fit.points + self.applied


# ---------------------------------------------------------------------------
# Stage 6 — Liveness
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class Printable:
    """A signal that owes the player a sentence when it moves them.

    ``load`` is the full inbox's **coarse code**, and it is the only payload any
    signal carries here: their inbox depth is theirs, so the code crosses and the
    count does not. It is present exactly when the signal is the challenge load,
    which is a refusal rather than a convention — a second signal quietly
    borrowing the field would be a second thing printed as a band nobody argued.
    """

    signal: LivenessSignal
    points: int
    load: ChallengeLoad | None = None

    def __post_init__(self) -> None:
        carries = self.signal is LivenessSignal.CHALLENGE_LOAD
        invariant(
            carries == (self.load is not None),
            f"{self.signal.value} carries a coarse load code "
            f"{'it may not' if self.load is not None else 'it owes'}",
        )


@final
@dataclass(frozen=True, slots=True)
class Silent:
    """A signal that never prints. **It carries points and no code.**

    ``docs/adr/0123``'s type, verbatim, and the absence of a code is the whole
    of it: a silent signal cannot be named as the reason somebody moved because
    there is no name on the value. Which signals are silent is the **ruleset's**
    roster — ``LivenessRules.silent_signals()`` — pinned by a test at exactly
    two, so identifying them here would be a second answer to a settled question.
    """

    points: int


#: A liveness signal is one or the other and there is no third state. The union
#: is what makes *printable* a property of a value rather than of whoever reads
#: it: nothing downstream re-decides whether a signal owes an explanation.
LivenessMove = Printable | Silent


@final
@dataclass(frozen=True, slots=True)
class Liveness:
    """Everything that moves a candidate's position without moving their Fit.

    ``liveness_offset = Σ printable + clamp(Σ silent, −MOVE_NOTICE, +MOVE_NOTICE)``

    **The silent stack is budgeted per player, on the signed net**, at the same
    threshold that owes an explanation. One constant and not two: the printing
    promise holds only while the budget is at most the notice threshold, and two
    constants can drift apart in a ruleset edit and break it *silently*.

    The promise then falls out of the arithmetic rather than being policed — with
    ``|Σ silent| ≤ move_notice``, any player moved more than ``move_notice`` has a
    printable contributor to name.

    **Nothing here crosses the wire as a number.** What a candidate carries is
    ``fit`` and a list of reason codes; :attr:`offset` exists to be added to a
    Fit inside :func:`rank_key` and nowhere else.
    """

    printable: tuple[Printable, ...]
    silent: tuple[Silent, ...]
    #: The bounds and the notice threshold this offset was computed under. The
    #: clamp is not a fact about the signals alone, and a Liveness that did not
    #: carry it would be a number nobody could re-derive.
    rules: LivenessRules

    @classmethod
    def of(cls, moves: Iterable[LivenessMove], rules: LivenessRules) -> "Liveness":
        """Build one from a stream of moves, splitting them by their own type.

        The split lives here rather than at each caller because it is the same
        two lines everywhere and the day it is written a third time is the day
        one of the copies quietly puts a ``Silent`` in the printable list.
        """

        held = tuple(moves)
        return cls(
            printable=tuple(move for move in held if isinstance(move, Printable)),
            silent=tuple(move for move in held if isinstance(move, Silent)),
            rules=rules,
        )

    @property
    def printable_net(self) -> int:
        """What the printable signals sum to. Never clamped on its own."""

        return sum(move.points for move in self.printable)

    @property
    def silent_net(self) -> int:
        """What the silent signals sum to **before** the budget."""

        return sum(move.points for move in self.silent)

    @property
    def applied_silent(self) -> int:
        """The silent net, held inside ``±move_notice``.

        The bound is on the signed net rather than on the summed magnitude,
        because the only thing a searcher can observe is position and position is
        the net: a −6 decline beside a +6 exposure adjustment nets to zero, and
        there is nothing to explain.
        """

        notice = self.rules.move_notice
        return max(-notice, min(notice, self.silent_net))

    @property
    def budget_bound(self) -> bool:
        """Whether the silent budget actually clamped. Re-derived, never stored.

        ``docs/adr/0123``'s falsifier is a query over the recorded signal values
        and the ruleset version rather than a column: if the clamp never binds
        the per-player rule was theoretical, and if it binds often one of the two
        silent signals is miscalibrated.
        """

        return self.applied_silent != self.silent_net

    @property
    def offset(self) -> int:
        """The offset, inside the roster's own bounds. **Never serialised.**"""

        total = self.printable_net + self.applied_silent
        return max(self.rules.offset_minimum, min(self.rules.offset_maximum, total))

    @property
    def reasons(self) -> tuple[Printable, ...]:
        """The printable signals, ranked by how far each moved them.

        The engine ranks and the client picks how many to show, exactly as it
        does for the terms of Fit. Ties break on ``LivenessSignal``'s declaration
        order, so two signals at the same magnitude come back in the same order
        on every process whatever ``PYTHONHASHSEED`` is.
        """

        return tuple(
            sorted(
                self.printable,
                key=lambda move: (-abs(move.points), _SIGNAL_ORDER[move.signal]),
            )
        )

    @property
    def dominant(self) -> Printable | None:
        """The largest printable contributor, or ``None`` when none fired.

        *Dominant* narrows to **printable** on purpose: a silent signal cannot be
        the reason anybody is given, so naming one would be the promise broken in
        the one place it is kept.
        """

        ranked = self.reasons
        return ranked[0] if ranked else None


@final
@dataclass(frozen=True, slots=True)
class Reciprocal:
    """The candidate's own Fit for the searcher, and the mode it ran under.

    The mode travels because it is **not recoverable from the candidate's
    declaration**: a ``NO_PREFERENCE`` candidate inherits the searcher's, so a
    reader a year later cannot work out which weight vector produced ``fit_ba``
    from the row alone.
    """

    fit_ab: float
    fit_ba: float
    mode: SearchMode


def rank_key(modified: ModifiedFit, liveness: Liveness) -> float:
    """``rank_key = fit + liveness_offset``. The one place the two meet.

    **It returns a bare float and that is the point.** ``rank_key`` is never shown
    and never crosses the wire in any shape (``docs/adr/0106`` §5); a quantity
    with no type of its own has no field it could be written to, and the
    assertion that none exists is made centrally over the emitted contract rather
    than route by route.

    The printed Fit is the only number a player is asked to trust, and it stops
    meaning what it says the moment it silently contains *they open the app a
    lot*.
    """

    return modified.points + liveness.offset
