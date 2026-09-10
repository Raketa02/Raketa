#!/bin/bash
# ---------------------------------------------------------------------------
# The ECS task definition agrees with the application it runs.
#
#   bash .github/scripts/check-taskdef.sh
#
# Two questions, both about the same disagreement — a deployment artifact that
# only `local` ever exercises, drifting away from the application it describes.
#
# **Would the container start?** backend/deploy/ecs/taskdef.json supplies
# environment variables and secrets to a container running APP_ENV=production,
# and app/core/config.py refuses to start on configuration that is dangerous
# rather than merely wrong. Nothing compared the two, so the two disagreed: the
# committed file supplied no REDIS_URL, no PHOTO_STORAGE_SECRET_KEY and no
# ALLOW_ORIGINS, and a deploy of it would have registered a revision whose tasks
# died on startup (#341).
#
# **Would the container be killed mid-shutdown?** `stopTimeout` was unset, which
# is not the same as unbounded — Fargate supplies 30, exactly gunicorn's
# --graceful-timeout, so the agent's SIGKILL landed on the same second the
# master would have force-killed its own stragglers (#345). Nothing related the
# two numbers, and they live in different files.
#
#   exit 0  every container definition starts, and outlives its own drain
#   exit 1  one does not — the report names the variable or the number
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
# Tested by .github/scripts/test-taskdef.sh (`make test-taskdef`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

TASKDEF="backend/deploy/ecs/taskdef.json"
[ -f "$ROOT/$TASKDEF" ] || { echo "Cannot find $TASKDEF from $ROOT." >&2; exit 2; }

cd "$ROOT/backend" || exit 2

echo
echo "Checking $TASKDEF against the application it runs:"

# No settings are supplied here, deliberately — unlike every other check in this
# family, which pins the environment it needs. The whole question is what the
# task definition alone is enough for, so anything this line added would be a
# variable the file does not have to supply. The module scrubs the inherited
# environment for the same reason.
poetry run python -m scripts.taskdef
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
  echo "Could not run the task-definition check (exit $status)." >&2
  echo "It needs the backend installed — 'poetry install' in backend/." >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# They disagree. Say what to do about it — a failure that does not tell you how
# to fix it is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  # One annotation for both rules. GitHub renders this above the diff, and a
  # title naming only the boot half would send a reader chasing a variable on a
  # run that failed over a timeout.
  echo "::error title=Task definition disagrees with the application::backend/deploy/ecs/taskdef.json does not match what backend/ actually runs — either a variable app/core/config.py demands and it does not supply, or a stopTimeout that does not outlive docker/api/startup.prod.sh's --graceful-timeout. See the job log."
fi

cat >&2 <<EOF
  The report above says which edit fixes it. Whichever it is, the two files
  move together: $TASKDEF is the deployment artifact and
  backend/app/core/config.py and backend/docker/api/startup.prod.sh are the
  application it has to agree with. No real ARN, credential or secret belongs
  in this repository — <AWS_ACCOUNT_ID> and <SECRET_SUFFIX> are substituted at
  deploy time.

  If a refusal or a timeout in the application is what changed, this is the
  check working: the same commit updates the artifact, the checklist in
  docs/environments.md, and the Secrets Manager payload in
  backend/docs/deployment/aws-ecs.md.

────────────────────────────────────────────────────────────────────────────
EOF

exit 1
