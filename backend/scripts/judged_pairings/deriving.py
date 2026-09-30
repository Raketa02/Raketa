"""The six judged pairings, re-derived against the live ruleset.

This half **reads and scores**; ``tables`` writes the answer into the documents.
The split is the one the two halves change for: a rendering edit is a document
decision and a derivation edit is a ruleset decision, and a module edited for
both reasons is edited twice as often by people who understand half of it.

``docs/specs/matchmaking/judged-pairings.json`` holds one searcher and seven
candidate rows as **inputs** plus the verdict a human passed on each
(``docs/adr/0122``). Everything else about a judged pairing is *derived* — every
term value, every renormalised weight, every Fit — and this is where.

**Three things the fixture records are read by nobody, and that is the fence
working rather than an omission.** Gender and preference, the block and hold
state, and the profile commit date are all facts about the *population* these
six were judged in; none of them can enter a Fit, because ``ScorableCandidate``
has no field for any of them and ``tests/unit/test_scorable_candidate_fence.py``
walks the source transitively and fails the build on one appearing. Gating and
candidate generation read them on the other side of the fence, where the I/O is.
The fixture states them so a reader knows the gates were pinned neutral; the
scorer could not consult them if it wanted to.

**The clock is not one of those.** It is read, because it is an input to a term's
evidence — the soonest cell the two of them share — and the fixture's own reason
for pinning a Wednesday is that on a Saturday ``TODAY`` and ``WEEKEND`` collapse.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence, final

from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scorable import (
    CombinedUncertainty,
    GridCell,
    LevelReading,
    ScorableCandidate,
    Searcher,
)
from app.engines.matchfit.scoring import Fit
from app.engines.matchfit.v1 import renormalised_weights, score
from app.engines.racketskill.core import combine_sigma, confidence_percent
from app.kernel import IsoWeekday, iso_weekday
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET

#: The repository root, from this file's own place in it. Derived rather than
#: passed in: a generator that can be pointed at a different tree is one that can
#: quietly regenerate nothing.
REPO = Path(__file__).resolve().parents[3]

SPECS = REPO / "docs" / "specs" / "matchmaking"
FIXTURE = SPECS / "judged-pairings.json"
JUDGED_DOC = SPECS / "the-judged-pairings.md"
WEIGHTS_DOC = SPECS / "ranking-weights.md"

#: The fixture's own column names against the terms they read. The fixture is
#: product's document and its spellings are its own; this is the one place the
#: two vocabularies are mapped, so a renamed column is one edit and a loud one.
COLUMNS: Mapping[str, Term] = OrderedDict(
    (
        ("level", Term.LEVEL_FIT),
        ("balance", Term.PREDICTED_BALANCE),
        ("intent", Term.INTENT_ALIGNMENT),
        ("avail", Term.AVAILABILITY_OVERLAP),
        ("style", Term.PLAYING_STYLE),
        ("distance", Term.DISTANCE),
        ("vibe", Term.SOCIAL_VIBE),
    )
)

MODES: Mapping[str, SearchMode] = OrderedDict(
    (("comp", SearchMode.COMPETITIVE), ("fun", SearchMode.FOR_FUN))
)

#: The two tag columns, together — §6's counterfactual stands both of them down
#: at once, because standing one down is not the alternative anybody proposed.
TAG_TERMS = (Term.PLAYING_STYLE, Term.SOCIAL_VIBE)


@final
@dataclass(frozen=True, slots=True)
class Verdict:
    """One judged outcome, and how it is spelled wherever it is printed.

    Three facts about one verdict, held together because they move together: a
    fourth spelling or a fourth verdict is one row here rather than an edit in
    four places. ``shown`` is the one the floor is read across — a docked
    candidate reached a screen, and the dock happened somewhere that is not Fit.
    """

    #: As a document prints it, emphasis and all.
    printed: str
    #: As a terminal prints it. A console rendering ``**Not shown**`` is a table
    #: that leaked.
    plain: str
    shown: bool


VERDICTS: Mapping[str, Verdict] = {
    "shown": Verdict(printed="Shown", plain="shown", shown=True),
    "shown_docked": Verdict(printed="Shown, docked", plain="shown, docked", shown=True),
    "not_shown": Verdict(printed="**Not shown**", plain="NOT SHOWN", shown=False),
}

#: The days, in ISO order, to check the fixture's clock against its own
#: parenthesised name. Spelled out rather than taken from ``strftime("%A")``,
#: which answers in the runner's locale and would fail this fixture on a machine
#: configured in Polish.
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

#: The searcher's week, as four concrete hours — ``(weekday, the hour the cell
#: starts at)``. The fixture says only *four of 112*, and that is not an
#: omission: availability reads ``|shared| / |mine|`` and **no constant at
#: all**, so which four they are moves no value in any case — which is also why
#: the week becoming hours (``docs/adr/0189`` §5) moved nothing in the tables.
#: The identity is needed anyway, because the term's evidence names the next
#: hour the two of them share.
WEEK: tuple[tuple[int, int], ...] = (
    (1, 19),
    (3, 19),
    (5, 19),
    (6, 10),
)

#: A cell the searcher did **not** tick. It is what makes *they share none of
#: your times* a measurement rather than a blank week: a candidate with no grid
#: at all reads *we do not know when they play*, which stands the term down and
#: renormalises its weight onto the other six. Case 2's whole assertion is about
#: what zero overlap costs, so the two readings must not be spelled the same way.
UNSHARED = (7, 15)


class Unreadable(Exception):
    """The harness cannot run — a missing fixture, a document without markers.

    Separate from a failed re-derivation on purpose, and carried out to a
    different exit code. *The floor moved* is a finding; *I could not look* is
    not, and a check that reports the second as the first is one that reports
    green the day somebody moves a file.
    """


@dataclass(frozen=True)
class Reading:
    """One judged case scored in one mode, with what the tables print of it."""

    case_id: str
    #: The case's name as §10's first column prints it — product's prose, in
    #: product's document, emphasis included. Unlike a **verdict**, which is a
    #: machine code spelled per medium, this *is* the document text and has
    #: nowhere else to be written.
    label: str
    verdict: Verdict
    note: str | None
    mode_key: str
    mode: SearchMode
    fit: Fit
    delta_mu: float
    sigma_pair: float
    balance_pct: float
    values: Mapping[str, float]
    #: §6's counterfactual: the same pairing with both tag columns stood down
    #: and renormalised over the five terms that remain.
    blank_points: float

    @property
    def is_shown(self) -> bool:
        return self.verdict.shown

    @property
    def verdict_text(self) -> str:
        return self._spelled(self.verdict.printed)

    @property
    def verdict_plain(self) -> str:
        return self._spelled(self.verdict.plain)

    def _spelled(self, verdict: str) -> str:
        return f"{verdict}, {self.note}" if self.note else verdict

    def weight_of(self, column: str) -> float:
        """One term's renormalised weight in this reading, by fixture column."""

        term = COLUMNS[column]
        return next(scored.weight for scored in self.fit.terms if scored.term is term)


# ---------------------------------------------------------------------------
# Reading the fixture, and scoring it
# ---------------------------------------------------------------------------


def read_fixture(path: Path = FIXTURE) -> dict[str, Any]:
    """The judged pairings, from the spec and never copied into code.

    A copied fixture is a fixture that drifts, and the failure it drifts into is
    *the tests still pass and the document is now wrong*.
    """

    if not path.is_file():
        raise Unreadable(f"the judged pairings are gone from {path}")
    loaded: dict[str, Any] = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict
    )
    return loaded


def cells(*specs: tuple[int, int]) -> tuple[GridCell, ...]:
    return tuple(GridCell(day=iso_weekday(day), hour=hour) for day, hour in specs)


def weekday(clock: str) -> IsoWeekday:
    """The weekday the fixture pinned, read off its own ``clock`` string.

    Read rather than assumed, because it is an input: the fixture's stated reason
    for a Wednesday is that on a Saturday *today* and *the weekend* collapse into
    one cell, so a clock somebody moves must move the readings and not be
    silently ignored. The parenthesised name is checked against the date, so a
    fixture that contradicts itself fails here rather than in a table.
    """

    stamp = clock.split()[0]
    try:
        day = date.fromisoformat(stamp)
    except ValueError as malformed:
        raise Unreadable(f"the fixture's clock is not a date: {clock!r}") from malformed
    named = clock.partition("(")[2].partition(")")[0].strip()
    actual = WEEKDAYS[day.isoweekday() - 1]
    if named and named.casefold() != actual.casefold():
        raise Unreadable(
            f"the fixture's clock calls {stamp} a {named}, and it is a {actual}"
        )
    return iso_weekday(day.isoweekday())


def build_searcher(fixture: Mapping[str, Any], mode: SearchMode) -> Searcher:
    """The one searcher every case is judged against, in one mode."""

    facts = fixture["searcher"]
    ticked = int(facts["grid_cells"])
    if ticked > len(WEEK):
        raise Unreadable(
            f"the fixture ticks {ticked} cells and this harness knows {len(WEEK)}"
        )
    return Searcher(
        level=LevelReading(mu=float(facts["mu"]), sigma=float(facts["sigma"])),
        mode=mode,
        tags=tuple(facts["tags"]),
        grid=cells(*WEEK[:ticked]),
        radius_km=float(facts["radius_km"]),
        today=weekday(str(fixture["clock"])),
    )


def build_candidate(
    fixture: Mapping[str, Any], case: Mapping[str, Any]
) -> ScorableCandidate:
    """One judged candidate, through the same fenced type a search builds.

    The pair's combined uncertainty is **RacketSkill's** and is combined here,
    on the module's side of the fence, exactly as the matcher does it. Writing
    the combined figure into the fixture instead would be pinning arithmetic
    nobody runs.

    ``reliability`` is ``None`` for every case and that is the fixture's own
    *day-one term set*: nobody has a Player Score yet, so the term stands down
    for everybody and the basis is seven weights renormalised.
    """

    theirs = case["candidate"]
    mine = float(fixture["searcher"]["sigma"])
    sigma = float(theirs["sigma"])
    pair = combine_sigma(mine, sigma)
    shared = int(theirs["shared_cells"])
    return ScorableCandidate(
        player_id=f"case-{case['id']}",
        level=LevelReading(mu=float(theirs["mu"]), sigma=sigma),
        declared_intent=case["intent"],
        tags=tuple(theirs["tags"]),
        grid=cells(*WEEK[:shared], UNSHARED),
        radius_km=float(theirs["radius_km"]),
        area_code="PL-WAW-C",
        distance_km=float(theirs["km"]),
        combined=CombinedUncertainty(sigma=pair, confidence=confidence_percent(pair)),
        reliability=None,
    )


def score_case(
    fixture: Mapping[str, Any],
    case: Mapping[str, Any],
    mode_key: str,
    ruleset: Ruleset = LIVE_RULESET,
) -> Fit:
    """One judged case, scored in one mode against the live ruleset.

    **The only call to ``score`` in this package.** A second spelling of it would
    let the tables and the tests agree with each other perfectly while both
    disagreed with the engine.
    """

    return score(
        build_searcher(fixture, MODES[mode_key]),
        build_candidate(fixture, case),
        ruleset,
    )


def readings(
    fixture: Mapping[str, Any], ruleset: Ruleset = LIVE_RULESET
) -> list[Reading]:
    """Every (case, mode) the fixture states a reading for, re-derived.

    The fixture decides which modes a case is judged in, and that is a design
    fact rather than a gap: case 3′ is **two pairings**, because ADR-0103 gates
    at a mode-relative constant and one Δμ cannot serve both modes.
    """

    derived: list[Reading] = []
    for case in fixture["cases"]:
        judged_in = case.get("readings") or {}
        if not judged_in:
            # Loud rather than skipped. A case nobody scores is a verdict nobody
            # checks, and it would sit in the fixture reading as covered.
            raise Unreadable(
                f"case {case['id']} states no readings, so no mode judges it — "
                f"give it a `readings` block naming the modes it is judged in"
            )
        for mode_key in judged_in:
            derived.append(_read(fixture, case, mode_key, ruleset))
    return derived


def by_id(derived: Sequence[Reading], case_id: str, mode_key: str) -> Reading | None:
    """One reading, or ``None`` where the fixture judges that case in one mode."""

    return next(
        (
            reading
            for reading in derived
            if reading.case_id == case_id and reading.mode_key == mode_key
        ),
        None,
    )


def _read(
    fixture: Mapping[str, Any],
    case: Mapping[str, Any],
    mode_key: str,
    ruleset: Ruleset,
) -> Reading:
    mode = MODES[mode_key]
    fit = score_case(fixture, case, mode_key, ruleset)
    scored = {term.term: term for term in fit.terms}
    missing = [name for name, term in COLUMNS.items() if term not in scored]
    if missing:
        raise Unreadable(
            f"case {case['id']} {mode_key}: {', '.join(missing)} stood down, and a "
            f"judged pairing has no column for a term that produced no reading"
        )
    verdict = VERDICTS.get(str(case["verdict"]))
    if verdict is None:
        raise Unreadable(
            f"case {case['id']} is judged {case['verdict']!r}, which is not one of "
            f"{', '.join(VERDICTS)}"
        )
    return Reading(
        case_id=str(case["id"]),
        label=str(case["label"]),
        verdict=verdict,
        note=case.get("note"),
        mode_key=mode_key,
        mode=mode,
        fit=fit,
        delta_mu=abs(float(case["candidate"]["mu"]) - float(fixture["searcher"]["mu"])),
        sigma_pair=build_candidate(fixture, case).combined.sigma,
        balance_pct=_balance_pct(scored[Term.PREDICTED_BALANCE].value, ruleset),
        values=OrderedDict(
            (name, scored[term].value) for name, term in COLUMNS.items()
        ),
        blank_points=_blank_points(fit, ruleset, mode),
    )


def _balance_pct(value: float, ruleset: Ruleset) -> float:
    """The forecast percentage behind the term's normalised reading.

    Inverted through the clamp rather than recomputed from Δμ and σ. The
    coefficients have exactly one home and a second copy of them here would
    agree with the engine right up until the day somebody moved one — and the
    clamp bounds *are* the term's zero and one, so the inversion is exact.
    """

    rules = ruleset.balance
    return rules.pct_min + value * (rules.pct_max - rules.pct_min)


def _blank_points(fit: Fit, ruleset: Ruleset, mode: SearchMode) -> float:
    """The same pairing with both tag columns stood down, renormalised.

    This is the number §6 exists to print. Standing a column down redistributes
    its weight over the survivors, so *declaring nothing* is scored on a
    five-term basis — and on a socially blank pairing that beats *declaring
    everything*, which is the renormalisation pathology the measured zero of
    0.20 was built to refuse.

    It runs through the engine's own ``renormalised_weights`` and never a second
    copy of the arithmetic: a counterfactual computed differently from the thing
    it is a counterfactual to proves nothing at all.
    """

    kept = tuple(term.term for term in fit.terms if term.term not in TAG_TERMS)
    shares = renormalised_weights(ruleset.modes[mode].weights, kept)
    return sum(
        shares[term.term] * term.value for term in fit.terms if term.term in shares
    )


# ---------------------------------------------------------------------------
# The floor, re-derived
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FloorBound:
    """What the six judged verdicts leave room for, against what is configured.

    ``the-five-numbers.md`` §1 defines ``QUALITY_FLOOR`` by six judged cases
    rather than by an integer, and §11 makes turning a term on a ruleset release
    that re-runs them. That is an inequality, and this is it.
    """

    highest_hidden: float
    lowest_shown: float
    configured: int

    @property
    def holds(self) -> bool:
        return self.highest_hidden < self.configured <= self.lowest_shown

    @property
    def margin(self) -> float:
        """How far the floor sits below the lowest case it must still show."""

        return self.lowest_shown - self.configured

    def spelled(self) -> str:
        """The bound, in the form both documents print it."""

        return (
            f"{self.highest_hidden:.1f}  <  QUALITY_FLOOR  ≤  {self.lowest_shown:.1f}"
        )


def floor_bound(
    derived: Sequence[Reading], ruleset: Ruleset = LIVE_RULESET
) -> FloorBound:
    """``max(Fit | not shown) < QUALITY_FLOOR ≤ min(Fit | shown)``.

    Both sides must exist. A fixture with nothing hidden bounds the floor from
    below at nothing at all and would report a vacuous pass — which is the shape
    of failure this whole machine exists to refuse.
    """

    hidden = [reading.fit.points for reading in derived if not reading.is_shown]
    shown = [reading.fit.points for reading in derived if reading.is_shown]
    if not hidden or not shown:
        raise Unreadable(
            "the floor is read off a fixture with cases on both sides of it, and "
            f"this one has {len(shown)} shown and {len(hidden)} not shown"
        )
    return FloorBound(
        highest_hidden=max(hidden),
        lowest_shown=min(shown),
        configured=ruleset.floors.quality_floor,
    )
