"""The judged-pairings reader: re-derive the six, regenerate their tables.

``docs/specs/matchmaking/judged-pairings.json`` holds one searcher and seven
candidate rows as **inputs** plus the verdict a human passed on each
(``docs/adr/0122``). Everything else about a judged pairing is *derived*: every
term value, every renormalised weight, every Fit. This package is the machine
that derives them, and it is the only one — the tables in
``the-judged-pairings.md`` and ``ranking-weights.md`` §10 are written from here,
and the §20.1 scenario tests score their cases through here. Two harnesses would
be two answers, and the second one drifts.

**Two modules, and the split is what they change for.** ``deriving`` reads the
fixture and scores it, and changes when a ruleset or a formula does. ``tables``
renders and writes, and changes when a document does. ``__main__`` is the
command. This is ``app/engines/matchfit/v1/``'s shape one directory over, for
the same reason.

**The floor re-derivation is the part a diff cannot do.**
``ranking-weights.md`` §11 has always demanded that *turning a term on is a
ruleset release that re-runs the six cases and may move the floor*. That is a
statement about an inequality::

    max(Fit | not shown)  <  QUALITY_FLOOR  ≤  min(Fit | shown)

and a document cannot fail. The command prints that bound and **exits non-zero
when the configured floor sits outside it** — so a weight release that quietly
hides the median stranger stops being something somebody has to notice.

It is not ``#183``'s replay harness and must not be merged into it. That machine
asks *how does this ruleset move the population* and has no floor in it; this
one asks *does this ruleset still show the six things we said it must*, which is
pass/fail against named verdicts.

Run it from ``backend/``::

    poetry run python -m scripts.judged_pairings
"""

from scripts.judged_pairings.deriving import (
    COLUMNS,
    DAY_PARTS,
    FIXTURE,
    JUDGED_DOC,
    MODES,
    REPO,
    SPECS,
    TAG_TERMS,
    UNSHARED,
    VERDICTS,
    WEEK,
    WEEKDAYS,
    WEIGHTS_DOC,
    FloorBound,
    Reading,
    Unreadable,
    Verdict,
    build_candidate,
    build_searcher,
    by_id,
    cells,
    floor_bound,
    read_fixture,
    readings,
    score_case,
    weekday,
)
from scripts.judged_pairings.tables import (
    BEGIN,
    END,
    regenerate,
    regions,
    render_bound,
    render_counterfactual,
    render_one_line_assertions,
    render_readings,
    render_totals,
    replace_region,
    rewrite_fixture,
)

__all__ = [
    "BEGIN",
    "COLUMNS",
    "DAY_PARTS",
    "END",
    "FIXTURE",
    "FloorBound",
    "JUDGED_DOC",
    "MODES",
    "REPO",
    "Reading",
    "SPECS",
    "TAG_TERMS",
    "UNSHARED",
    "Unreadable",
    "VERDICTS",
    "Verdict",
    "WEEK",
    "WEEKDAYS",
    "WEIGHTS_DOC",
    "build_candidate",
    "build_searcher",
    "by_id",
    "cells",
    "floor_bound",
    "read_fixture",
    "readings",
    "regenerate",
    "regions",
    "render_bound",
    "render_counterfactual",
    "render_one_line_assertions",
    "render_readings",
    "render_totals",
    "replace_region",
    "rewrite_fixture",
    "score_case",
    "weekday",
]
