#!/bin/bash
# ---------------------------------------------------------------------------
# Run a command and record the runner's peak memory while it ran.
#
#   bash .github/scripts/memory-peak.sh <label> <command> [args...]
#
# ADR-0181 §7: the runner is 2 vCPU / 8 GB, and worker counts are sized from
# that — measured, not assumed. Two Jest workers per shard is a claim about this
# runner, and the way it fails is not a red test: a starved runner loses contact
# with GitHub and the job dies with every assertion passing. So each run writes
# the number down, as an annotation on the run's summary page where somebody
# will see it, rather than in a log nobody reads.
#
# It samples /proc/meminfo once a second: peak used is MemTotal less the lowest
# MemAvailable seen, and swap is reported beside it, since a runner that is
# swapping is already starving. Off Linux there is no /proc/meminfo, and the
# command simply runs.
#
# The command's exit status is this script's exit status, always. A wrapper on
# a gate's path that swallowed a failure would turn a red test green.
# ---------------------------------------------------------------------------
set -uo pipefail

[ $# -ge 2 ] || { echo "usage: memory-peak.sh <label> <command> [args...]" >&2; exit 2; }
label="$1"
shift

if [ ! -r /proc/meminfo ]; then
  "$@"
  exit $?
fi

samples=$(mktemp)
(
  while :; do
    awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ { v[$1] = $2 }
         END { print v["MemTotal:"], v["MemAvailable:"], v["SwapTotal:"] - v["SwapFree:"] }' /proc/meminfo
    sleep 1
  done
) >"$samples" &
sampler=$!

"$@"
status=$?

kill "$sampler" 2>/dev/null
wait "$sampler" 2>/dev/null

report=$(awk '
  NF == 3 {
    total = $1
    if (low == "" || $2 < low) low = $2
    if ($3 > swap) swap = $3
  }
  END {
    if (total == "") exit 1
    printf "peak %d MB used of %d MB (lowest available %d MB), swap peak %d MB\n",
      (total - low) / 1024, total / 1024, low / 1024, swap / 1024
  }' "$samples")
rm -f "$samples"

if [ -n "$report" ]; then
  echo "memory — $label: $report"
  [ -n "${GITHUB_ACTIONS:-}" ] && echo "::notice title=Memory — $label::$report"
  [ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "- **Memory — $label:** $report" >>"$GITHUB_STEP_SUMMARY"
fi

exit "$status"
