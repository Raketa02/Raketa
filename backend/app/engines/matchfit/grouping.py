"""What a line-up is, what a forecast is, and what the objective hands back.

``scoring`` holds the answer Fit returns and ``ranking`` the two either side of
the floor. This holds the third: **what the engine returns when it is seating
four people rather than ranking one.** It lives beside them for the same reason
they do — a shape outlives a version, and ``v1/group`` owns only the arithmetic.

**A four contains six pairs and the searcher is in three of them.** That is the
whole reason there is a group objective at all rather than a sum of Fits, and it
is why every type here is about a *combination*: a shortlist's unit is a person,
and none of the shapes one directory up can hold *these three, seated this way*.

**``G`` is never a field.** :class:`GroupScore` computes it as a property from
the terms that produced it, so there is no constructor that takes an
already-summed objective and no row anybody could write one to. It is only ever
compared to another ``G`` — there is no group floor, nothing is seated because
its objective cleared a bar — and it never crosses the wire in any shape
(``docs/adr/0117``). What crosses instead is one closed
:class:`~app.engines.matchfit.core.GroupReason` naming the term with the largest
margin between the winner and the runner-up.

**A post-modifier Fit arrives as a number and not as a breakdown.** ADR-0117
admits a group term only if it reads something no seat's Fit read, and a
:class:`Seated` carrying the whole ``ModifiedFit`` would put every term Fit
already charged one attribute access away from a future group term. The
restriction is the rule, expressed where it can be checked rather than
remembered.

**The σ of a four is combined outside this engine**, exactly as a pair's is
(``scorable``). ``combine_sigma`` is RacketSkill's — *the single place any engine
is allowed to combine two standard deviations* — and ``.importlinter`` forbids
one engine to import the other, so a four's spread arrives through
:class:`SigmaCombiner`, handed in by the module that composes the two. Writing
``√(Σσ²)`` here would be a second definition of an identity that already has an
owner, which is the failure the engine-to-engine fence exists for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, final, runtime_checkable

from app.engines.matchfit.core import (
    ForecastAssumption,
    GroupReason,
    GroupTerm,
    Seat,
)
from app.engines.matchfit.ruleset import WEIGHT_TOTAL, IntentRules
from app.engines.matchfit.scorable import (
    GridCell,
    LevelReading,
    ScorableCandidate,
    Searcher,
)
from app.kernel import invariant


@runtime_checkable
class SigmaCombiner(Protocol):
    """How several Uncertainties become one. **Supplied, never written here.**

    Independent uncertainties add in quadrature, and that rule has exactly one
    home — ``racketskill/core.combine_sigma``. A pair's combination already
    arrives through the module that composes the two engines; a four's arrives
    the same way, and this Protocol is the shape of that arrival rather than a
    second opinion about it.

    It is a function and not a number because the enumeration is on this side:
    which four people are being read is decided here, so nothing outside could
    have precomputed their spread.
    """

    def __call__(self, sigmas: Sequence[float]) -> float: ...


@final
@dataclass(frozen=True, slots=True)
class PersonalFacts:
    """The two facts *how do these two get on* is made of, for one person.

    Fit reads a searcher against a candidate; the group objective reads two
    candidates against each other, and the three cross pairs contain no searcher
    at all. Neither side of a cross pair is *the* searcher, so the reading cannot
    take a :class:`~app.engines.matchfit.scorable.Searcher` and a
    :class:`~app.engines.matchfit.scorable.ScorableCandidate` — it takes two of
    these, and both halves of a Fit project onto it.

    **The searcher's declaration is their mode.** They are not asked what kind of
    evening they want twice: the tab they are on *is* the answer, and it is read
    off ``IntentRules.same_evening`` rather than by comparing two enums'
    spellings, because the two enums are deliberately different types.

    It carries nothing a term may not read. Every field is already on a fenced
    type, which is why this projection needs no fence of its own.
    """

    declared_intent: str | None
    tags: tuple[str, ...]

    @classmethod
    def of(cls, candidate: ScorableCandidate) -> "PersonalFacts":
        return cls(declared_intent=candidate.declared_intent, tags=candidate.tags)

    @classmethod
    def of_searcher(cls, searcher: Searcher, intent: IntentRules) -> "PersonalFacts":
        return cls(
            declared_intent=intent.same_evening[searcher.mode], tags=searcher.tags
        )


@final
@dataclass(frozen=True, slots=True)
class Forecast:
    """How even a game is forecast to be. **One type, everywhere it appears.**

    The best-of-three forecast answers *are these the right people*, the arranged
    forecast answers *is this the right way round*, and a provisional one answers
    the second with a seat still empty. Three readings, one shape — because they
    are the same claim about different sets of people, and three shapes would be
    three places for the caveat to fall off.

    **``provisional`` is derived from the assumption rather than stored beside
    it.** The failure being guarded against is a screen showing the number
    without its caveat, and a sibling boolean is exactly how the two get
    separated in a refactor (``docs/adr/0108``). Here they cannot be: there is no
    way to construct a provisional forecast with nothing to say about what was
    assumed, and no way to state an assumption without the figure being marked.

    ``sigma_group`` crosses because **the confidence is part of the claim** — the
    evidence is named rather than a category — and it is combined outside this
    engine, like every other σ.
    """

    pct: int
    sigma_group: float
    #: What was assumed, or ``None`` when nothing was. One value today: a
    #: half-empty side is read as if the missing player matched the one already
    #: there.
    assumption: ForecastAssumption | None

    def __post_init__(self) -> None:
        invariant(0 <= self.pct <= 100, f"a forecast of {self.pct}%")
        invariant(self.sigma_group >= 0.0, f"a negative group σ: {self.sigma_group}")

    @property
    def provisional(self) -> bool:
        """Whether a seat was still empty when this was read.

        A property and not a field, so the number and its caveat are one value.
        """

        return self.assumption is not None


@final
@dataclass(frozen=True, slots=True)
class Seated:
    """One of the three people beside the searcher, and what their seat is worth.

    ``fit`` is the **post-modifier** Fit — one number, the same one the floor
    tested and the card prints. It is a float and not a ``ModifiedFit`` on
    purpose: ADR-0117 admits a group term only if it reads something no seat's
    Fit read, and carrying the breakdown here would leave every term Fit already
    charged one attribute access from a term that must not re-charge it.

    ``locked`` is the searcher's own hand-seating. A locked seat is excluded from
    the mean and the min because a locked poor Fit pins the min across every
    combination, which would make ``w_minfit`` inert in ``FILL_SEATS`` — and a
    constant in an argmax is not a term.
    """

    candidate: ScorableCandidate
    fit: float
    locked: bool = False

    def __post_init__(self) -> None:
        invariant(
            0.0 <= self.fit <= WEIGHT_TOTAL,
            f"a seat's Fit outside the scale: {self.fit}",
        )

    @property
    def level(self) -> LevelReading:
        return self.candidate.level

    @property
    def player_id(self) -> str:
        return self.candidate.player_id

    @property
    def grid(self) -> tuple[GridCell, ...]:
        return self.candidate.grid

    @property
    def personal(self) -> PersonalFacts:
        return PersonalFacts.of(self.candidate)


@final
@dataclass(frozen=True, slots=True)
class CrossPair:
    """Two of the four with **no searcher between them**, and how they are seated.

    Three of a four's six pairs, invisible to every Fit by construction, because
    a Fit is always about the searcher and somebody. They are the reason a group
    objective exists at all rather than a sum of Fits.

    ``seat`` is not derivable from the pair — the same two candidates partner
    each other in one arrangement and face each other in the other two — which is
    why the seat travels with them rather than being worked out again by whoever
    reads them.
    """

    mine: "Seated"
    theirs: "Seated"
    seat: Seat


@final
@dataclass(frozen=True, slots=True)
class Arrangement:
    """Which side each of the four plays on. **Exactly three, and never more.**

    An arrangement of a four is fully described by *who partners the searcher* —
    the other two are the opposition by subtraction — so the three pairings of
    four people are the three choices of partner, and there is no representation
    here in which a fourth could be written down. ``arrange()`` is not a separate
    step that walks them: the combination is chosen by ``argmax G`` over all
    three, because the seat delta and the cross pairs' seat scopes vary with the
    arrangement (``docs/adr/0117``).

    **A line-up is who; an arrangement is which way round.** The two are separate
    words because the best-of-three forecast answers *are these the right people*
    and the arranged forecast answers *is this the right way round*, and
    conflating them is how a screen stops changing when somebody is moved across
    the net.

    **A seat may be empty, and the empty seat is one of the three positions.**
    *Three of four* is an honest answer rather than a different shape, so a
    line-up with an open seat is arranged the way a full one is: with two seated
    there are still three arrangements, because the open seat can be the
    searcher's partner or either opponent. The one thing that cannot be arranged
    is a side with nobody on it — the searcher is always on their own side, so
    what that rules out is an arrangement facing no opponent at all.
    """

    #: ``None`` when the searcher's partner seat is the open one.
    partner: Seated | None
    #: One or two. **Never none** — a side with nobody on it is not a side, and
    #: nothing downstream of here has an honest reading for one.
    opponents: tuple[Seated, ...]

    def __post_init__(self) -> None:
        invariant(
            1 <= len(self.opponents) <= 2,
            f"an arrangement facing {len(self.opponents)} opponents: a side "
            f"with nobody on it is not a side, and three is not a side either",
        )

    @property
    def complete(self) -> bool:
        """Whether all four seats are taken. **The objective needs this.**"""

        return self.partner is not None and len(self.opponents) == 2

    @property
    def seated(self) -> tuple[Seated, ...]:
        """The non-viewer seats that are **taken**, partner first."""

        return (
            self.opponents if self.partner is None else (self.partner, *self.opponents)
        )

    @property
    def partner_id(self) -> str:
        """The partner's id, or the empty string for an open partner seat.

        A total order needs a value for every arrangement, including the one
        whose partner seat is open, and a tie between two arrangements breaks on
        a fact rather than on a set (``docs/adr/0105``). The empty string sorts
        first, which is one answer to *who is beside me* everywhere it is read.
        """

        return "" if self.partner is None else self.partner.player_id

    @property
    def cross_pairs(self) -> tuple[CrossPair, ...]:
        """The pairs containing no searcher, each at the seat it occupies.

        Invisible to every Fit by construction, because a Fit is always about the
        searcher and somebody. The two opponents partner **each other**, which is
        why the same three people read differently in each arrangement even
        though the set of cross pairs does not change.

        **An open seat is in no pair.** Three of them exist only in a complete
        four; a line-up with a seat still open has one or none, and a cross
        reading against nobody would be the invented number this engine refuses
        everywhere else.
        """

        pairs: list[CrossPair] = []
        if len(self.opponents) == 2:
            pairs.append(
                CrossPair(self.opponents[0], self.opponents[1], Seat.PARTNER)
            )
        if self.partner is not None:
            pairs.extend(
                CrossPair(self.partner, opponent, Seat.OPPONENT)
                for opponent in self.opponents
            )
        return tuple(pairs)

    @classmethod
    def all_of(cls, seated: Sequence[Seated]) -> tuple["Arrangement", ...]:
        """Every way round these people can sit, in a deterministic order.

        Three for a complete four, in the order the three were handed over —
        deterministic rather than incidental, because a tie breaks on which of
        them is the partner and never on a set (``docs/adr/0105``).

        **Three again for a four with one seat open**, because the open seat is
        itself one of the three positions: beside the searcher, or across the
        net. One for a line-up with a single guest, who can only be an opponent —
        seating them beside the searcher would leave the far side empty. And none
        at all for nobody, which is the *nobody tonight* line-up rather than an
        error.
        """

        if not seated:
            return ()
        if len(seated) == 1:
            return (cls(partner=None, opponents=(seated[0],)),)
        if len(seated) == 2:
            first, second = seated
            return (
                cls(partner=first, opponents=(second,)),
                cls(partner=second, opponents=(first,)),
                cls(partner=None, opponents=(first, second)),
            )
        invariant(
            len(seated) == 3,
            f"a doubles line-up seating {len(seated)} people beside the searcher",
        )
        first, second, third = seated
        return (
            cls(partner=first, opponents=(second, third)),
            cls(partner=second, opponents=(first, third)),
            cls(partner=third, opponents=(first, second)),
        )


@final
@dataclass(frozen=True, slots=True)
class Arranged:
    """One arrangement, its forecast, and how far apart the two sides are.

    **What the builder is offered, and the whole of it.** Every swap the builder
    permits is one of these, so *Even it out* is a selection and never a
    computation, and there is no arithmetic left for a client to be tempted by
    (``docs/adr/0108``).

    It carries no ``G`` and never will. A :class:`GroupScore` is the objective's
    own working, compared to another objective and recorded; this is what a
    screen draws. They are separate types precisely so that the number the four
    was chosen by has nowhere to leak through.
    """

    arrangement: Arrangement
    forecast: Forecast
    #: How far apart the two sides' strengths are. **The min-gap arrangement is
    #: what *Even it out* selects**, and it is a different question from
    #: ``argmax G`` — the new fact the builder can state is that the two differ.
    side_gap: float


@final
@dataclass(frozen=True, slots=True)
class GroupTermReading:
    """One group term that produced a reading, and what it was worth here.

    ``weight`` is the **renormalised** weight — the term's share of a hundred
    over the terms that actually fired — exactly as a ``ScoredTerm``'s is. A
    group term stands down for the same kind of reason a term of Fit does: four
    people none of whom declared an intent and hold no tag in either column give
    no cross reading, and *we looked and found nothing* is not a fact about
    those three pairs.
    """

    term: GroupTerm
    weight: float
    value: float
    contribution: float

    def __post_init__(self) -> None:
        invariant(
            0.0 <= self.value <= 1.0,
            f"{self.term.value} read {self.value}, which is outside [0, 1]",
        )


@final
@dataclass(frozen=True, slots=True)
class GroupScore:
    """One arrangement of one four, and what the objective made of it.

    **There is no ``objective`` field.** ``G`` is a property of the terms that
    produced it, so nothing can construct a score carrying an objective its own
    terms do not add up to, and there is no attribute a serialiser could reach
    for. It is compared to another ``G`` and to nothing else.
    """

    arrangement: Arrangement
    #: Every group term that fired, in ``GroupTerm``'s own declaration order.
    terms: tuple[GroupTermReading, ...]
    #: The terms that stood down — the renormalisation basis, without which two
    #: objectives are not comparable a year later.
    degraded_terms: tuple[GroupTerm, ...]
    #: The arranged forecast for these four, this way round.
    forecast: Forecast
    #: How far apart the two sides' strengths are. **The min-gap arrangement is
    #: what *Even it out* selects**, and it is a different question from
    #: ``argmax G`` — the new fact the builder can state is that the two differ.
    side_gap: float

    @property
    def objective(self) -> float:
        """``G``. **Recorded, never returned, and never a number on a screen.**"""

        return sum(term.contribution for term in self.terms)

    @property
    def arranged(self) -> Arranged:
        """The half of this a screen may see: the way round, and the forecast.

        A projection rather than a field, so a score and the arrangement it
        publishes cannot be constructed apart and cannot disagree — and so the
        objective has no path onto the wire even by accident.
        """

        return Arranged(
            arrangement=self.arrangement,
            forecast=self.forecast,
            side_gap=self.side_gap,
        )

    def contribution_of(self, term: GroupTerm) -> float:
        """What one term was worth here, or nothing at all if it stood down.

        Zero for a term that did not fire, because the margin this feeds is
        *what the winner gained over the runner-up on this term* and a term
        neither of them could read gained nobody anything.
        """

        for reading in self.terms:
            if reading.term is term:
                return reading.contribution
        return 0.0


@runtime_checkable
class PairAdmissibility(Protocol):
    """Whether two candidates may share a court. **Precomputed, never asked here.**

    ``docs/adr/0116``: a four contains six pairs and every absolute gate binds
    all six, so eligibility for a *seat* is a property of a **combination** and
    cannot be spent at candidate generation. The three gates that bind — a block
    either way, the mutual gender preference, and the level tolerance the
    newcomer window tightens — all read facts this engine may not see, so the
    mask is built in the module where the I/O is and arrives here as one
    ``K × K`` question the enumeration asks three times per combination.

    It is a **callable and not a set** for the reason ``SigmaCombiner`` is one:
    what crosses the fence is the answer, never the evidence. A set of pairs
    would be a set of ids the enumeration could iterate, and an order taken off a
    set is the determinism failure ``docs/adr/0105`` is about.
    """

    def __call__(self, one: str, other: str) -> bool: ...


@final
@dataclass(frozen=True, slots=True)
class LineupCounts:
    """What the enumeration walked, and what it threw away.

    Layer 4's counters. ``refused_by_gate`` is
    ``docs/adr/0116``'s own falsifier — *if it is indistinguishable from zero the
    gate is decorative; if it dominates the enumeration the pool is too thin for
    doubles* — and neither reading is available from anything a route returns.
    """

    combinations: int
    refused_by_gate: int
    refused_by_floor: int

    def __post_init__(self) -> None:
        for name, count in (
            ("combinations", self.combinations),
            ("refused_by_gate", self.refused_by_gate),
            ("refused_by_floor", self.refused_by_floor),
        ):
            invariant(count >= 0, f"{name} counted {count}")


@final
@dataclass(frozen=True, slots=True)
class Seating:
    """Who the engine seated, every way round they may sit, and what decided it.

    **The winner and the runner-up are here and the objective is not.** ``G``
    rides on the two :class:`GroupScore`s, which the record keeps and no route
    returns; what a screen may draw is ``arrangements``, ``best``, ``evenest``
    and one closed :class:`~app.engines.matchfit.core.GroupReason`.

    ``best`` and ``evenest`` are separate fields rather than one, because **the
    new fact the builder can state is that they differ** — which happens
    precisely when a four's levels are near-equal and balance has nothing left to
    say. They are ``None`` only when nobody could be seated at all, which is the
    *nobody tonight* line-up and not an error.
    """

    #: Who took a seat, in the order they were seated. Nought to three.
    seated: tuple[Seated, ...]
    #: Every way round these people can sit, each with its own forecast.
    arrangements: tuple[Arranged, ...]
    #: The best by ``G`` — or, while a seat is open and there is no objective to
    #: read, the evenest, because balance is then the only thing left saying
    #: anything about which way round.
    best: Arranged | None
    #: The min-gap arrangement. **What *Even it out* selects.**
    evenest: Arranged | None
    #: Why this four beat the runner-up. ``None`` when there was no runner-up to
    #: beat — one admissible combination, or none.
    reason: GroupReason | None
    #: Layer 4's first row: the winning combination and its whole ``G``
    #: breakdown. ``None`` while the line-up is incomplete, because an
    #: incomplete four has no objective.
    winner: GroupScore | None
    #: Layer 4's second row — **exactly what the deciding margin is computed
    #: from**, and nothing else about the 1 770 that lost.
    runner_up: GroupScore | None
    counts: LineupCounts


__all__ = [
    "Arranged",
    "Arrangement",
    "CrossPair",
    "Forecast",
    "GroupScore",
    "GroupTermReading",
    "LineupCounts",
    "PairAdmissibility",
    "PersonalFacts",
    "Seated",
    "Seating",
    "SigmaCombiner",
]
