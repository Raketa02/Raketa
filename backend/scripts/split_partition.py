"""``python -m scripts.split_partition`` — the split groups add up to the suite.

Run from ``backend/`` as ``make split-partition``, which passes the durations file
its targets use. Each of CI's backend shards is to run one group of
``make test-group`` (ADR-0181 §5, #489), so a shard layout is only as good as the
claim that **every collected test lands in exactly one group**. This checks that
claim for two and three groups, by collection alone:

  1. the suite, collected through ``make test`` — what a single run executes;
  2. each group, collected through ``make test-group`` — what a shard executes;
  3. the same again against a durations file gone stale on purpose: a third of
     its entries withheld, as if those tests were written after the last refresh,
     and one entry for a test that no longer exists.

  exit 0  every group layout adds up to the suite
  exit 1  one does not — the report names the tests
  exit 2  it could not run — a collection failed, or printed no ids to read

Both collections go **through the make targets**, never through a copy of their
flags, so the algorithm and the durations file checked here are a shard's. What
it cannot see is xdist: ``--collect-only`` turns distribution off, so the split is
made once, in one process, where a shard makes it in every worker — the same
deterministic selection over the same collection, which xdist refuses to run if
its workers disagree about. Checking the ids each shard actually *ran* is #489's
CI job; this is the collection half, runnable on a laptop in under a minute.

The third pass is the case the design rests on: a stale file may only unbalance
the groups, and pytest-split gives a test it does not know the average duration —
this is where that is seen rather than assumed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

#: The layouts checked. Two is CI's first; three is the next one it would add.
SPLITS = (2, 3)

#: How many ids of each kind a failure prints before saying how many it left out.
SHOWN = 10


@dataclass(frozen=True)
class Partition:
    """How a suite's ids and its groups' ids disagree, if they do."""

    missing: tuple[str, ...]
    duplicated: tuple[str, ...]
    foreign: tuple[str, ...]

    @property
    def adds_up(self) -> bool:
        return not (self.missing or self.duplicated or self.foreign)


def partition_of(
    collected: Sequence[str], groups: Mapping[int, Sequence[str]]
) -> Partition:
    """A test in no group is *missing*, one in two is *duplicated*, and one a
    group holds that the suite never collected is *foreign* — which only a
    collection that differs between runs can produce."""

    counts = Counter(nodeid for ids in groups.values() for nodeid in ids)
    suite = set(collected)
    return Partition(
        missing=tuple(sorted(suite - counts.keys())),
        duplicated=tuple(sorted(n for n, c in counts.items() if c > 1)),
        foreign=tuple(sorted(counts.keys() - suite)),
    )


def nodeids_in(output: str) -> list[str]:
    """The ids ``pytest --collect-only -q`` printed, one per line — and nothing
    of pytest-split's banner or the summary around them."""

    return [
        line
        for line in output.splitlines()
        if line.startswith("tests/") and "::" in line
    ]


class CollectionFailed(Exception):
    pass


def _collect(target: str, **make_vars: str) -> list[str]:
    assignments = [f"{name}={value}" for name, value in make_vars.items()]
    completed = subprocess.run(
        ["make", "-s", target, *assignments, "PYTEST_ARGS=--collect-only"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )
    said = " ".join(["make", target, *assignments])
    if completed.returncode != 0:
        raise CollectionFailed(
            f"{said} exited {completed.returncode}:\n"
            + completed.stdout[-2000:]
            + completed.stderr[-2000:]
        )
    ids = nodeids_in(completed.stdout)
    if not ids:
        # Read nothing, and every group would add up to nothing — a pass that
        # checked no test. A second `-q` in addopts prints files, not ids.
        raise CollectionFailed(f"{said} printed no test ids to read")
    return ids


def _layouts_add_up(suite: Sequence[str], durations: Path) -> bool:
    known = set(json.loads(durations.read_text())) if durations.exists() else set()
    unknown = sum(1 for nodeid in suite if nodeid not in known)
    print(f"  {len(suite) - unknown} of {len(suite)} tests have a recorded duration")

    every_layout_adds_up = True
    for splits in SPLITS:
        groups = {
            group: _collect(
                "test-group",
                GROUP=str(group),
                SPLITS=str(splits),
                DURATIONS=str(durations),
            )
            for group in range(1, splits + 1)
        }
        partition = partition_of(suite, groups)
        sizes = " + ".join(str(len(ids)) for ids in groups.values())
        total = sum(len(ids) for ids in groups.values())
        if partition.adds_up:
            print(
                f"  SPLITS={splits}: {sizes} = {total}"
                " — every test in exactly one group"
            )
            continue
        every_layout_adds_up = False
        print(f"  SPLITS={splits}: {sizes} = {total} — DOES NOT ADD UP")
        for kind, ids in (
            ("in no group", partition.missing),
            ("in more than one group", partition.duplicated),
            ("in a group but never collected", partition.foreign),
        ):
            if ids:
                print(f"    {len(ids)} {kind}:")
                for nodeid in ids[:SHOWN]:
                    print(f"      {nodeid}")
                if len(ids) > SHOWN:
                    print(f"      … and {len(ids) - SHOWN} more")
    return every_layout_adds_up


def a_stale_copy_of(durations: Path, into: Path) -> Path:
    """The committed file with a third of its entries withheld and one entry for
    a test that no longer exists."""

    recorded = json.loads(durations.read_text()) if durations.exists() else {}
    stale = {
        nodeid: seconds
        for index, (nodeid, seconds) in enumerate(sorted(recorded.items()))
        if index % 3
    }
    stale["tests/unit/test_deleted_since_the_refresh.py::test_gone"] = 1.0
    path = into / "stale_durations.json"
    path.write_text(json.dumps(stale, indent=4, sort_keys=True))
    return path


def main(argv: Sequence[str]) -> int:
    if len(argv) != 1:
        print(
            "usage: python -m scripts.split_partition <durations file>", file=sys.stderr
        )
        return 2
    durations = BACKEND / argv[0]
    try:
        suite = _collect("test")
        if len(suite) != len(set(suite)):
            raise CollectionFailed("the suite's own collection repeats an id")
        print(f"The suite: {len(suite)} tests, collected through `make test`.")

        print(f"Durations as committed ({argv[0]}):")
        committed_adds_up = _layouts_add_up(suite, durations)

        with tempfile.TemporaryDirectory() as scratch:
            print("Durations gone stale (a third withheld, one for a deleted test):")
            stale = a_stale_copy_of(durations, into=Path(scratch))
            stale_adds_up = _layouts_add_up(suite, stale)
    except CollectionFailed as failure:
        print(f"Could not collect — {failure}", file=sys.stderr)
        return 2

    if committed_adds_up and stale_adds_up:
        print("OK — every layout adds up to the suite, stale durations included.")
        return 0
    print("A group layout does not add up to the suite — a shard would test less.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
