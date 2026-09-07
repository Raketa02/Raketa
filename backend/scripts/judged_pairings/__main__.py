"""``python -m scripts.judged_pairings`` — re-derive the six and write them back.

Run from ``backend/``. There is one mode and no flags: it re-derives, it prints
the bound, and it regenerates. A dry run was offered here for a while and nothing
ever called it — the check runs the same derivation and reports what moved, which
is the only question a dry run was going to answer.

  exit 0  the tables reproduce, and the floor still sits inside its bound
  exit 1  the floor no longer holds
  exit 2  it could not run — no fixture, or a document with no marker

The drift half is the caller's: ``.github/scripts/check-judged-pairings.sh``
snapshots the generated files, runs this, and compares. It is not asked here
because *the tables moved* and *the floor moved* are different failures with
different fixes, and a single exit code for both would send half the people who
hit one to the wrong instructions.
"""

from __future__ import annotations

import sys

from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from scripts.judged_pairings.deriving import (
    REPO,
    FloorBound,
    Unreadable,
    floor_bound,
    read_fixture,
    readings,
)
from scripts.judged_pairings.tables import regenerate

RULE = "────────────────────────────────────────────────────────────────────────────"


def main() -> int:
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
    """Say which side broke, and what it means.

    A bound that fails silently is a bound nobody re-derives, and *the floor is
    too high* and *the floor is too low* have opposite fixes.
    """

    print(RULE, file=sys.stderr)
    print("  THE QUALITY FLOOR NO LONGER SITS INSIDE ITS JUDGED BOUND", file=sys.stderr)
    print(RULE, file=sys.stderr)
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
    print(RULE, file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
