"""The derived halves, written back into the documents they belong to.

This half **renders and writes**; ``deriving`` reads and scores. Everything here
changes for a document reason — a column renamed, a sentence rewritten, a fourth
table generated — and nothing here knows how a Fit is computed.

**On this repository's generate-commit-diff idiom**, after ``make gen-api``: the
derived halves are regenerated, committed, and CI regenerates and diffs them. A
hand edit to a generated table fails the build, and a formula change re-derives
the whole fixture for free — which is exactly what ``ranking-weights.md`` §10
claims the fixture buys and could not do against prose.

**The regions are named and a missing marker raises.** A region whose marker
somebody deleted is a region that silently stops being regenerated, which reads
as a table that always reproduces — the worst of the failures available here,
because it is the one nobody sees.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Mapping, Sequence

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.v1 import renormalised_weights
from scripts.judged_pairings.deriving import (
    COLUMNS,
    FIXTURE,
    JUDGED_DOC,
    MODES,
    WEIGHTS_DOC,
    FloorBound,
    Reading,
    Unreadable,
    by_id,
)

#: What a generated region looks like in a Markdown document. The names are the
#: contract: a region whose marker moved is a region that stops being
#: regenerated, and that is a silent failure, so a missing marker raises.
BEGIN = "<!-- generated: {name} — `make gen-judged-pairings`; do not edit by hand -->"
END = "<!-- /generated: {name} -->"

#: Relative from `docs/specs/matchmaking/`, which is where every generated region
#: lives. Named because §5's row is the one sentence in this file long enough
#: that the link would otherwise wrap mid-path.
LIVENESS_ADR = "../../adr/0099-relaxation-offers-the-searchers-own-asks.md"


def replace_region(text: str, name: str, body: str, where: Path) -> str:
    """Swap one marked region's body, leaving the markers themselves in place."""

    begin, end = BEGIN.format(name=name), END.format(name=name)
    start, stop = text.find(begin), text.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise Unreadable(f"{where.name} has no '{name}' region to regenerate")
    return text[: start + len(begin)] + "\n" + body + "\n" + text[stop:]


# ---------------------------------------------------------------------------
# The tables
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

    rows = []
    for case_id, modes in by_case.items():
        first = next(iter(modes.values()))
        name = case_id if first.is_shown else f"**{case_id}**"
        points = [
            f"{modes[key].fit.points:.1f}" if key in modes else "—" for key in MODES
        ]
        rows.append(
            f"| {name} · {first.label} | {first.verdict_text} | "
            + " | ".join(points)
            + " |"
        )
    return "\n".join(["| Case | Verdict | Comp | Fun |", "|---|---|--:|--:|", *rows])


def render_bound(bound: FloorBound) -> str:
    """The inequality, fenced, in the form both documents print it."""

    return "```\n" + bound.spelled() + "\n```"


def render_one_line_assertions(
    derived: Sequence[Reading], fixture: Mapping[str, Any]
) -> str:
    """§5 — the two cases that differ from case 1 by exactly one input.

    The argument is this document's and lives here; **both numbers in it are
    derived**, which is the whole reason the section is generated. It said
    *12.64 competitive, 17.58 for fun* in hand-typed bold until now, so a weight
    release would have regenerated §3, §6 and §10 and left this one silently
    wrong — which is worse than never having generated anything, because the
    document would still look maintained.
    """

    case = {str(row["id"]): row["candidate"] for row in fixture["cases"]}
    for wanted in ("1", "2", "6"):
        if wanted not in case:
            raise Unreadable(
                f"§5 contrasts case {wanted} against case 1, and it is gone"
            )

    avail = []
    for key in MODES:
        reading = by_id(derived, "1", key)
        if reading is None:
            raise Unreadable(
                f"§5 reads case 1's availability weight, and {key} is gone"
            )
        avail.append(f"{reading.weight_of('avail'):.2f}")

    return "\n".join(
        [
            "| | Differs by | Assertion |",
            "|---|---|---|",
            f"| **Case 2** | `shared_cells` {case['1']['shared_cells']} → "
            f"{case['2']['shared_cells']} | Fit falls by exactly the availability "
            f"weight — **{avail[0]} competitive, {avail[1]} for fun**. Availability "
            "overlap is evidence a game can be *arranged*, and its absence costs its "
            "weight and not a point more |",
            f"| **Case 6** | candidate radius {case['1']['radius_km']} → "
            f"{case['6']['radius_km']} km | `Fit(6) == Fit(1)` **identically**. The "
            "searcher sitting outside the candidate's ring is a Liveness dock and "
            f"never enters Fit ([ADR-0099]({LIVENESS_ADR})) |",
        ]
    )


def render_counterfactual(derived: Sequence[Reading]) -> str:
    """§6 — what *socially blank* is worth, against standing the columns down."""

    blank = {key: by_id(derived, "1", key) for key in MODES}
    exceptional = {key: by_id(derived, "4", key) for key in MODES}
    if not any(blank.values()):
        raise Unreadable("§6's counterfactual is case 1's, and case 1 is not judged")

    def row(label: str, cell: Mapping[str, str]) -> str:
        return f"| {label} | " + " | ".join(cell.get(key, "—") for key in MODES) + " |"

    def points(
        readings: Mapping[str, Reading | None], attribute: str, emphasis: str
    ) -> Mapping[str, str]:
        return {
            key: emphasis.format(getattr(reading, attribute))
            for key, reading in readings.items()
            if reading is not None
        }

    return "\n".join(
        [
            "| | comp | fun |",
            "|---|--:|--:|",
            row(
                "Case 1, tags declared, nothing fires",
                {key: f"{r.fit.points:.1f}" for key, r in blank.items() if r},
            ),
            row(
                "Case 1, **both columns stood down**",
                points(blank, "blank_points", "**{:.1f}**"),
            ),
            row(
                "Case 4, *everything exceptional*",
                {key: f"{r.fit.points:.1f}" for key, r in exceptional.items() if r},
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Writing it back
# ---------------------------------------------------------------------------


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
    recorded = {(reading.case_id, reading.mode_key): reading for reading in derived}
    for case in fixture["cases"]:
        case["readings"] = OrderedDict(
            (mode_key, _reading_block(recorded[(str(case["id"]), mode_key)]))
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

    shares = renormalised_weights(ruleset.modes[mode].weights, tuple(COLUMNS.values()))
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


def regions(
    fixture: Mapping[str, Any], derived: Sequence[Reading], bound: FloorBound
) -> "OrderedDict[Path, tuple[tuple[str, str], ...]]":
    """Every generated region, by the document it lives in.

    One place, because it is the answer to *what does a hand edit fail on* and
    the check scopes its comparison to exactly these files.
    """

    return OrderedDict(
        (
            (
                JUDGED_DOC,
                (
                    ("judged-readings", render_readings(derived)),
                    ("floor-bound", render_bound(bound)),
                    (
                        "one-line-assertions",
                        render_one_line_assertions(derived, fixture),
                    ),
                    ("blank-counterfactual", render_counterfactual(derived)),
                ),
            ),
            (
                WEIGHTS_DOC,
                (
                    ("judged-totals", render_totals(derived)),
                    ("floor-bound", render_bound(bound)),
                ),
            ),
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
    for path, bodies in regions(fixture, derived, bound).items():
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
