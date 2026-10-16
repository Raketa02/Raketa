#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the contract drift check.
#
#   bash .github/scripts/test-contract-drift.sh          # every client (make test-drift)
#   bash .github/scripts/test-contract-drift.sh frontend_club   # the ones named
#
# Drives check-contract-drift.sh against a deliberately-stale tree and asserts
# it goes red, then against the committed tree and asserts it goes green. The
# point of a drift check is that it is watched, and a check that has never once
# failed is indistinguishable from one that cannot — the same reason
# .claude/hooks/test-hooks.sh exists for the guardrail hooks.
#
# The stale case is built the way the real one arrives: the CONTRACT is changed
# and the client is left alone. The check regenerates and the working tree stops
# matching HEAD, which is exactly the comparison CI makes on a pull request that
# commits a contract change without its client types.
#
# **A client is an app whose package.json declares `gen:api`**, and there are
# three: the player app, the club website and the public site, each generating
# from its own document (docs/adr/0187 §5). Every one is driven — its document
# is what gets perturbed, so a client that read another's document would stay
# green here. Naming apps drives only those: CI runs this in each client's own
# job, where no other client is installed. The wiring assertions at the end
# always cover every client, because a client CI never checks is the failure
# they exist for.
#
# It perturbs each document and generated file in place and restores the
# original bytes from a temporary copy on exit — including on failure or
# interrupt — so it is safe to run on a dirty tree and preserves whatever was
# there.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-contract-drift.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"

source "$ROOT/.github/scripts/paths-filter.sh"
source "$ROOT/.github/scripts/contract-clients.sh"

pass=0
fail=0

ok()   { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad()  { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

expect_exit() { # <want> <name> <command...>
  local want="$1" name="$2" got
  shift 2
  "$@" >/dev/null 2>&1
  got=$?
  [ "$got" = "$want" ] && ok "$name" || bad "$name" "want exit $want, got $got"
}

# A line of the workflow that is not a comment contains <needle>. One awk, not
# `grep -v '#' | grep -q`: under pipefail the first grep can die of SIGPIPE when
# the second quits early, and a found line reads as missing.
workflow_runs() { # <needle>
  awk -v needle="$1" '!/^[[:space:]]*#/ && index($0, needle) { found = 1 } END { exit !found }' "$CI_YML"
}

# The clients, and each one's document and output, come from
# contract-clients.sh — the same answers the check reads, not a copy of them.
CLIENTS=()
while read -r client; do
  [ -n "$client" ] && CLIENTS+=("$client")
done <<<"$(contract_clients)"
[ ${#CLIENTS[@]} -gt 0 ] || { echo "no app declares gen:api — nothing to test" >&2; exit 2; }

if [ $# -gt 0 ]; then
  SELECTED=("$@")
else
  SELECTED=("${CLIENTS[@]}")
fi
for app in "${SELECTED[@]}"; do
  case " ${CLIENTS[*]} " in
    *" $app "*) ;;
    *) echo "not a client: $app (the clients are: ${CLIENTS[*]})" >&2; exit 2 ;;
  esac
done

[ -f "$CHECK" ] && [ -f "$CI_YML" ] || { echo "missing: $CHECK or $CI_YML" >&2; exit 2; }

TMP=$(mktemp -d)
ORIGINALS=()  # every file a case perturbs …
COPIES=()     # … and its bytes before the first case, at the same index
back_up() { # <path>
  local copy="$TMP/${#ORIGINALS[@]}"
  cp "$1" "$copy"
  ORIGINALS+=("$1")
  COPIES+=("$copy")
}
PROBES=()     # files a case creates, removed on every exit
restore() {
  local i=0
  while [ "$i" -lt ${#ORIGINALS[@]} ]; do
    cp "${COPIES[$i]}" "${ORIGINALS[$i]}"
    i=$((i + 1))
  done
  if [ ${#PROBES[@]} -gt 0 ]; then
    rm -f "${PROBES[@]}"
  fi
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# Add a schema the client has never generated. openapi-typescript emits every
# entry under components.schemas, referenced or not, so this is the smallest
# contract change that is guaranteed to move the generated output — and it
# leaves every existing path and schema untouched.
add_probe_schema() { # <document>
  python3 - "$1" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    doc = json.load(fh)
doc["components"]["schemas"]["DriftProbe"] = {
    "type": "object",
    "properties": {"probe": {"type": "string", "title": "Probe"}},
    "title": "DriftProbe",
}
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}

# ---------------------------------------------------------------------------
echo
echo "check-contract-drift.sh — what it accepts"

expect_exit 2 "an app the check does not know is a usage error" \
  bash "$CHECK" frontend_nonesuch
expect_exit 2 "an app with no gen:api script is a usage error" \
  bash "$CHECK" backend
expect_exit 2 "a path is not an app" \
  bash "$CHECK" ../raketa/frontend_player
expect_exit 2 "no app at all is a usage error" \
  bash "$CHECK"

for app in "${SELECTED[@]}"; do
  read -r doc generated <<<"$(gen_api_of "$app")"
  if [ -z "$doc" ] || [ -z "$generated" ] || [ ! -f "$ROOT/$doc" ] || [ ! -f "$ROOT/$generated" ]; then
    bad "$app: its gen:api names a document and an output that exist" "read '$doc' → '$generated'"
    continue
  fi
  DOC="$ROOT/$doc"
  GEN="$ROOT/$generated"
  NEIGHBOUR="$(dirname "$GEN")/drift-probe.md"
  back_up "$DOC"
  back_up "$GEN"
  PROBES+=("$NEIGHBOUR")

  # -------------------------------------------------------------------------
  echo
  echo "$app — the committed tree"

  expect_exit 0 "$app: a contract and a client that agree pass" \
    bash "$CHECK" "$app"
  restore

  # The player app's src/generated/ holds a hand-maintained README.md beside the
  # generator's output. Scoping the diff to the directory rather than to the
  # file `gen:api` writes reported an edit to that README as contract drift — a
  # false failure, and the kind that teaches people to ignore the check. Found
  # by this suite, kept here, and driven for every client with a file of its
  # own beside the output.
  printf '<!-- drift probe -->\n' >"$NEIGHBOUR"
  expect_exit 0 "$app: a file beside the generated one is not drift" \
    bash "$CHECK" "$app"
  restore

  # -------------------------------------------------------------------------
  echo
  echo "$app — a contract change with a stale client"

  add_probe_schema "$DOC"
  out=$(bash "$CHECK" "$app" 2>&1)
  got=$?

  [ "$got" = 1 ] && ok "$app: a contract change without a regenerated client fails" \
    || bad "$app: a contract change without a regenerated client fails" "want exit 1, got $got"

  grep -qF "CONTRACT DRIFT — $app" <<<"$out" && ok "$app: the failure names the app" \
    || bad "$app: the failure names the app"

  grep -qF "$doc" <<<"$out" && ok "$app: the failure names its own contract document" \
    || bad "$app: the failure names its own contract document" "never mentioned $doc"

  grep -q 'make gen-api' <<<"$out" && ok "$app: the failure prints the command that fixes it" \
    || bad "$app: the failure prints the command that fixes it"

  grep -q 'DriftProbe' <<<"$out" && ok "$app: the failure prints the diff it found" \
    || bad "$app: the failure prints the diff it found"

  restore

  # The check must not leave the stale state behind as a pass on a second run.
  expect_exit 0 "$app: the restored tree passes again" \
    bash "$CHECK" "$app"
  restore

  [ "$app" = frontend_player ] || continue

  # -------------------------------------------------------------------------
  # A shape the client renders. **A shape is the API contract**: adding a field is
  # an API release, because the client renders every field it is handed. The probe
  # needs one schema the player document publishes and the player's mappers read;
  # the blocked-players list is that schema, since blockMappers.ts reads it.
  # -------------------------------------------------------------------------
  echo
  echo "$app — a reshaped rendered shape"

  published=$(python3 - "$DOC" <<'COUNT'
import json, sys
schemas = json.load(open(sys.argv[1]))["components"]["schemas"]
print("yes" if "BlockedPlayerSchema" in schemas and schemas["BlockedPlayerSchema"].get("properties") else "no")
COUNT
)

  [ "$published" = yes ] \
    && ok "the contract publishes the probe's rendered shape" \
    || bad "the contract publishes the probe's rendered shape" \
           "BlockedPlayerSchema is missing — the drift probe below would prove nothing"

  # Reshape it the way a real release does: a field added to a shape the client
  # already renders. Nothing else in the document moves.
  python3 - "$DOC" <<'RESHAPE'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    doc = json.load(fh)
shape = doc["components"]["schemas"]["BlockedPlayerSchema"]
shape["properties"]["probe_slots"] = {"type": "integer", "title": "Probe Slots"}
shape.setdefault("required", []).append("probe_slots")
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
RESHAPE

  out=$(bash "$CHECK" "$app" 2>&1)
  got=$?

  [ "$got" = 1 ] && ok "a reshaped rendered shape without a regenerated client fails" \
    || bad "a reshaped rendered shape without a regenerated client fails" "want exit 1, got $got"

  grep -q 'probe_slots' <<<"$out" && ok "the failure prints the reshaped shape" \
    || bad "the failure prints the reshaped shape"

  restore

  expect_exit 0 "the restored tree passes again after the evidence probe" \
    bash "$CHECK" "$app"
  restore
done

# ---------------------------------------------------------------------------
# The check firing is only half of it. It has to be REACHED — a drift step in a
# job that a backend-only pull request never runs is dormant in precisely the
# case it exists to catch. Asserted for every client, whichever were driven
# above: a client added without a lane is exactly the gap this is for.
# ---------------------------------------------------------------------------
echo
echo "ci.yml — every client is wired"

for app in "${CLIENTS[@]}"; do
  read -r doc generated <<<"$(gen_api_of "$app")"
  # ci.yml's filter and job names are the app's without its prefix:
  # frontend_club → club, club-static, club_ready.
  lane=${app#frontend_}

  filter_has "$CI_YML" "$lane" "$doc" \
    && ok "$app: the $lane filter watches $doc" \
    || bad "$app: the $lane filter watches $doc" \
           "a backend-only pull request would not run the $lane jobs"

  filter_has "$CI_YML" "$lane" "$app/**" \
    && ok "$app: the $lane filter watches the app" \
    || bad "$app: the $lane filter watches the app"

  workflow_runs "check-contract-drift.sh $app" \
    && ok "$app: ci.yml runs the check" \
    || bad "$app: ci.yml runs the check" "no step runs check-contract-drift.sh $app"

  workflow_runs "test-contract-drift.sh $app" \
    && ok "$app: ci.yml runs this suite for it" \
    || bad "$app: ci.yml runs this suite for it" "no step runs test-contract-drift.sh $app"

  # The drift step lives inside the jobs that already skip themselves until a
  # lockfile exists, not in a second job that would install the app itself.
  workflow_runs "needs.changes.outputs.${lane}_ready == 'true'" \
    && ok "$app: its jobs are gated on being bootstrapped" \
    || bad "$app: its jobs are gated on being bootstrapped"
done

# ---------------------------------------------------------------------------
echo
printf '\n  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" = 0 ]
