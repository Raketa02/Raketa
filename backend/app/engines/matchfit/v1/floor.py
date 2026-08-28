"""Stage 5 — the quality floor, and the minimum evidence beside it.

``QUALITY_FLOOR`` is the Fit below which a candidate is **not shown at all**, and
it is defined by the six judged pairings it must satisfy rather than by an
integer. The integer is read off them on the day-one basis, and the bound the six
leave is arithmetic — ``max(Fit | not shown) < QUALITY_FLOOR ≤ min(Fit | shown)``,
re-derived at release time by ``make judged-pairings`` and red when the configured
integer leaves it.

**One floor, both modes, every sport, never relaxed at any rung** — and the
signature is where that is said, not a paragraph. :func:`admits` takes no mode,
no sport and no rung, so there is no expression in this module for a bar that
moved for whichever pool is thin. Each extra dimension would be another place the
bar could be lowered quietly.

**One carve-out, and it is a person rather than a pool.** An interest lift — a
human's own *Let's play* — may admit a candidate who is below the bar, with its
reason printed (``docs/adr/0099`` as amended). That is not the floor moving: the
bar is the same integer for everybody, and what outranks it is somebody having
already said yes to this exact searcher. The newcomer-window and zero-exposure
lifts **reorder and never admit**, because exposure fairness is not a reason to
show somebody a bad evening — and the difference is visible here, where one of
the three is a parameter and the other two are not.

**Minimum evidence is a gate, never a score adjustment.** The floor is a fixed
bar over a score whose ingredients vary per comparison, so at the bar *giving
nothing* would become a small advantage over giving something mediocre: a
candidate on whom four terms stood down renormalises the survivors up to a
hundred and can clear a bar a fully-read candidate misses. The gate refuses that
without touching anybody's number.

**Today it excludes nobody, and that is the point.** Reliability is the one term
absent platform-wide, so the live set is seven and four of them must fire — and
every candidate the index can produce reads level, balance and distance from
facts it holds for everybody, plus at least one of intent, availability and the
two tag columns. It is standing insurance, in place before the day *we know
nothing about this person* could quietly become a passing score.

**Its one exemption is the newcomer window, and the window bends nothing else.**
Not the floor, not a gate, not a block. That exemption is why the window exists:
the moment ``player_score`` and ``matches`` land, the person with a
person-specific gap is exactly the newcomer, and minimum evidence would become a
newcomer exclusion on the day it started working. It is written now, while the
gate is inert, because the day it starts biting is the day it bites *them*.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import final

from app.engines.matchfit.core import Term
from app.engines.matchfit.ranking import ModifiedFit
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import invariant


class Refusal(str, Enum):
    """Why a candidate who was scored is not shown.

    Two reasons and not one, because the two are different facts about the
    product and the telemetry separates them: *the bar is in the right place and
    this pairing is poor* against *we do not know enough about this person to
    say*. Collapsing them would make the floor's own falsifier — the near-miss
    band — a mixture of two populations.
    """

    BELOW_QUALITY_FLOOR = "BELOW_QUALITY_FLOOR"
    TOO_LITTLE_EVIDENCE = "TOO_LITTLE_EVIDENCE"


@final
@dataclass(frozen=True, slots=True)
class Admission:
    """Whether this candidate is shown, and what the evidence gate saw.

    ``live`` and ``fired`` travel because the fraction alone is unreadable a year
    later: *four of seven* means one thing while reliability is absent
    platform-wide and another the day it lands, and the gate is deliberately
    expressed as a fraction so that turning a term on moves the bar with it.
    """

    refusal: Refusal | None
    #: The platform's live terms, in ``Term``'s own declaration order.
    live: tuple[Term, ...]
    #: Which of those fired **for this specific person**.
    fired: tuple[Term, ...]

    @property
    def admitted(self) -> bool:
        return self.refusal is None

    @property
    def evidence_fraction(self) -> float:
        """How much of the platform's live evidence this pairing produced."""

        return len(self.fired) / len(self.live)


def live_terms(ruleset: Ruleset, absent: frozenset[Term]) -> tuple[Term, ...]:
    """The terms live **for the platform**, in ``Term``'s own order.

    A term carrying weight in neither mode is live nowhere and is not counted
    against anybody; ``absent`` is the second half of the same idea — a term
    weighted here whose provider does not exist yet, which today is reliability
    alone. The gate counts **person-specific gaps and never platform-wide
    absence**, and this is the line where the difference is drawn: a fact nobody
    has about anybody cannot be evidence this person failed to produce.

    ``absent`` is an argument rather than something read off the ruleset because
    *no provider exists* is a fact about the composition root, not about the
    numbers. A ruleset that could declare it would be a weight release deciding
    which contexts are built.
    """

    weighted = tuple(
        term
        for term in Term
        if any(rules.weights[term] != 0 for rules in ruleset.modes.values())
    )
    unknown = absent - set(weighted)
    invariant(
        not unknown,
        f"a term absent platform-wide that no mode weights: "
        f"{sorted(term.value for term in unknown)}",
    )
    return tuple(term for term in weighted if term not in absent)


def admits(
    modified: ModifiedFit,
    ruleset: Ruleset,
    absent: frozenset[Term],
    newcomer: bool = False,
    interest_received: bool = False,
) -> Admission:
    """Whether this candidate reaches a screen at all.

    **The gate runs before the bar.** A pairing that produced too little evidence
    has a Fit that cannot be compared to a fixed bar in the first place — that is
    the whole argument for the gate — so refusing it as *below the floor* would
    record the wrong fact about it in the one place the floor's falsifier reads.

    The number the bar reads is the **modified** Fit: the reliability dock exists
    to push somebody under the floor, and a bar reading the unmodified score
    would make it decorative.

    ``newcomer`` exempts a candidate from the **evidence gate and from nothing
    else** — the bar below is reached whatever it says, and there is no third
    branch it could take. That is the window's whole licence: it may excuse a
    person-specific gap, and it may not lower a bar for anybody.

    ``interest_received`` is the mirror image, and the two exemptions are
    deliberately **disjoint**: this one clears the bar and never the evidence
    gate. A yes says *I want to play this person*, which outranks the engine's
    opinion of the pairing; it says nothing about whether the platform knows
    enough to have an opinion, and admitting a candidate the engine cannot score
    would put a Fit on a screen that is not comparable to the one beside it. So a
    lifted candidate on whom too little fired is still refused, with the reason
    the telemetry can read.
    """

    live = live_terms(ruleset, absent)
    read = {scored.term for scored in modified.fit.terms}
    fired = tuple(term for term in live if term in read)
    provisional = Admission(refusal=None, live=live, fired=fired)
    thin = provisional.evidence_fraction < ruleset.floors.minimum_evidence_fraction
    if thin and not newcomer:
        return replace(provisional, refusal=Refusal.TOO_LITTLE_EVIDENCE)
    if modified.points < ruleset.floors.quality_floor and not interest_received:
        return replace(provisional, refusal=Refusal.BELOW_QUALITY_FLOOR)
    return provisional
