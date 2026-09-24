"""``python -m scripts.shards_add_up <report>...`` — the groups ran the suite.

Run from ``backend/`` by ``.github/scripts/check-shards-add-up.sh``, which CI's
add-up job calls with every group's report. CI's backend tests are a matrix of
groups, each running ``make test-group`` on a runner of its own and writing a
JUnit report of the tests it ran (ADR-0181 §5, #489). A group layout that drops
a test, or runs one twice, is a green run that tested something other than the
suite, so this holds the reports' union against it:

  1. the suite, collected once through ``make test``, as split_partition does;
  2. every report, read back into the suite's test ids;
  3. every collected test in exactly one group — ``partition_of``'s arithmetic.

  exit 0  every collected test ran, in exactly one group
  exit 1  one did not — the output counts the tests missing, run twice or never
          collected, and names the first of each
  exit 2  it could not run — a report is unreadable, the collection failed, or
          the check itself crashed: never a verdict

``make split-partition`` is the collection half, runnable on a laptop; this is
the half that reads what actually ran, so it needs a run's reports.

**A report does not carry a test's id.** pytest's JUnit writer mangles each id
into a ``classname`` and a ``name``, so an id is recovered by mangling the
suite's ids the same way — with pytest's own functions, never a copy of them —
and matching. They are private (``_pytest``), which is the price of reading the
writer's own rule; a pytest that moved them fails this at import, and
check-shards-add-up.sh reports that as a check that could not run. And one
test can own two ``<testcase>`` elements: a failure in the
call and an error in the teardown are written separately. A report records one
pytest session, which runs a test once, so its ids are read as a set; a test
that ran twice is a test in two groups.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from pathlib import Path

from _pytest.junitxml import bin_xml_escape, mangle_test_address

from scripts.split_partition import (
    CollectionFailed,
    collect_suite,
    partition_of,
    print_disagreement,
)


class UnreadableReport(Exception):
    pass


#: A test as a JUnit report names it — its ``classname`` and its ``name``.
Address = tuple[str, str]


def report_names(suite: Sequence[str]) -> dict[Address, str]:
    """Each collected id under the address a JUnit report gives it. Two ids that
    read alike are refused: no report could say which of them ran, and that is
    the suite's doing, not a report's."""

    names: dict[Address, str] = {}
    for nodeid in suite:
        parts = mangle_test_address(nodeid)
        address = ".".join(parts[:-1]), str(bin_xml_escape(parts[-1]))
        if names.setdefault(address, nodeid) != nodeid:
            raise CollectionFailed(
                f"{names[address]} and {nodeid} read alike in a JUnit report,"
                " so no report can say which of them ran"
            )
    return names


def ids_in_report(report: Path, names: Mapping[Address, str]) -> list[str]:
    """The ids of the tests *report* says ran, each once, as the suite names
    them. A test the suite never collected comes back by its report name,
    ``classname.name``."""

    try:
        cases = ET.parse(report).getroot().iter("testcase")
        ran = {(case.get("classname", ""), case.get("name", "")) for case in cases}
    except (OSError, ET.ParseError) as exc:
        unreadable = f"{report.name} is not a readable report ({exc})"
        raise UnreadableReport(unreadable) from exc
    return sorted(names.get(each) or ".".join(filter(None, each)) for each in ran)


def main(argv: Sequence[str]) -> int:
    if not argv:
        print("usage: python -m scripts.shards_add_up <report.xml>...", file=sys.stderr)
        return 2
    reports = [Path(arg) for arg in argv]
    try:
        suite = collect_suite()
        names = report_names(suite)
        groups = {report.name: ids_in_report(report, names) for report in reports}
    except (CollectionFailed, UnreadableReport) as failure:
        print(f"Could not add the groups up — {failure}", file=sys.stderr)
        return 2

    print(f"The suite: {len(suite)} tests, collected through `make test`.")
    for name, ids in groups.items():
        print(f"  {name}: {len(ids)} ran")
    partition = partition_of(suite, groups)
    sizes = " + ".join(str(len(ids)) for ids in groups.values())
    total = sum(len(ids) for ids in groups.values())
    if partition.adds_up:
        print(f"OK — {sizes} = {total}: every collected test ran in exactly one group.")
        return 0

    print(f"{sizes} = {total} of {len(suite)} — THE GROUPS DO NOT ADD UP TO THE SUITE")
    print_disagreement(partition, indent="  ")
    print(
        "\nA shard layout that drops or repeats a test is a green run that tested"
        " something other than the suite.\n`make split-partition` from backend/ says"
        " whether the layout itself is at fault; a test whose ids differ\nbetween two"
        " collections — parameters drawn from a set, say (ADR-0105) — can land in"
        " two groups or none.\nA group whose report never arrived has all of its"
        " tests missing."
    )
    if os.environ.get("GITHUB_ACTIONS"):
        counts = (
            f"{len(partition.missing)} in no group, "
            f"{len(partition.duplicated)} in two or more, "
            f"{len(partition.foreign)} never collected"
        )
        print(f"::error title=The shards do not add up::{counts} — see the job log")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # a crash is a check that could not run, never a verdict
        print(f"shards_add_up could not run: {exc!r}", file=sys.stderr)
        sys.exit(2)
