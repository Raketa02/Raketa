#!/bin/bash
# ---------------------------------------------------------------------------
# ci-ok — the one status that says whether a push is green (ADR-0181 §4).
#
#   NEEDS='${{ toJSON(needs) }}' bash .github/scripts/check-ci-ok.sh verdict
#   bash .github/scripts/check-ci-ok.sh wiring [path/to/ci.yml]    # or: make ci-ok
#
# CI is a dozen parallel jobs, and a human reading a pull request reads one line.
# That line is only worth reading if it cannot be green while anything under it
# is not, and there are exactly two ways for it to lie:
#
#   verdict  a needed job went wrong and the summary passed anyway. Every needed
#            job must have succeeded or been skipped — skipped is how a job says
#            its app did not change. Failed is red; cancelled is red, because a
#            superseded, timed-out or lost job tested nothing; and a result this
#            check does not know is red, because the day GitHub adds one the
#            answer should be a run somebody reads.
#
#   wiring   a job never reached the summary at all. ci-ok must need every other
#            job in the workflow — a job left out runs, fails, and changes
#            nothing anybody reads — and must run `if: always()`. Without it a
#            failed need *skips* ci-ok, and a skipped check reads as passing;
#            `!cancelled()` skips it on a cancelled run, which is no better.
#
#   exit 0  green
#   exit 1  red, with every job that made it so named
#   exit 2  the check could not run — never a pass
#
# The workflow is read by a small parser rather than a YAML library, because the
# runner's system Python guarantees neither PyYAML nor anything else, and ci-ok
# runs before (and without) either app's setup. It reads what ci.yml's own style
# writes: two-space indentation, and ci-ok's `needs` one job per line — any other
# form is refused by name rather than misread.
#
# Tested by .github/scripts/test-ci-ok.sh (`make test-ci-ok`), which ci-ok runs
# before it renders a verdict. A summary check that has never once failed is
# indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

mode="${1:-}"
case "$mode" in
  verdict) ;;
  wiring) workflow="${2:-$ROOT/.github/workflows/ci.yml}" ;;
  *)
    echo "usage: check-ci-ok.sh verdict            (reads toJSON(needs) from NEEDS)" >&2
    echo "       check-ci-ok.sh wiring [ci.yml]" >&2
    exit 2
    ;;
esac

command -v python3 >/dev/null || { echo "check-ci-ok.sh needs python3, and there is none." >&2; exit 2; }

python3 - "$mode" "${workflow:-}" <<'PY'
import json
import os
import re
import sys

mode, workflow = sys.argv[1], sys.argv[2]
annotate = bool(os.environ.get("GITHUB_ACTIONS"))


def error(message):
    if annotate:
        print(f"::error title=ci-ok::{message}")


def verdict():
    raw = os.environ.get("NEEDS", "")
    if not raw.strip():
        print("No `needs` context in NEEDS — nothing to judge, so no verdict.", file=sys.stderr)
        return 2
    try:
        needs = json.loads(raw)
    except ValueError as exc:
        print(f"NEEDS is not JSON ({exc}) — no verdict.", file=sys.stderr)
        return 2
    if not isinstance(needs, dict) or not needs:
        print("NEEDS names no jobs — the check has lost its subject.", file=sys.stderr)
        return 2

    wrong = []
    for job, state in needs.items():
        result = state.get("result") if isinstance(state, dict) else None
        print(f"  {job}: {result}")
        if result not in ("success", "skipped"):
            wrong.append((job, result))

    if not wrong:
        print(f"ci-ok — {len(needs)} jobs, each succeeded or was skipped.")
        return 0
    print(file=sys.stderr)
    print("ci-ok is red. Every job below went wrong, and none of them tested this push:", file=sys.stderr)
    for job, result in wrong:
        print(f"  {job}: {result}", file=sys.stderr)
        error(f"{job} finished {result}, so this run is not green")
    return 1


KEY = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_-]*):(.*)$")


def value(text):
    """A scalar with its trailing comment, quotes and ${{ }} wrapper removed."""
    text = re.sub(r"\s+#.*$", "", text).strip().strip("'\"")
    wrapped = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", text)
    return wrapped.group(1) if wrapped else text


def significant(line):
    stripped = line.strip()
    return stripped and not stripped.startswith("#")


def indent(line):
    return len(line) - len(line.lstrip())


def jobs_of(lines):
    """{job id: [the lines of its body]}, in file order."""
    start = next((i for i, l in enumerate(lines) if re.match(r"^jobs:\s*(#.*)?$", l)), None)
    if start is None:
        return None
    block = []
    for line in lines[start + 1:]:
        if significant(line) and indent(line) == 0:
            break
        block.append(line)
    body = [l for l in block if significant(l)]
    if not body:
        return {}
    level = indent(body[0])
    jobs, current = {}, None
    for line in block:
        match = KEY.match(line)
        if significant(line) and indent(line) == level and match and not value(match.group(3)):
            current = match.group(2)
            jobs[current] = []
        elif current is not None:
            jobs[current].append(line)
    return jobs


def property_of(body, name):
    """(inline value, [list items]) of a job's top-level key, or None."""
    lines = [l for l in body if significant(l)]
    if not lines:
        return None
    level = indent(lines[0])
    for i, line in enumerate(lines):
        match = KEY.match(line)
        if not (match and indent(line) == level and match.group(2) == name):
            continue
        inline = value(match.group(3))
        items = []
        for item in lines[i + 1:]:
            if indent(item) <= level:
                break
            if item.strip().startswith("- "):
                items.append(value(item.strip()[2:]))
        return inline, items
    return None


def wiring():
    try:
        with open(workflow) as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        print(f"Cannot read the workflow ({exc}) — no verdict on its wiring.", file=sys.stderr)
        return 2
    jobs = jobs_of(lines)
    if not jobs:
        print(f"{workflow} has no jobs — the check has lost its subject.", file=sys.stderr)
        return 2
    if "ci-ok" not in jobs:
        print(f"{workflow} has no ci-ok job: nothing summarises the run, so nothing says it is green.", file=sys.stderr)
        error("the workflow has no ci-ok job")
        return 1

    problems = []

    needs = property_of(jobs["ci-ok"], "needs")
    inline, items = needs if needs is not None else ("", [])
    if inline:
        print(f"ci-ok's needs reads `{inline}`: write it one job per line, the only form this check reads.", file=sys.stderr)
        error("ci-ok's needs must be written one job per line")
        return 1
    named = set(items)
    others = [job for job in jobs if job != "ci-ok"]
    for job in others:
        if job not in named:
            problems.append(f"ci-ok does not need `{job}`, so it could fail and ci-ok would stay green")
    for job in sorted(named - set(others)):
        problems.append(f"ci-ok needs `{job}`, which is not a job in this workflow")

    condition = property_of(jobs["ci-ok"], "if")
    said = condition[0] if condition else None
    if said != "always()":
        now = f"`if: {said}`" if said else "no `if:`"
        problems.append(
            f"ci-ok runs on {now}, not `if: always()` — a failed or cancelled need would skip it, "
            "and a skipped check reads as passing"
        )

    if not problems:
        print(f"OK — ci-ok needs all {len(others)} other jobs in {os.path.basename(workflow)} and runs if: always().")
        return 0
    print(file=sys.stderr)
    print("ci-ok is not wired to judge the whole run:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
        error(problem)
    return 1


try:
    sys.exit(verdict() if mode == "verdict" else wiring())
except Exception as exc:  # a crash is a check that could not run, never a verdict
    print(f"check-ci-ok.sh could not run: {exc!r}", file=sys.stderr)
    sys.exit(2)
PY
