#!/bin/bash
# ---------------------------------------------------------------------------
# The API contract's clients, read from the clients themselves. Sourced:
#
#   source "$ROOT/.github/scripts/contract-clients.sh"
#   contract_clients                      # one app per line
#   read -r doc out <<<"$(gen_api_of frontend_club)"
#     # → backend/openapi.club.json frontend_club/src/generated/schema.d.ts
#
# or run, to print the clients — which is how the Makefile's gen-api asks:
#
#   bash .github/scripts/contract-clients.sh
#
# **A client is an app whose package.json declares a `gen:api` script**, and the
# document it generates from and the file it writes are that script's own
# arguments (docs/adr/0187 §5). Every gate that needs either answer asks here,
# so there is exactly one: check-contract-drift.sh (which app it accepts, which
# document and which file it diffs), its still-fires suite (which clients it
# drives, and asserts CI wires), check-contract-freshness.sh (which client to
# tell to regenerate) and `make gen-api` (which clients it regenerates). Each
# used to carry its own copy, and a copy is how a disagreement starts.
#
# Python rather than node to read package.json: the backend's jobs, where the
# freshness check runs, guarantee python3 and nothing else — the reason
# check-ci-ok.sh gives.
# ---------------------------------------------------------------------------

CONTRACT_CLIENTS_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

contract_clients() {
  python3 - "$CONTRACT_CLIENTS_ROOT" <<'PY'
import json, pathlib, sys
for manifest in sorted(pathlib.Path(sys.argv[1]).glob("*/package.json")):
    try:
        scripts = json.loads(manifest.read_text()).get("scripts") or {}
    except (OSError, ValueError, AttributeError):
        continue
    if "gen:api" in scripts:
        print(manifest.parent.name)
PY
}

# "<document> <output>", both relative to the repository root, read out of the
# app's `openapi-typescript <document> -o <output>`. Nothing at all when the
# script is missing or has another shape — a caller refuses rather than guesses.
gen_api_of() { # <app>
  python3 - "$CONTRACT_CLIENTS_ROOT" "$1" <<'PY'
import json, pathlib, sys
root, app = pathlib.Path(sys.argv[1]), sys.argv[2]
try:
    words = json.loads((root / app / "package.json").read_text())["scripts"]["gen:api"].split()
except (OSError, ValueError, KeyError, TypeError, AttributeError):
    sys.exit(0)
document = words[1] if len(words) > 1 and not words[1].startswith("-") else ""
output = words[words.index("-o") + 1] if "-o" in words[:-1] else ""
if document and output:
    # The script runs inside the app, so `../backend/…` is the root's `backend/…`.
    document = document[3:] if document.startswith("../") else f"{app}/{document}"
    print(f"{document} {app}/{output}")
PY
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  contract_clients
fi
