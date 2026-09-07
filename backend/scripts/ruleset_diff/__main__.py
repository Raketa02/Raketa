"""``python -m scripts.ruleset_diff`` — re-derive the synthetic diff and write it.

Run from ``backend/``. One mode and one flag: it regenerates the population and
the answers, prints the diff against the committed answers, and writes both.

    poetry run python -m scripts.ruleset_diff                 # the committed corpus
    poetry run python -m scripts.ruleset_diff --density dense # on demand, not a gate

  exit 0  it ran; the report says what moved
  exit 2  it could not run

**The drift half is the caller's**: ``.github/scripts/check-ruleset-diff.sh``
snapshots the artifacts, runs this twice under two different ``PYTHONHASHSEED``
values, and compares. It is not decided here because *the ruleset moved* and
*the pipeline is not deterministic* are different failures with different fixes,
and one exit code for both would send half the people who hit one to the wrong
instructions — the same split ``scripts/judged_pairings`` draws one document
over.

**And what this is not.** It is not the judged pairings: that machine asks *does
this ruleset still show the six things we said it must*, which is pass/fail
against named verdicts. This one asks *how does this ruleset move a population*,
and it carries no threshold at all (``the-replay-harness.md`` §5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.engines.matchfit.v1 import MatchFitV1
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from scripts.ruleset_diff.answers import derive, read, write as write_answers
from scripts.ruleset_diff.population import (
    ARTIFACTS,
    REPO,
    Density,
    generate,
    write as write_population,
)
from scripts.ruleset_diff.report import compare, render


def answers_path(density: Density) -> Path:
    """The committed answers — **the baseline the next run diffs against**."""

    return ARTIFACTS / f"answers.{density.value}.json"


def population_path(density: Density) -> Path:
    """The committed population, so a generator edit is a visible diff."""

    return ARTIFACTS / f"population.{density.value}.json"


def main(argv: list[str] | None = None) -> int:
    parsed = argparse.ArgumentParser(prog="scripts.ruleset_diff")
    parsed.add_argument(
        "--density",
        choices=[density.value for density in Density],
        default=Density.THIN.value,
        help="which population to run. Only the thin one is a build gate.",
    )
    arguments = parsed.parse_args(argv)
    density = Density(arguments.density)

    population = generate(density)
    baseline = read(answers_path(density))
    answers = derive(population, LIVE_RULESET, MatchFitV1())
    diff = None if baseline is None else compare(baseline, answers)
    print(render(answers, diff))

    for path in (
        write_population(population, population_path(density)),
        write_answers(answers, answers_path(density)),
    ):
        print(f"  wrote {path.relative_to(REPO)}")
    print()
    print("  Commit both if the diff above is the change you meant to make.")
    print("  CI regenerates and diffs them (make test-ruleset-diff covers the check).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
