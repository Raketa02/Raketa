#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the kernel/engines purity gates.
#
#   bash scripts/test-purity-gates.sh          # or: make test-gates
#
# Three gates guard ADR-0015's purity rules, and no one mechanism covers all of
# it: the `.importlinter` contracts (module granularity), the AST walk in
# tests/unit/test_kernel_purity.py (what module granularity cannot see), and
# mypy strict scoped to the two packages in pyproject.toml. All three were added
# to a tree that already satisfied them — so on the day they landed, not one of
# them had ever been observed to fail, which is indistinguishable from not
# working. This drives each one against a deliberately impure tree.
#
# It writes probe modules into app/kernel/, app/engines/ and app/shared/, runs
# the real gates over them, and removes them on exit — including on failure or
# interrupt. Nothing else in the tree is touched, so it is safe on a dirty one.
# The probes are new files rather than edits to existing ones: a probe that
# perturbs a real module would need restoring, and a restore that half-runs is
# worse than a file that is simply deleted.
#
# Not part of `make check`, for the same reason `make test-hooks` and
# `make test-drift` are not: it shells out to the very tools `check` runs, and a
# gate suite belongs where a gate suite is looked at — CI, and after a change to
# a gate. The backend CI job runs it.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT" || exit 2

KERNEL_PROBE="$ROOT/app/kernel/_purity_probe.py"
ENGINE_PROBE="$ROOT/app/engines/_purity_probe.py"
OUTSIDE_PROBE="$ROOT/app/shared/_purity_probe.py"
AST_TEST="tests/unit/test_kernel_purity.py"

clean() { rm -f "$KERNEL_PROBE" "$ENGINE_PROBE" "$OUTSIDE_PROBE"; }
trap clean EXIT INT TERM
clean

for f in .importlinter pyproject.toml "$AST_TEST"; do
  [ -f "$ROOT/$f" ] || { echo "missing: $f" >&2; exit 2; }
done

pass=0
fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

probe() { # <path> <source>
  printf '%s' "$2" >"$1"
}

# The three gates, each as CI runs it.
imports() { poetry run lint-imports 2>&1; }
types()   { poetry run mypy app 2>&1; }
walk()    { poetry run pytest "$AST_TEST" -q --no-cov -p no:cacheprovider 2>&1; }

expect() { # <red|green> <gate> <name> [pattern...]
  local want="$1" gate="$2" name="$3" out status
  shift 3
  out=$("$gate")
  status=$?
  case "$want" in
    green) [ "$status" = 0 ] && ok "$name" || { bad "$name" "expected a pass, got exit $status"; printf '%s\n' "$out" | tail -12 | sed 's/^/        /'; return; } ;;
    red)   [ "$status" != 0 ] && ok "$name" || { bad "$name" "expected a failure, got exit 0"; return; } ;;
  esac
  local pattern
  for pattern in "$@"; do
    grep -qF "$pattern" <<<"$out" \
      && ok "  … and says so: $pattern" \
      || { bad "  … and says so: $pattern" "not in the output"; printf '%s\n' "$out" | tail -20 | sed 's/^/        /'; }
  done
}

# ---------------------------------------------------------------------------
echo
echo "the committed tree — every gate green, so a red below is the probe"

expect green imports "the import contracts hold"
expect green types   "mypy strict holds for the kernel and the engines"
expect green walk    "the source walk holds"

# ---------------------------------------------------------------------------
echo
echo ".importlinter — a forbidden import"

# The hole ADR-0022 records: app.shared was on neither contract, so this exact
# line typechecked, linted and shipped with CI fully green.
probe "$KERNEL_PROBE" 'from app.shared.clock import SystemClock

CLOCK = SystemClock()
'
expect red imports "the kernel reaching app.shared is refused" \
  "app.kernel is not allowed to import app.shared" \
  "app.kernel._purity_probe -> app.shared.clock"
clean

probe "$ENGINE_PROBE" 'from app.shared.ids import new_uuid

ID = new_uuid()
'
expect red imports "an engine reaching app.shared is refused" \
  "app.engines is not allowed to import app.shared"
clean

probe "$ENGINE_PROBE" 'import random
import secrets
import time
import uuid

_ = (random, secrets, time, uuid)
'
expect red imports "an engine taking ambient randomness or time is refused" \
  "app.engines is not allowed to import random" \
  "app.engines is not allowed to import secrets" \
  "app.engines is not allowed to import time" \
  "app.engines is not allowed to import uuid"
clean

# datetime is the one rule that differs between the two packages, so it is
# asserted in both directions. An engine receives an instant; the kernel's time
# module is the one place that builds one.
probe "$ENGINE_PROBE" 'from datetime import datetime

Instant = datetime
'
expect red imports "an engine importing datetime is refused" \
  "app.engines is not allowed to import datetime"
clean

probe "$KERNEL_PROBE" 'from datetime import datetime, timezone

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
'
expect green imports "the kernel importing datetime is allowed"
clean

# ---------------------------------------------------------------------------
echo
echo "the source walk — what module granularity cannot see"

# Both gates are pointed at the same probe on purpose. import-linter passing it
# is not a bug in import-linter; it is the reason the AST walk exists.
probe "$KERNEL_PROBE" 'from datetime import datetime, timezone


def stamp() -> datetime:
    return datetime.now(timezone.utc)
'
expect green imports "import-linter cannot see a clock read through a legal import"
expect red walk "the walk refuses datetime.now() in the kernel" \
  "app/kernel/_purity_probe.py" \
  "ambient clock read"
clean

probe "$ENGINE_PROBE" 'import time


def stamp() -> float:
    return time.time()
'
expect red walk "the walk refuses time.time() in the engines" \
  "app/engines/_purity_probe.py"
clean

probe "$ENGINE_PROBE" 'import httpx


def fetch(url: str) -> object:
    return httpx.get(url)
'
expect red walk "the walk names a third-party import" \
  "app/engines/_purity_probe.py" \
  "httpx"
clean

# ---------------------------------------------------------------------------
echo
echo "mypy strict — scoped to the two packages"

# The kind both pre-existing errors were: `float ** float` is Any in typeshed, so
# an unannotated square root leaks Any out of a function declared to return float.
probe "$KERNEL_PROBE" 'from typing import Any


def sigma(value: Any) -> float:
    return value**0.5
'
expect red types "an Any returned from the kernel is refused" \
  "app/kernel/_purity_probe.py" \
  "no-any-return"
clean

probe "$ENGINE_PROBE" 'def scale(value):
    return value * 2
'
expect red types "an untyped def in the engines is refused" \
  "app/engines/_purity_probe.py" \
  "no-untyped-def"
clean

probe "$ENGINE_PROBE" 'def scale(value: int) -> int:
    return value * 2  # type: ignore[no-any-return]
'
expect red types "a type: ignore with nothing to silence is refused" \
  "app/engines/_purity_probe.py" \
  "unused-ignore"
clean

# The override is scoped, and scoped means the rest of the tree is unchanged:
# the same untyped def outside the two packages is still accepted.
probe "$OUTSIDE_PROBE" 'def scale(value):
    return value * 2
'
expect green types "the same untyped def outside the two packages still passes"
clean

# ---------------------------------------------------------------------------
echo
echo "the tree is left as it was found"

expect green imports "the import contracts hold again"
expect green types   "mypy strict holds again"
expect green walk    "the source walk holds again"

# ---------------------------------------------------------------------------
echo
printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ] || exit 1
