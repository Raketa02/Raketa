#!/bin/bash
# ---------------------------------------------------------------------------
# The ECS task definition can start a container.
#
#   bash .github/scripts/check-taskdef-boots.sh
#
# backend/deploy/ecs/taskdef.json supplies a list of environment variables and
# secrets to a container running APP_ENV=production. app/core/config.py refuses
# to start on configuration that is dangerous rather than merely wrong. Nothing
# compared the two, so the two disagreed: the committed task definition supplied
# no REDIS_URL, no PHOTO_STORAGE_SECRET_KEY and no ALLOW_ORIGINS, and a deploy of
# it would have registered a revision whose tasks died on startup (#341).
#
#   exit 0  every container definition in the file boots
#   exit 1  one does not — the report names the variable
#   exit 2  the check could not run
#
# **It executes the authority rather than restating it.** There is no list of
# required variables in this script or in the module behind it: the check hands
# `Settings` exactly what the task definition supplies and lets the refusals
# speak. That is the entire point. A list here would be a fourth copy of a fact
# already written in config.py, in docs/environments.md and in the task
# definition — and #341 is what happens when three copies disagree, which they
# did for eleven days, silently, because only `local` runs and nothing exercises
# a deployment artifact.
#
# **What it does not prove.** A `secrets` entry names a variable whose value
# lives in Secrets Manager; the check stands a placeholder in for it and asserts
# presence. This says the task definition supplies everything the application
# demands. It cannot say the values behind those ARNs are right, and it creates,
# reads and provisions nothing in AWS.
#
# Tested by .github/scripts/test-taskdef-boots.sh (`make test-taskdef`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

TASKDEF="backend/deploy/ecs/taskdef.json"
[ -f "$ROOT/$TASKDEF" ] || { echo "Cannot find $TASKDEF from $ROOT." >&2; exit 2; }

cd "$ROOT/backend" || exit 2

echo
echo "Booting $TASKDEF through app/core/config.py:"

# No settings are supplied here, deliberately — unlike every other check in this
# family, which pins the environment it needs. The whole question is what the
# task definition alone is enough for, so anything this line added would be a
# variable the file does not have to supply. The module scrubs the inherited
# environment for the same reason.
poetry run python -m scripts.taskdef_boot
status=$?

if [ "$status" = 0 ]; then
  exit 0
fi

if [ "$status" = 2 ]; then
  # The module ran and refused: it printed which part of the task definition it
  # could not read. Repeating a guess about poetry over the top of a specific
  # message would send the reader to the wrong fix.
  echo >&2
  echo "The task definition could not be read — see the message above." >&2
  exit 2
fi

if [ "$status" != 1 ]; then
  echo >&2
  echo "Could not run the task-definition boot check (exit $status)." >&2
  echo "It needs the backend installed — 'poetry install' in backend/." >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# It cannot boot. Say what to do about it — a failure that does not tell you how
# to fix it is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Task definition cannot boot::backend/deploy/ecs/taskdef.json does not supply everything app/core/config.py demands. See the job log for the variable."
fi

cat >&2 <<EOF
  Fix — one of two edits, and the report above says which:

    * The task definition is missing a variable. Add it to $TASKDEF:
      to 'secrets' if it carries a credential, following the templated
      shape of the entries already there — <AWS_ACCOUNT_ID> and
      <SECRET_SUFFIX> are substituted at deploy time, and no real ARN
      or secret belongs in this repository. To 'environment' if it does
      not, with its value committed.

    * A refusal in backend/app/core/config.py is new, and the deployment
      artifacts have not caught up. Then this is the check working: the
      same commit that adds a refusal supplies the variable here, names
      it in the checklist in docs/environments.md, and adds it to the
      Secrets Manager payload in backend/docs/deployment/aws-ecs.md.

────────────────────────────────────────────────────────────────────────────
EOF

exit 1
