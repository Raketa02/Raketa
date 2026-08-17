"""The ``MatchFitEngine`` Protocol and the vocabulary it speaks.

A consuming context depends on this abstraction, never on a version, so swapping
``matchfit/v1`` for a later lineage — or for an implementation behind HTTP — is a
wiring change at the FastAPI boundary like any other port (``docs/adr/0015``).

**One score, and one number beside it saying how much of it was measured.** Match
Fit answers *how good is this match for me* as a single comparable figure so that
ten cards become rankable, and it reports **Coverage** as its own number rather
than blending it in. A thin score and a strong score are different facts: a fit of
84 at 60% coverage is a more honest and less immediately legible thing than a fit
of 84, and that trade was made deliberately (``docs/adr/0027``).

**Every signal is a term.** There is no bonus, no penalty and no modifier applied
outside the weighting. The source design added ``+8`` / ``+5`` / ``−8`` after the
weighted sum, which pushed the score outside 0–100 and then clamped it — and a
bonus added outside the weighting has no defined meaning at all once the weights
are renormalised, which is now the mechanism. Ladder qualification and familiarity
are *terms* here for exactly that reason.

**A term is a constraint or a piece of evidence, and the kind decides what its
absence means.** This is the whole repair ADR-0027 records, and it is structural
rather than conventional:

* A **constraint** term encodes a limit the player declared — the days and hours
  they can play, price, travel, match type, a ladder they entered. An undeclared
  limit is genuinely *no limit*: the term scores full marks, keeps its weight, and
  Coverage is untouched.
* An **evidence** term encodes something the platform observed — skill overlap,
  predicted balance, reliability, familiarity. Absent evidence is **not** a good
  score. The term is *excluded*, the surviving weights are renormalised over what
  actually ran, and Coverage falls.

``ExcludedTerm`` therefore has no ``value`` field to fill in and no ``kind`` field
to set wrongly: only evidence is ever excluded, so its kind is derived. *A missing
declaration is not a missing measurement*, and the two cannot be spelled the same
way here even by accident.

**A reason is a term, not a second object.** ``reasons`` holds the same
``ScoredTerm`` instances that are in ``terms``, ranked by **contribution** — weight
times value — rather than by how well each scored. A card showing *"38 zł, under
your 45 zł ceiling"* beside a score computed from a different price would be two
readings of a match that only has one, so there is only one object to read.

**Numbers and machine codes, never words.** Every term carries a ``TermCode`` and
a payload of quantities in the units the kernel keeps them in — grosze, minutes,
exact ratios. The engine emits no display text, no formatted Level, no formatted
price and no formatted time; how they are drawn, in which language and with which
currency symbol, is the client's, and the two clients do not share a shape
(``docs/adr/0022``).

**The ranking is not here.** Which matches a player is *shown* — the exploration, the
diversity caps, the impressions an unfilled match is owed, where the tail is cut —
composes this score with its coverage and lives in the calling module's application
layer, because it reads configuration, runs experiments and draws randomness, and an
engine may do none of those (``docs/adr/0027``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol, TypeAlias, final, runtime_checkable

from app.engines.forecast import Certainty, PairingAnalysis
from app.engines.matchmaking import (
    CourtHold,
    HourWindow,
    LadderQualification,
    Level,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    Weekday,
)
from app.kernel import (
    Grosze,
    Instant,
    MinuteOfDay,
    Minutes,
    Payable,
    Ratio,
    invariant,
)


class TermKind(Enum):
    """What a term's **absence** means, which is the only thing this decides.

    Not a category for a reader's benefit: it is the property that makes *"we do
    not know"* and *"it is good"* different kinds of number, which is the collapse
    the source design's optimistic defaults were.
    """

    CONSTRAINT = "constraint"
    EVIDENCE = "evidence"


class TermCode(Enum):
    """The stable machine key of every term the engine can emit.

    A client renders copy per code and the codes never change, which is what lets
    the wording of a reason change without a backend release. The enum lists the
    terms that **exist**, and as of the two below it lists all ten of them:
    ``matchfit/v1/constants.py``'s ``PENDING_WEIGHTS`` is empty, so there is no
    longer a code a client could handle and never receive.
    """

    SKILL_OVERLAP = "skill_overlap"
    PREDICTED_BALANCE = "predicted_balance"
    TIME_FIT = "time_fit"
    MATCH_VIABILITY = "match_viability"
    GROUP_RELIABILITY = "group_reliability"
    TRAVEL = "travel"
    LADDER_QUALIFICATION = "ladder_qualification"
    PRICE = "price"
    MATCH_TYPE = "match_type"
    FAMILIARITY = "familiarity"


@final
@dataclass(frozen=True)
class SkillOverlapFact:
    """The player's own Level, and the Level this match says it is aimed at.

    Both exact ratios on the rating scale and neither of them rendered: *"3,00"*
    is a formatting decision and the two clients do not share one.

    ``band_half_width`` is **which of the two answers the target came from**,
    carried as the quantity rather than as a label. Absent means the target is the
    *Seat target* — the exact Level that would even this match, which the pairing
    engine gives only when one seat is open — and present means it is the midpoint
    of a *Target band* that wide either side. So a client writes *"this seat is
    aimed at 3,10"* or *"this match is aimed at 2,60–3,60"* from the same payload,
    and the same rule ``PriceFact.ceiling`` follows: an absent field is a fact
    about what was available, not a zero.

    ``distance`` is a property rather than a field, for the reason every derived
    number here is one: a carried copy is a number a later edit can leave
    disagreeing with the two it came from, and it is what the term's value was
    actually computed from.
    """

    level: Level
    target: Level
    band_half_width: Ratio | None
    kind: Literal["skill_overlap"] = "skill_overlap"

    @property
    def distance(self) -> Ratio:
        """How far the player is from the target, in Level points. **Unsigned.**

        The term is symmetric — being a Level too strong for a match and a Level
        too weak are both *not the match you belong in* — so the direction is not
        what the score reads. It is still recoverable from the two Levels beside
        it, which is what lets a client say *"above"* or *"below"* without the
        score having to encode which.
        """

        return Ratio(abs(self.target - self.level))


@final
@dataclass(frozen=True)
class BalanceFact:
    """The forecast this term read: the estimate, and how sure of it the platform is.

    ``estimate`` is a whole percent where 100 is dead even, and ``margin`` is how
    wrong it could be in the same units — the pair a card needs in order to say
    *"84% balanced"* or to say nothing at all.

    ``certainty`` is carried so that **suppression stays a presentation decision**.
    The term scores on the estimate whatever the grade is, so a client that
    declines to print a LOW forecast is hiding a number the ranking still used, and
    it can only know to do that if the grade travels with it. Reading
    ``BalanceForecast.fit_to_print`` is the same question asked of the same enum.

    ``imputed_seats`` is how many of the roster's Levels were stood in for, and it
    is the difference between *"we are unsure about these four people"* and *"three
    of these four are nobody yet"* — two matches that can carry the same margin and
    are not the same claim.
    """

    estimate: int
    margin: int
    certainty: Certainty
    imputed_seats: int
    kind: Literal["predicted_balance"] = "predicted_balance"


@final
@dataclass(frozen=True)
class PriceFact:
    """What the price term actually read: the payable, and the declared ceiling.

    Both in **grosze**, the kernel's unit, and neither formatted. ``ceiling`` is
    absent when the player declared none, which is what a client needs in order to
    say *"38 zł"* rather than *"38 zł, under your ceiling"* — the second sentence
    is a claim about a declaration that does not exist.
    """

    payable: Payable
    ceiling: Grosze | None
    kind: Literal["price"] = "price"


@final
@dataclass(frozen=True)
class TimeFact:
    """When the match starts on the club's clock face, and when the player said.

    Both halves in the vocabulary the declaration is made in — a ``Weekday`` and a
    ``MinuteOfDay``, never a rendered *"Tuesday 18:30"* — so the client owns the
    words and the locale, and the two are the *club's* local day and minute rather
    than anything read off a UTC instant.

    ``days`` and ``hours`` are the declaration itself, absent when the player made
    none. That is what lets a client say *"Tuesday 18:30"* rather than *"Tuesday
    18:30, outside the hours you gave"* to somebody who gave none — the second
    sentence is a claim about a declaration that does not exist.

    The two predicates below are **properties and not fields**, so the rule that
    decides the term's value is also the rule a client reads. A carried pair of
    bools would be the same conclusion stored twice, free to disagree with the
    quantities beside it after a refactor; deriving them means the payload cannot
    say *inside* while the term scored *outside*.
    """

    weekday: Weekday
    minute: MinuteOfDay
    days: frozenset[Weekday] | None
    hours: tuple[HourWindow, ...] | None
    kind: Literal["time_fit"] = "time_fit"

    @property
    def on_a_declared_day(self) -> bool:
        """True when the player declared no days at all, which is *any day*."""

        return self.days is None or self.weekday in self.days

    @property
    def inside_a_declared_window(self) -> bool:
        """True when the player declared no hours at all, which is *any hour*.

        Otherwise the start has to fall inside one of them. **The start decides**
        — a match that begins inside a declared window is inside it however long
        it runs — which is a rule with a constant's falsifying note behind it in
        ``matchfit/v1/constants.py`` and is the reason no duration is carried here.
        """

        return self.hours is None or any(
            window.contains(self.minute) for window in self.hours
        )


@final
@dataclass(frozen=True)
class ViabilityFact:
    """The four facts behind *will this match actually be played*.

    Every one of them a quantity in the unit its own vocabulary keeps it in — two
    seat counts, a rung of the hold ladder, elapsed minutes, a share — so a client
    can write *"3 of 4 paid, court booked"* or *"nobody has joined and the club is
    full"* from the same numbers the term was scored from.

    ``paid_seats`` and ``sold_seats`` rather than the fraction between them,
    because *three of four* and *seventy-five per cent* are the same number and not
    the same sentence, and the one a card shows is the first.

    ``minutes_to_cutoff`` is **signed**, as every ``Minutes`` is. It is negative for
    a match whose cutoff has already passed, which candidate generation is supposed
    to have filtered out before an engine ever sees it — reporting the number the
    engine actually read is what lets a caller notice that it did not.
    """

    paid_seats: int
    sold_seats: int
    hold: CourtHold
    minutes_to_cutoff: Minutes
    crowding: Ratio
    kind: Literal["match_viability"] = "match_viability"


@final
@dataclass(frozen=True)
class TravelFact:
    """How far away it is and how far they said they would go, both in minutes."""

    minutes: Minutes
    radius: Minutes | None
    kind: Literal["travel"] = "travel"


@final
@dataclass(frozen=True)
class MatchTypeFact:
    """Whether the match is counted, and what the player asked for.

    ``preference`` is the enum and not a rendered word, for the same reason
    ``counted`` is a bool: *"a friendly, and you asked for counted matches"* is a
    sentence the client owns, assembled from two machine values.
    """

    counted: bool
    preference: MatchTypePreference | None
    kind: Literal["match_type"] = "match_type"


@final
@dataclass(frozen=True)
class LadderFact:
    """Which of the three ladder states this match is in for this player."""

    qualification: LadderQualification
    kind: Literal["ladder_qualification"] = "ladder_qualification"


@final
@dataclass(frozen=True)
class ReliabilityFact:
    """The reliability the term scored on, and how many records it was read from.

    ``observed`` is how many of the *other* seated players carried a record and
    ``seated`` how many there were, so a client can tell *"this group turns up"*
    from *"one of these four has a record and the rest are strangers"*. Those are
    different claims and the term's value alone cannot separate them.
    """

    least_reliable: Ratio
    observed: int
    seated: int
    kind: Literal["group_reliability"] = "group_reliability"


@final
@dataclass(frozen=True)
class FamiliarityFact:
    """How many of the others are new to the current player, out of how many."""

    new_faces: int
    others: int
    kind: Literal["familiarity"] = "familiarity"


#: Everything a scored term can say about itself in quantities. One member per
#: term that can score, each with the machine key its ``TermCode`` carries and a
#: payload of numbers — never a sentence, never a formatted figure.
TermFact: TypeAlias = (
    SkillOverlapFact
    | BalanceFact
    | TimeFact
    | ViabilityFact
    | PriceFact
    | TravelFact
    | MatchTypeFact
    | LadderFact
    | ReliabilityFact
    | FamiliarityFact
)


@final
@dataclass(frozen=True)
class ScoredTerm:
    """One term that ran: its weight, its value in 0..1, and what it read.

    ``value`` is exact — a ``Ratio`` over two integers — so the weighted average
    below it is exact and the score crosses into a whole percent exactly once, at
    the end. A term is never handed a float to lose precision in on the way.

    ``contribution`` is weight times value and is the quantity **reasons are ranked
    by**, because a term scoring 1,0 out of a weight of 3 says less about why this
    match is good than one scoring 0,8 out of 24. It is a property rather than a
    field for the reason every derived number here is: a carried copy is a number a
    retune can leave disagreeing with the two it came from.

    ``fact.kind`` and ``code`` are checked against each other rather than trusted.
    They are the same machine key spelled twice — once for ranking, once on the
    payload a client reads — and a term carrying a travel payload under the price
    code would render a distance as a price with no test able to notice.
    """

    code: TermCode
    kind: TermKind
    weight: int
    value: Ratio
    fact: TermFact

    def __post_init__(self) -> None:
        invariant(self.weight > 0, f"a term with weight {self.weight}")
        invariant(0 <= self.value <= 1, f"a term value outside 0..1: {self.value}")
        invariant(
            self.fact.kind == self.code.value,
            f"a {self.code.value} term carrying a {self.fact.kind} payload",
        )

    @property
    def contribution(self) -> Ratio:
        """Weight times value: how much of the score this term actually produced."""

        return Ratio(self.weight * self.value)


@final
@dataclass(frozen=True)
class ExcludedTerm:
    """One term that did not run, because the platform observed nothing to run it on.

    It keeps its ``weight`` — that is what Coverage is measured against — and has
    **no value**, which is the point: there is no field here for a friendly default
    to be written into, so *"we do not know"* cannot be spelled as a score. The
    surviving weights are renormalised over what ran, and this term's weight is
    the difference between the two denominators.

    ``kind`` is derived and always evidence. **Only evidence is ever excluded**, so
    a carried kind would be a field with one legal value and one silent bug.
    """

    code: TermCode
    weight: int

    def __post_init__(self) -> None:
        invariant(self.weight > 0, f"a term with weight {self.weight}")

    @property
    def kind(self) -> TermKind:
        return TermKind.EVIDENCE


#: One term, in either of the two states a term can be in. Both members are
#: ``@final``, so the union is closed: a third state would have to be added here,
#: where every reader can see it arrive, rather than by subclassing one of these.
Term: TypeAlias = ScoredTerm | ExcludedTerm


@final
@dataclass(frozen=True)
class MatchFitScore:
    """How good one match is for one player — and how much of that was measured.

    ``fit`` is the weighted average of the terms that ran, as a whole percent.
    ``coverage`` is the share of the table's weight those terms hold, also a whole
    percent. **The second is never blended into the first**, and reading either one
    alone is a mistake the type cannot prevent: a fit of 100 at 63% coverage is a
    match nothing is known to be wrong with, not a perfect match.

    Both are carried rather than derived, for the same reason the split bar is
    carried on a ``BalanceForecast``: the derivation goes through the engine's
    rounding, and a property recomputing it here would be a second implementation
    of the rounding rule. What keeps them honest is an invariant asserted over
    every roster in the suite — *the score is the weighted average of its own
    terms* — rather than a comment saying so.

    ``terms`` holds every term in the table, scored and excluded alike, in table
    order. It is the whole audit trail: the score, the coverage, the reasons and
    the warning are all statements about this tuple.

    ``reasons`` are the strongest **contributors**, best first, and are the very
    same objects that are in ``terms`` — asserted with ``is``, so a card cannot
    show a reason computed from anything but the score beside it. ``warning`` is
    the *lowest* contributor, and only when its **raw value** is below threshold:
    the asymmetry is deliberate, because a term can be last by contribution while
    being perfectly fine in itself.

    ``engine_version`` and ``pairing_version`` both travel because a Match Fit
    score has **two producers**, and a constant belonging to either can only be
    falsified against results it can be attributed to. The pairing version is read
    off the analysis the score was computed from, never carried separately, so the
    two cannot disagree about which forecast this was.
    """

    fit: int
    coverage: int
    terms: tuple[Term, ...]
    reasons: tuple[ScoredTerm, ...]
    warning: ScoredTerm | None
    engine_version: str
    pairing_version: str

    def __post_init__(self) -> None:
        codes = tuple(term.code for term in self.terms)
        invariant(len(codes) > 0, "a score with no terms at all")
        invariant(len(set(codes)) == len(codes), f"a term scored twice: {codes}")
        # A score has to have been produced by *something*. It cannot fail while
        # the table holds a constraint term, since a constraint always scores — but
        # this value object is public vocabulary and a caller can build one, and a
        # weighted average over no weight is a division by zero rather than a low
        # score.
        invariant(len(self.scored) > 0, "a score with no term that ran")
        invariant(0 <= self.fit <= 100, f"a fit outside 0..100: {self.fit}")
        invariant(
            0 <= self.coverage <= 100, f"a coverage outside 0..100: {self.coverage}"
        )

    @property
    def scored(self) -> tuple[ScoredTerm, ...]:
        """The terms that ran. What the score is an average of."""

        return tuple(term for term in self.terms if isinstance(term, ScoredTerm))

    @property
    def excluded(self) -> tuple[ExcludedTerm, ...]:
        """The terms that did not. What Coverage is missing."""

        return tuple(term for term in self.terms if isinstance(term, ExcludedTerm))


@runtime_checkable
class MatchFitEngine(Protocol):
    """A pure, versioned Match Fit engine.

    ``score`` is a function of the match, the player's declaration, the pairing
    analysis and the instant it is asked at, and nothing else: no clock, no
    randomness, no state between calls.

    **The analysis is an input, never a collaborator** (``docs/adr/0026``). The
    caller runs Pairing and hands the result over, so the score and the card beside
    it are computed from one pairing by construction. An engine free to build its
    own forecast is an engine that can score a match against a pairing nobody was
    shown, which is two implementations of one question smuggled into one layer.
    """

    @property
    def version(self) -> str: ...

    def score(
        self,
        *,
        snapshot: MatchSnapshot,
        profile: PlayerProfile,
        analysis: PairingAnalysis,
        now: Instant,
    ) -> MatchFitScore: ...
