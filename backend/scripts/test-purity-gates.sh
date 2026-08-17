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
PAIRING_PROBE="$ROOT/app/engines/pairing/_purity_probe.py"
MATCHFIT_PROBE="$ROOT/app/engines/matchfit/_purity_probe.py"
APPLICATION_PROBE="$ROOT/app/application/_purity_probe.py"
SHARED_DOMAIN_PROBE="$ROOT/app/shared/domain/_purity_probe.py"
MODULE_DOMAIN_PROBE="$ROOT/app/modules/users/domain/_purity_probe.py"
MODULE_APPLICATION_PROBE="$ROOT/app/modules/users/application/_purity_probe.py"
MODULE_INFRA_PROBE="$ROOT/app/modules/users/infrastructure/_purity_probe.py"
# A whole context rather than a file: the one claim the wildcard arms make that no
# probe inside an existing module can check. Fixed, script-owned, and removed with
# the rest — it is the only probe that is a directory, so it is the only `rm -rf`.
NEW_CONTEXT_DIR="$ROOT/app/modules/_purity_probe_context"
AST_TEST="tests/unit/test_kernel_purity.py"

clean() {
  rm -f "$KERNEL_PROBE" "$ENGINE_PROBE" "$OUTSIDE_PROBE" \
        "$PAIRING_PROBE" "$MATCHFIT_PROBE" \
        "$APPLICATION_PROBE" "$SHARED_DOMAIN_PROBE" \
        "$MODULE_DOMAIN_PROBE" "$MODULE_APPLICATION_PROBE" "$MODULE_INFRA_PROBE"
  rm -rf "$NEW_CONTEXT_DIR"
}
trap clean EXIT INT TERM
clean

for f in .importlinter pyproject.toml "$AST_TEST"; do
  [ -f "$ROOT/$f" ] || { echo "missing: $f" >&2; exit 2; }
done

# The modules the probes below import, and why their absence is fatal rather
# than a red assertion: `import-linter` builds a graph of what resolves, so an
# import of a module that no longer exists is not a broken contract — it is not
# an edge at all, and the run comes back 0 broken. A probe naming a deleted
# module therefore reports the fence as *holding* while proving nothing, which
# is the failure mode this whole suite exists to refuse. #75 deleted
# `app/shared/clock.py`, the kernel probe's original target, and this is the
# check that would have said so in one line instead of an assertion diff.
for f in app/shared/ids.py \
         app/engines/pairing/v1/__init__.py \
         app/engines/matchfit/v1/__init__.py \
         app/engines/forecast.py \
         app/core/config.py \
         app/core/exception_handlers.py \
         app/shared/domain/errors.py; do
  [ -f "$ROOT/$f" ] || { echo "probed module is gone, so its probe proves nothing: $f" >&2; exit 2; }
done

# Where the probes are *written* matters for the same reason, and for one that is
# sharper still. Two arms of the configuration contract are wildcards, and
# `import-linter` reports a wildcard matching nothing as KEPT — not as an error, the
# way it reports a literal module that does not exist. So a renamed package under
# `app/modules/` would leave the contract green, this suite's probes landing in a
# directory the fence no longer covers, and nothing anywhere saying so.
for d in app/application \
         app/shared/domain \
         app/modules/users/domain \
         app/modules/users/application \
         app/modules/users/infrastructure; do
  [ -f "$ROOT/$d/__init__.py" ] || { echo "a probe's home package is gone, so its arm proves nothing: $d" >&2; exit 2; }
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

# Patterns are matched against one line at a time, and `import-linter` wraps its
# report at 80 columns — so a pattern longer than that can never match, however
# correct it looks. It is a silent miss rather than an error: the gate went red for
# the right reason and the assertion about *why* fails beside it. Long module paths
# are where this bites, so assert the "… is not allowed to import" line and the
# "… -> target" chain line separately rather than as one long string.
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
# line typechecked, linted and shipped with CI fully green. It read
# `from app.shared.clock import SystemClock` until #75 retired that module, and
# the substitution is not cosmetic — see the preflight note above.
probe "$KERNEL_PROBE" 'from app.shared.ids import new_uuid

ID = new_uuid()
'
expect red imports "the kernel reaching app.shared is refused" \
  "app.kernel is not allowed to import app.shared" \
  "app.kernel._purity_probe -> app.shared.ids"
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
echo ".importlinter — the two matchmaking engines, fenced from each other"

# The failure this fence exists to stop: Match Fit reaching for the pairing engine
# instead of taking its output as an input value. An engine free to build its own
# forecast can score a match against a pairing nobody was shown (docs/adr/0026).
probe "$MATCHFIT_PROBE" 'from app.engines.pairing.v1 import PairingEngineV1

ENGINE = PairingEngineV1()
'
expect red imports "Match Fit reaching for the pairing engine is refused" \
  "app.engines.matchfit is not allowed to import app.engines.pairing" \
  "app.engines.matchfit._purity_probe -> app.engines.pairing.v1"
clean

# Asserted in both directions, because a one-way fence is a fence somebody walks
# round. The pairing engine must not learn that Match Fit exists either.
probe "$PAIRING_PROBE" 'from app.engines.matchfit.v1 import MatchFitEngineV1

ENGINE = MatchFitEngineV1()
'
expect red imports "the pairing engine reaching for Match Fit is refused" \
  "app.engines.pairing is not allowed to import app.engines.matchfit"
clean

# And the legitimate direction, which is the whole point of the fence being drawn
# where it is: the *output vocabulary* is shared, so Match Fit reads a forecast's
# types without being able to produce one.
probe "$MATCHFIT_PROBE" 'from app.engines.forecast import BalanceForecast, PairingAnalysis

READS = (BalanceForecast, PairingAnalysis)
'
expect green imports "Match Fit reading the pairing engine's output types is allowed"
clean

# ---------------------------------------------------------------------------
echo
echo ".importlinter — configuration fenced out of the business rules"

# The rule the contract states: the environment may select configuration defaults,
# but never behaviour a domain test could observe. A use case reading `APP_ENV` to
# pick a deadline is a rule that is true on a laptop and false in production, and the
# domain suite cannot see the difference — which is what makes it worth a fence
# rather than a review comment.
#
# Each of the contract's four source arms gets its **own** probe rather than one
# standing in for all four. Two of them are wildcards, and a wildcard matching
# nothing is reported KEPT (see the preflight above), so an arm can quietly stop
# covering anything while the run still says the fence held. One probe would prove
# one arm and imply three.
probe "$APPLICATION_PROBE" 'from app.core.config import get_settings

DEADLINE = get_settings().ACCESS_TOKEN_EXPIRE_SECONDS
'
expect red imports "the cross-cutting application layer reading settings is refused" \
  "app.application is not allowed to import app.core.config" \
  "app.application._purity_probe -> app.core.config"
clean

probe "$SHARED_DOMAIN_PROBE" 'from app.core.config import get_settings

DEADLINE = get_settings().ACCESS_TOKEN_EXPIRE_SECONDS
'
expect red imports "the shared domain layer reading settings is refused" \
  "app.shared.domain is not allowed to import app.core.config" \
  "app.shared.domain._purity_probe -> app.core.config"
clean

# The two wildcard arms. `users` stands for every context under app/modules/ — and
# for the four that are named in the glossary but not yet modelled, which is the
# reason the arms are wildcards at all.
probe "$MODULE_DOMAIN_PROBE" 'from app.core.config import get_settings

MAX_ATTEMPTS = 3 if get_settings().DEBUG else 10
'
expect red imports "a module's domain layer reading settings is refused" \
  "app.modules.users.domain is not allowed to import app.core.config" \
  "app.modules.users.domain._purity_probe -> app.core.config"
clean

probe "$MODULE_APPLICATION_PROBE" 'from app.core.config import Environment, get_settings

SKIP_CHECK = get_settings().APP_ENV is Environment.LOCAL
'
expect red imports "a module's application layer reading settings is refused" \
  "app.modules.users.application is not allowed to import app.core.config" \
  "app.modules.users.application._purity_probe -> app.core.config"
clean

# The two ways round the fence that are the same rule broken by a different import.
# Both are forbidden beside the settings module for the reason ambience is forbidden
# to the engines: naming only the obvious route leaves the others open.
probe "$MODULE_APPLICATION_PROBE" 'from pydantic_settings import BaseSettings


class LocalSettings(BaseSettings):
    DEADLINE_SECONDS: int = 30
'
expect red imports "declaring a second settings class in a business layer is refused" \
  "app.modules.users.application is not allowed to import pydantic_settings"
clean

probe "$MODULE_DOMAIN_PROBE" 'import os

DEADLINE_SECONDS = int(os.environ.get("DEADLINE_SECONDS", "30"))
'
expect red imports "reading the process environment from a domain layer is refused" \
  "app.modules.users.domain is not allowed to import os"
clean

# And the legitimate direction, which is what the fence is *for*: configuration is
# read at the composition boundary and handed inward. An adapter is on the outside of
# it, so the same import that is refused four times above is allowed here.
probe "$MODULE_INFRA_PROBE" 'from app.core.config import get_settings

SECRET = get_settings().JWT_SECRET_KEY
'
expect green imports "an infrastructure adapter reading settings is allowed"
clean

# The wildcard arms' whole reason for existing, and the one claim about them that a
# probe inside `users` cannot make: a context that does not exist yet is fenced on
# the day somebody creates it, not on the day somebody remembers to come back to
# `.importlinter`. Clubs, Courts, Bookings and Matches are all named in the glossary
# and none is modelled, so this is the case that will actually be exercised.
mkdir -p "$NEW_CONTEXT_DIR/domain"
: >"$NEW_CONTEXT_DIR/__init__.py"
: >"$NEW_CONTEXT_DIR/domain/__init__.py"
probe "$NEW_CONTEXT_DIR/domain/rules.py" 'from app.core.config import get_settings

CANCELLATION_DEADLINE_HOURS = 1 if get_settings().DEBUG else 24
'
expect red imports "a context created tomorrow is fenced without touching .importlinter" \
  "app.modules._purity_probe_context.domain is not allowed to import" \
  "app.modules._purity_probe_context.domain.rules -> app.core.config"
clean

# ---------------------------------------------------------------------------
echo
echo ".importlinter — the framework and the ORM fenced out of the domain layers"

# backend/CLAUDE.md forbids a domain layer importing FastAPI, SQLAlchemy, Pydantic or
# an external SDK. Nothing enforced it, and it was already broken: every module's
# `domain/errors.py` took its error base classes from `app.core.exception_handlers`,
# which imports all three of fastapi, starlette and pydantic (#101). The taxonomy now
# lives in `app/shared/domain/errors.py` and imports nothing but stdlib.
#
# The violation was **only ever indirect** — no domain module has imported a framework
# directly, before or since — so this contract sets `allow_indirect_imports = false`
# and the indirect probe below is the one that matters. A direct probe alone would
# still go red if somebody flipped that flag, and the fence would be decoration.
probe "$MODULE_DOMAIN_PROBE" 'from app.core.exception_handlers import ErrorResponse

SCHEMA = ErrorResponse
'
expect red imports "a domain layer reaching a framework *through another module* is refused" \
  "app.modules.users.domain is not allowed to import fastapi" \
  "app.modules.users.domain._purity_probe -> app.core.exception_handlers" \
  "app.core.exception_handlers -> fastapi"
clean

probe "$MODULE_DOMAIN_PROBE" 'from pydantic import BaseModel


class Rule(BaseModel):
    limit: int
'
expect red imports "a domain layer importing pydantic directly is refused" \
  "app.modules.users.domain is not allowed to import pydantic"
clean

# The fourth forbidden package, and the one that is not a web framework at all. It is
# fenced because CLAUDE.md forbids all four to a domain layer in one breath — this is
# the ORM model somebody reaches for while writing an aggregate, which is how
# persistence gets into a domain object without anybody deciding it should.
probe "$MODULE_DOMAIN_PROBE" 'from sqlalchemy import Column, Integer

LIMIT = Column("limit", Integer)
'
expect red imports "a domain layer importing the ORM is refused" \
  "app.modules.users.domain is not allowed to import sqlalchemy"
clean

# The second arm, and the one the error taxonomy itself now sits in — so the fence has
# to hold there or the move has simply relocated the problem.
probe "$SHARED_DOMAIN_PROBE" 'from fastapi import HTTPException

Raised = HTTPException
'
expect red imports "the shared domain layer importing fastapi is refused" \
  "app.shared.domain is not allowed to import fastapi" \
  "app.shared.domain._purity_probe -> fastapi"
clean

# Same wildcard reasoning as the configuration contract: a context nobody has written
# yet is fenced on the day it is created. Starlette, because a contract's third
# forbidden module is exactly the one nobody probes.
mkdir -p "$NEW_CONTEXT_DIR/domain"
: >"$NEW_CONTEXT_DIR/__init__.py"
: >"$NEW_CONTEXT_DIR/domain/__init__.py"
probe "$NEW_CONTEXT_DIR/domain/rules.py" 'from starlette.responses import JSONResponse

Response = JSONResponse
'
expect red imports "a context created tomorrow is fenced from the framework too" \
  "app.modules._purity_probe_context.domain is not allowed to import" \
  "app.modules._purity_probe_context.domain.rules -> starlette"
clean

# And the legitimate direction. The fence is around the domain layers, not the app: an
# adapter and a route handler are where a framework belongs, and the transport half of
# the error envelope still imports all three.
probe "$MODULE_INFRA_PROBE" 'from fastapi import status
from pydantic import BaseModel


class Payload(BaseModel):
    code: int = status.HTTP_200_OK
'
expect green imports "an infrastructure adapter importing the framework is allowed"
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
