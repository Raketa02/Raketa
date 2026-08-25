#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the module bans in eslint.config.mjs.
#
#   bash scripts/test-import-boundaries.sh      # or: pnpm test:boundaries
#
# Four modules may be imported from exactly one place, or from nowhere at all:
#
#   expo-secure-store                            → src/shared/lib/auth
#   @react-native-async-storage/async-storage    → nowhere; it is unencrypted
#   expo-location                                → src/shared/lib/platform
#   expo-image-picker                            → src/shared/lib/platform
#
# Each ban was added to a tree that already satisfied it, so not one of them has
# ever been seen to fail — and a rule that has never fired is indistinguishable
# from one that cannot. A renamed directory, a `files` glob that stops matching,
# a rewritten `no-restricted-imports` block that drops an entry: all three are
# silent, and everybody has long since stopped watching. This drives the real
# linter against code that breaks each rule and asserts it goes red, then
# against the one place the import is legitimate and asserts it goes green.
#
# The same argument .claude/hooks/test-hooks.sh makes for the guardrail hooks
# and .github/scripts/test-contract-drift.sh makes for the contract check.
#
# Both halves matter. A rule that fires in its owning module too is a rule
# somebody switches off, and a linter an agent learns to read past is worse than
# no linter.
#
# ESLint is fed the violation on **stdin** under a filename it never opens, so
# no fixture file exists on disk for someone to find and helpfully "fix", and a
# failed run leaves the tree exactly as it found it.
# ---------------------------------------------------------------------------
set -uo pipefail

APP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ESLINT="$APP/node_modules/.bin/eslint"
CONFIG="$APP/eslint.config.mjs"

for f in "$ESLINT" "$CONFIG"; do
  [ -e "$f" ] || { echo "missing: $f — run pnpm install first" >&2; exit 2; }
done

cd "$APP" || exit 2

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() {
  fail=$((fail + 1))
  printf '  FAIL  %s\n' "$1"
  if [ $# -gt 1 ]; then printf '        %s\n' "$2"; fi
}

# Lint one import of <module>, as though it were written in the file at <path>.
# Prints the linter's output; exits non-zero when the ban fired.
lint_import() { # <module> <path>
  printf "import * as Native from '%s';\n\nexport const used = Native;\n" "$1" \
    | "$ESLINT" --stdin --stdin-filename "$2" 2>&1
}

expect_blocked() { # <module> <path> <substring the message must name>
  local module="$1" path="$2" needle="$3" out status
  out=$(lint_import "$module" "$path")
  status=$?

  if [ "$status" = 0 ]; then
    bad "$module is blocked in $path" "the linter accepted it"
  elif ! printf '%s' "$out" | grep -q -- "$needle"; then
    # A ban that fires without saying where to go instead teaches an agent to
    # delete the import and give up on the capability.
    bad "$module is blocked in $path" "the message never names '$needle'"
  else
    ok "$module is blocked in $path"
  fi
}

expect_allowed() { # <module> <path>
  local module="$1" path="$2" out status
  out=$(lint_import "$module" "$path")
  status=$?

  if [ "$status" = 0 ]; then
    ok "$module is allowed in $path"
  else
    bad "$module is allowed in $path" "$(printf '%s' "$out" | tail -n 3)"
  fi
}

# The places a ban would actually be broken: a feature reaching for the device
# directly, a route file doing the same, and a test — which could not drive a
# native module even if the linter let it through, because there is no JS
# implementation underneath one.
FEATURE='src/features/onboarding/hooks/usePlaceholder.ts'
SCREEN='src/app/(onboarding)/placeholder.tsx'
TEST='src/features/onboarding/hooks/usePlaceholder.test.ts'
SUPPORT='src/test-support/placeholder.ts'

# The three modules that are exempt from *a* ban, and are the interesting cases
# precisely because of it. An exemption is one rule wide, and a config that
# re-lists its bans by hand instead of subtracting the one it means loses every
# ban added afterwards — silently, and only here. That is not hypothetical: both
# native bans below were missing from the auth and observability blocks when this
# script probed only features, screens and tests, and it passed 17 of 17.
AUTH='src/shared/lib/auth/placeholder.ts'
OBSERVABILITY='src/shared/lib/observability/placeholder.ts'

# The ports themselves. Each owns exactly one native module; the other is as
# banned here as it is in a feature.
LOCATION_PORT='src/shared/lib/platform/location.ts'
PICKING_PORT='src/shared/lib/platform/imagePicking.ts'
OTHER_PLATFORM_FILE='src/shared/lib/platform/appState.ts'

echo "the keychain — expo-secure-store belongs to src/shared/lib/auth"
expect_blocked expo-secure-store "$FEATURE" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$SCREEN" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$TEST" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$LOCATION_PORT" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$OBSERVABILITY" 'src/shared/lib/auth'
expect_allowed expo-secure-store "$AUTH"

echo
echo "unencrypted storage — @react-native-async-storage/async-storage belongs nowhere"
expect_blocked @react-native-async-storage/async-storage "$FEATURE" 'AsyncStorage'
expect_blocked @react-native-async-storage/async-storage "$TEST" 'AsyncStorage'
# Not even the module that owns credentials, which is the only place anyone
# would argue for it.
expect_blocked @react-native-async-storage/async-storage "$AUTH" 'AsyncStorage'

echo
echo "the device's position — expo-location belongs to src/shared/lib/platform"
expect_blocked expo-location "$FEATURE" 'src/shared/lib/platform'
expect_blocked expo-location "$SCREEN" 'src/shared/lib/platform'
expect_blocked expo-location "$TEST" 'src/shared/lib/platform'
expect_blocked expo-location "$SUPPORT" 'src/shared/lib/platform'
expect_blocked expo-location "$AUTH" 'src/shared/lib/platform'
expect_blocked expo-location "$OBSERVABILITY" 'src/shared/lib/platform'
expect_blocked expo-location "$OTHER_PLATFORM_FILE" 'src/shared/lib/platform'
# The exemption is one file wide, not one directory wide.
expect_blocked expo-location "$PICKING_PORT" 'src/shared/lib/platform'
expect_allowed expo-location "$LOCATION_PORT"

echo
echo "the photo library — expo-image-picker belongs to src/shared/lib/platform"
expect_blocked expo-image-picker "$FEATURE" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$SCREEN" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$TEST" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$SUPPORT" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$AUTH" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$OBSERVABILITY" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$OTHER_PLATFORM_FILE" 'src/shared/lib/platform'
expect_blocked expo-image-picker "$LOCATION_PORT" 'src/shared/lib/platform'
expect_allowed expo-image-picker "$PICKING_PORT"

echo
printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ] || exit 1
