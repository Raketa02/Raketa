"""The judged-pairings reader: re-derive the six, regenerate their tables.

``docs/specs/matchmaking/judged-pairings.json`` holds one searcher and seven
candidate rows as **inputs** — μ, σ, grid cells, distance, both radii, tag ids,
declared intent — plus the verdict a human passed on each
(``docs/adr/0122``). Everything else about a judged pairing is *derived*: every
term value, every renormalised weight, every Fit. This module is the machine
that derives them, and it is the only one: the tables in
``the-judged-pairings.md`` and ``ranking-weights.md`` §10 are written from here,
and the §20.1 scenario tests score their cases through here.

**On this repository's generate-commit-diff idiom**, after ``make gen-api``: the
derived halves are regenerated, committed, and CI regenerates and diffs them. A
hand edit to a generated table fails the build, and a formula change re-derives
the whole fixture for free — which is exactly what ``ranking-weights.md`` §10
claims the fixture buys and could not do against prose.

**The floor re-derivation is the part a diff cannot do.**
``ranking-weights.md`` §11 has always demanded that *turning a term on is a
ruleset release that re-runs the six cases and may move the floor*. That is a
statement about an inequality::

    max(Fit | not shown)  <  QUALITY_FLOOR  ≤  min(Fit | shown)

and a document cannot fail. This module prints that bound and **exits non-zero
when the configured floor sits outside it** — so a weight release that quietly
hides the median stranger stops being something somebody has to notice.

It is not ``#183``'s replay harness and must not be merged into it. That machine
asks *how does this ruleset move the population* and has no floor in it; this
one asks *does this ruleset still show the six things we said it must*, which is
pass/fail against named verdicts.

Run it from ``backend/``::

    poetry run python -m scripts.judged_pairings            # regenerate
    poetry run python -m scripts.judged_pairings --check    # re-derive only
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

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
from app.kernel import iso_weekday
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.availability import DayPart

#: The repository root, from this file's own place in it. Derived rather than
#: passed in: a generator that can be pointed at a different tree is one that can
#: quietly regenerate nothing.
REPO = Path(__file__).resolve().parents[2]

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

#: The verdicts a human passed, spelled for a reader. ``shown_docked`` is case
#: 6's and says the dock happened somewhere that is not Fit. The emphasis is the
#: document's — a console gets ``PLAIN`` below, because a terminal printing
#: ``**Not shown**`` is a table that leaked.
VERDICTS = {
    "shown": "Shown",
    "shown_docked": "Shown, docked",
    "not_shown": "**Not shown**",
}

PLAIN = {"shown": "shown", "shown_docked": "shown, docked", "not_shown": "NOT SHOWN"}

#: Which verdicts mean the candidate reached a screen. The floor's bound is read
#: across this split and nothing else.
SHOWN = frozenset({"shown", "shown_docked"})

#: The parts of a day, in the order the platform lays them out — the one
#: vocabulary fact the engine is told rather than allowed to know.
DAY_PARTS = tuple(part.value for part in DayPart)

#: A Wednesday. On a Saturday ``TODAY`` and ``WEEKEND`` collapse into one cell,
#: which is the fixture's own stated reason for the clock it pins.
WEDNESDAY = iso_weekday(3)

#: The searcher's week, as four concrete cells. The fixture says only *four of
#: twenty-one*, and that is not an omission: availability reads
#: ``|shared| / |mine|`` and **no constant at all**, so which four they are moves
#: no value in any case. The identity is needed anyway, because the term's
#: evidence names the next cell the two of them share.
WEEK: tuple[tuple[int, DayPart], ...] = (
    (1, DayPart.EVENING),
    (3, DayPart.EVENING),
    (5, DayPart.EVENING),
    (6, DayPart.MORNING),
)

#: A cell the searcher did **not** tick. It is what makes *they share none of
#: your times* a measurement rather than a blank week: a candidate with no grid
#: at all reads *we do not know when they play*, which stands the term down and
#: renormalises its weight onto the other six. Case 2's whole assertion is about
#: what zero overlap costs, so the two readings must not be spelled the same way.
UNSHARED = (7, DayPart.AFTERNOON)


@dataclass(frozen=True)
class Reading:
    """One judged case scored in one mode, with what the tables print of it."""

    case_id: str
    label: str
    verdict: str
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
        return self.verdict in SHOWN

    @property
    def verdict_text(self) -> str:
        """The verdict as a document prints it, emphasis and all."""

        spelled = VERDICTS[self.verdict]
        return f"{spelled}, {self.note}" if self.note else spelled

    @property
    def verdict_plain(self) -> str:
        """The same verdict for a terminal, with the Markdown taken out."""

        spelled = PLAIN[self.verdict]
        return f"{spelled}, {self.note}" if self.note else spelled


class Unreadable(Exception):
    """The harness cannot run — a missing fixture, a document without markers.

    Separate from a failed re-derivation on purpose, and carried out to a
    different exit code. *The floor moved* is a finding; *I could not look* is
    not, and a check that reports the second as the first is one that reports
    green the day somebody moves a file.
    """


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


def cells(*specs: tuple[int, DayPart]) -> tuple[GridCell, ...]:
    return tuple(GridCell(day=iso_weekday(day), part=part.value) for day, part in specs)


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
        today=WEDNESDAY,
        day_parts=DAY_PARTS,
    )


def build_candidate(
    fixture: Mapping[str, Any], case: Mapping[str, Any]
) -> ScorableCandidate:
    """One judged candidate, through the same fenced type a search builds.

    The pair's combined uncertainty is **RacketSkill's** and is combined here,
    on the module's side of the fence, exactly as the matcher does it. Writing
    the combined figure into the fixture instead would be pinning arithmetic
    nobody runs.
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
    """One judged case, scored in one mode against the live ruleset."""

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


def _read(
    fixture: Mapping[str, Any],
    case: Mapping[str, Any],
    mode_key: str,
    ruleset: Ruleset,
) -> Reading:
    mode = MODES[mode_key]
    candidate = build_candidate(fixture, case)
    fit = score(build_searcher(fixture, mode), candidate, ruleset)
    scored = {term.term: term for term in fit.terms}
    missing = [name for name, term in COLUMNS.items() if term not in scored]
    if missing:
        raise Unreadable(
            f"case {case['id']} {mode_key}: {', '.join(missing)} stood down, and a "
            f"judged pairing has no column for a term that produced no reading"
        )
    return Reading(
        case_id=str(case["id"]),
        label=str(case["label"]),
        verdict=str(case["verdict"]),
        note=case.get("note"),
        mode_key=mode_key,
        mode=mode,
        fit=fit,
        delta_mu=abs(float(case["candidate"]["mu"]) - float(fixture["searcher"]["mu"])),
        sigma_pair=candidate.combined.sigma,
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


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_readings(derived: Sequence[Reading]) -> str:
    """§3 — every term value and every Fit, one row per judged (case, mode)."""

    header = "| Case | Mode | Δμ | " + " | ".join(COLUMNS) + " | **Fit** | Verdict |"
    rule = "|---|---|" + "--:|" * (1 + len(COLUMNS)) + "---|---|"
    rows = [
        "| "
        + " | ".join(
            (
                reading.case_id,
                reading.mode_key,
                f"{reading.delta_mu:.3f}",
                *(f"{reading.values[name]:.3f}" for name in COLUMNS),
                f"**{reading.fit.points:.1f}**",
                reading.verdict_text,
            )
        )
        + " |"
        for reading in derived
    ]
    return "\n".join([header, rule, *rows])


def render_totals(derived: Sequence[Reading]) -> str:
    """`ranking-weights.md` §10 — one row per case, a column per mode."""

    by_case: "OrderedDict[str, dict[str, Reading]]" = OrderedDict()
    for reading in derived:
        by_case.setdefault(reading.case_id, {})[reading.mode_key] = reading

    header = "| Case | Verdict | Comp | Fun |"
    rule = "|---|---|--:|--:|"
    rows = []
    for case_id, modes in by_case.items():
        first = next(iter(modes.values()))
        name = f"**{case_id}**" if not first.is_shown else case_id
        points = [
            f"{modes[key].fit.points:.1f}" if key in modes else "—" for key in MODES
        ]
        rows.append(
            f"| {name} · {first.label} | {first.verdict_text} | "
            + " | ".join(points)
            + " |"
        )
    return "\n".join([header, rule, *rows])


def render_bound(bound: FloorBound) -> str:
    """The inequality, fenced, in the form both documents already print it."""

    return "```\n" + bound.spelled() + "\n```"


def render_counterfactual(derived: Sequence[Reading]) -> str:
    """§6 — what *socially blank* is worth, against standing the columns down."""

    blank = {reading.mode_key: reading for reading in derived if reading.case_id == "1"}
    exceptional = {
        reading.mode_key: reading for reading in derived if reading.case_id == "4"
    }
    if not blank:
        raise Unreadable("§6's counterfactual is case 1's, and case 1 is not judged")

    def row(label: str, cell: "dict[str, str]") -> str:
        return f"| {label} | " + " | ".join(cell.get(key, "—") for key in MODES) + " |"

    return "\n".join(
        [
            "| | comp | fun |",
            "|---|--:|--:|",
            row(
                "Case 1, tags declared, nothing fires",
                {key: f"{r.fit.points:.1f}" for key, r in blank.items()},
            ),
            row(
                "Case 1, **both columns stood down**",
                {key: f"**{r.blank_points:.1f}**" for key, r in blank.items()},
            ),
            row(
                "Case 4, *everything exceptional*",
                {key: f"{r.fit.points:.1f}" for key, r in exceptional.items()},
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Writing it back
# ---------------------------------------------------------------------------

#: What a generated region looks like in a Markdown document. The names are the
#: contract: a region whose marker moved is a region that stops being
#: regenerated, and that is a silent failure, so a missing marker raises.
BEGIN = "<!-- generated: {name} — `make gen-judged-pairings`; do not edit by hand -->"
END = "<!-- /generated: {name} -->"


def replace_region(text: str, name: str, body: str, where: Path) -> str:
    """Swap one marked region's body, leaving the markers themselves in place."""

    begin, end = BEGIN.format(name=name), END.format(name=name)
    start, stop = text.find(begin), text.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise Unreadable(f"{where.name} has no '{name}' region to regenerate")
    return text[: start + len(begin)] + "\n" + body + "\n" + text[stop:]


def _rounded(value: float, places: int) -> float:
    """A derived number as the fixture carries it: rounded, and never a string.

    ``round`` and not a format: the fixture is read by machines, and a diff
    between ``0.2`` and ``0.2000`` is noise a reviewer has to read past.
    """

    return round(value, places)


def rewrite_fixture(
    fixture: dict[str, Any], derived: Sequence[Reading], ruleset: Ruleset
) -> dict[str, Any]:
    """The fixture with its derived halves re-derived, its inputs untouched.

    ``basis`` and every ``readings`` block are computed; the searcher, the
    candidates, the verdicts and the labels are what a human judged and are
    never written here. That split **is** ADR-0122: a judged pairing is two
    people, never a profile of scores.
    """

    fixture["basis"] = OrderedDict(
        (
            key,
            OrderedDict(
                (name, _rounded(share, 4))
                for name, share in _basis(MODES[key], ruleset).items()
            ),
        )
        for key in MODES
    )
    by_case = {(reading.case_id, reading.mode_key): reading for reading in derived}
    for case in fixture["cases"]:
        case["readings"] = OrderedDict(
            (
                mode_key,
                _reading_block(by_case[(str(case["id"]), mode_key)]),
            )
            for mode_key in case["readings"]
        )
    return fixture


def _basis(mode: SearchMode, ruleset: Ruleset) -> "OrderedDict[str, float]":
    """The day-one basis: the seven live terms, renormalised over themselves.

    Reliability stands down for everybody on day one — nobody has a Player Score
    yet — so the basis every judged reading was computed on is seven weights
    scaled by ×100/87 competitive and ×100/91 for fun, and it is derived from the
    weights rather than restated beside them.
    """

    weights = ruleset.modes[mode].weights
    shares = renormalised_weights(weights, tuple(COLUMNS.values()))
    return OrderedDict((name, shares[term]) for name, term in COLUMNS.items())


def _reading_block(reading: Reading) -> "OrderedDict[str, Any]":
    return OrderedDict(
        (
            ("delta_mu", _rounded(reading.delta_mu, 4)),
            ("sigma_pair", _rounded(reading.sigma_pair, 4)),
            ("balance_pct", _rounded(reading.balance_pct, 2)),
            (
                "terms",
                OrderedDict(
                    (name, _rounded(reading.values[name], 4)) for name in COLUMNS
                ),
            ),
            ("fit", _rounded(reading.fit.points, 2)),
        )
    )


def regenerate(
    fixture: dict[str, Any],
    derived: Sequence[Reading],
    bound: FloorBound,
    ruleset: Ruleset,
) -> list[Path]:
    """Write every derived half, and report which files changed."""

    written: list[Path] = []
    regions = {
        JUDGED_DOC: (
            ("judged-readings", render_readings(derived)),
            ("floor-bound", render_bound(bound)),
            ("blank-counterfactual", render_counterfactual(derived)),
        ),
        WEIGHTS_DOC: (
            ("judged-totals", render_totals(derived)),
            ("floor-bound", render_bound(bound)),
        ),
    }
    for path, bodies in regions.items():
        if not path.is_file():
            raise Unreadable(f"the document to regenerate is gone from {path}")
        before = path.read_text(encoding="utf-8")
        after = before
        for name, body in bodies:
            after = replace_region(after, name, body, path)
        if after != before:
            path.write_text(after, encoding="utf-8")
            written.append(path)

    rewritten = (
        json.dumps(
            rewrite_fixture(fixture, derived, ruleset), indent=2, ensure_ascii=False
        )
        + "\n"
    )
    if rewritten != FIXTURE.read_text(encoding="utf-8"):
        FIXTURE.write_text(rewritten, encoding="utf-8")
        written.append(FIXTURE)
    return written


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.judged_pairings",
        description=(
            "Re-derive the six judged pairings against the live ruleset, "
            "re-derive the quality floor's bound, and regenerate their tables."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive and print, but write nothing",
    )
    args = parser.parse_args(argv)

    try:
        fixture = read_fixture()
        derived = readings(fixture, LIVE_RULESET)
        bound = floor_bound(derived, LIVE_RULESET)
    except Unreadable as unreadable:
        print(f"judged pairings: {unreadable}", file=sys.stderr)
        return 2

    print(f"Ruleset {LIVE_RULESET.version} — {len(derived)} judged readings.")
    print()
    for reading in derived:
        print(
            f"  {reading.case_id:>8} {reading.mode_key:<5} "
            f"Fit {reading.fit.points:6.2f}   {reading.verdict_plain}"
        )
    print()
    print(
        f"  max(Fit | not shown) = {bound.highest_hidden:.2f}"
        f"  <  QUALITY_FLOOR = {bound.configured}"
        f"  ≤  {bound.lowest_shown:.2f} = min(Fit | shown)"
    )
    print()

    if not bound.holds:
        _report_floor(bound)
        return 1

    print(
        f"OK — the floor holds, by {bound.margin:.2f} points under the lowest case "
        f"it must still show."
    )

    if args.check:
        return 0

    try:
        written = regenerate(fixture, derived, bound, LIVE_RULESET)
    except Unreadable as unreadable:
        print(f"judged pairings: {unreadable}", file=sys.stderr)
        return 2

    if written:
        for path in written:
            print(f"  regenerated {path.relative_to(REPO)}")
        print("Commit the result — CI regenerates and diffs it.")
    else:
        print("  nothing to regenerate; every table already reproduces.")
    return 0


def _report_floor(bound: FloorBound) -> None:
    """Say which side broke, and what it means. A bound that fails silently is
    a bound nobody re-derives."""

    print(
        "────────────────────────────────────────────────────────────────────────────",
        file=sys.stderr,
    )
    print("  THE QUALITY FLOOR NO LONGER SITS INSIDE ITS JUDGED BOUND", file=sys.stderr)
    print(
        "────────────────────────────────────────────────────────────────────────────",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    if bound.configured > bound.lowest_shown:
        print(
            f"  QUALITY_FLOOR = {bound.configured} now hides a case judged shown, "
            f"which reads {bound.lowest_shown:.2f}.",
            file=sys.stderr,
        )
    else:
        print(
            f"  QUALITY_FLOOR = {bound.configured} now shows a case judged hidden, "
            f"which reads {bound.highest_hidden:.2f}.",
            file=sys.stderr,
        )
    print(file=sys.stderr)
    print(
        "  ranking-weights.md §11: turning a term on is a ruleset release that\n"
        "  re-runs the six cases and may move the floor. This is that release.\n"
        "\n"
        "  Fix — one of two, and both land as an ADR naming the case that now\n"
        "  decides differently (the-five-numbers.md §1):\n"
        "\n"
        "      · move QUALITY_FLOOR inside the bound above, or\n"
        "      · re-judge the case whose verdict the ruleset no longer supports.\n",
        file=sys.stderr,
    )
    print(
        "────────────────────────────────────────────────────────────────────────────",
        file=sys.stderr,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
