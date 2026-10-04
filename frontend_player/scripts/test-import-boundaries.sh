#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the module bans in eslint.config.mjs.
#
#   bash scripts/test-import-boundaries.sh      # or: pnpm test:boundaries
#
# Eight modules may be imported from exactly one place:
#
#   expo-secure-store                            → src/shared/lib/auth
#   @react-native-async-storage/async-storage    → feature_flags/api/datafileCache.ts
#                                                  and preferences/phonePreferences.ts
#   expo-location                                → platform/location.ts
#   expo-image-picker                            → platform/imagePicking.ts
#   react-native-sse                             → platform/liveStream.ts
#   expo-haptics                                 → platform/haptics.ts
#   expo-clipboard                               → platform/clipboard.ts
#   @featurevisor/sdk                            → feature_flags/api/featurevisor.ts
#
# And one **name** out of a module every screen imports:
#
#   { Share } from 'react-native'                → platform/share.ts
#
# AsyncStorage was banned everywhere until ADR-0180 let the feature flags' saved datafile
# use it — a public file, never a credential — and ADR-0188 let the phone-preferences store
# keep three choices a player made beside it. The ban is still asserted everywhere else, both
# owning modules' own directories included, because an allow-list of two is only two while
# something checks it.
#
# And one is banned everywhere *except* a feature's api/ and mappers/ layers, plus the
# one file above that is an api/ layer without a feature to live in:
#
#   @/generated/**                               → api/, mappers/, platform/liveStream.ts
#
# One more is banned in **one feature only**, and it is the one rule here that is about
# two features rather than about a module:
#
#   @/features/plans                             → never from features/games
#
# ADR-0149 §1: `features/plans` may import `features/games` and never the reverse, which
# keeps ADR-0145 §4's clause — *"`games` importing the Plan"* — checkable on this side of
# the wire. That record says so in as many words: *"a grep, not a judgement"*. This is
# where the grep is proved still to fire, in both directions, because a one-way edge that
# has quietly become a wall is as wrong as one that has become a door.
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

# The same, for one NAME out of a module — `Share` out of `react-native`, whose every other name
# is the app's own drawing and must stay free.
lint_named_import() { # <name> <module> <path>
  printf "import { %s } from '%s';\n\nexport const used = %s;\n" "$1" "$2" "$1" \
    | "$ESLINT" --stdin --stdin-filename "$3" 2>&1
}

expect_name_blocked() { # <name> <module> <path> <substring the message must name>
  local name="$1" module="$2" path="$3" needle="$4" out status
  out=$(lint_named_import "$name" "$module" "$path")
  status=$?

  if [ "$status" = 0 ]; then
    bad "{ $name } from $module is blocked in $path" "the linter accepted it"
  elif ! printf '%s' "$out" | grep -q -- "$needle"; then
    bad "{ $name } from $module is blocked in $path" "the message never names '$needle'"
  else
    ok "{ $name } from $module is blocked in $path"
  fi
}

expect_name_allowed() { # <name> <module> <path>
  local name="$1" module="$2" path="$3" out status
  out=$(lint_named_import "$name" "$module" "$path")
  status=$?

  if [ "$status" = 0 ]; then
    ok "{ $name } from $module is allowed in $path"
  else
    bad "{ $name } from $module is allowed in $path" "$(printf '%s' "$out" | tail -n 3)"
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
LIVE_PORT='src/shared/lib/platform/liveStream.ts'
HAPTICS_PORT='src/shared/lib/platform/haptics.ts'
CLIPBOARD_PORT='src/shared/lib/platform/clipboard.ts'
SHARE_PORT='src/shared/lib/platform/share.ts'
OTHER_PLATFORM_FILE='src/shared/lib/platform/appState.ts'

# The flag seam's three edges, each an api/ file of one feature: the fetch, the saved
# datafile (the one AsyncStorage importer), and the SDK wrapper (the one Featurevisor
# importer). Each exemption is one file wide, so the two exempt files are each probed with
# the other's module, and the fetch beside them with both.
FLAGS_FETCH='src/features/feature_flags/api/datafileApi.ts'
FLAGS_CACHE='src/features/feature_flags/api/datafileCache.ts'
FLAGS_SDK='src/features/feature_flags/api/featurevisor.ts'
FLAGS_HOOK='src/features/feature_flags/hooks/useFeatureOnMount.ts'

# The phone-preferences store (ADR-0188 §1) — the second AsyncStorage importer, one file wide
# like the first: its own directory's barrel may not, and neither may the sign-out sequence that
# empties it through the barrel.
PREFERENCES_STORE='src/shared/lib/preferences/phonePreferences.ts'
PREFERENCES_OTHER='src/shared/lib/preferences/index.ts'

# Where a generated wire type is legitimately read: the two layers of a feature, and the
# one file outside a feature that is an api/ layer — the live channel, whose frame ADR-0147
# §7 requires to be the generated type.
WIRE_LAYER='src/features/onboarding/api/placeholder.ts'

# The one-way edge's four sides: the three layers of `features/games` the ban has to reach,
# and the feature on the permitted side of it.
GAMES_SCREEN='src/features/games/components/Placeholder.tsx'
GAMES_WIRE='src/features/games/mappers/placeholder.ts'
GAMES_DOMAIN='src/features/games/domain/placeholder.ts'
PLANS_SCREEN='src/features/plans/components/Placeholder.tsx'
CHALLENGES_SCREEN='src/features/challenges/components/Placeholder.tsx'

echo "the keychain — expo-secure-store belongs to src/shared/lib/auth"
expect_blocked expo-secure-store "$FEATURE" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$SCREEN" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$TEST" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$LOCATION_PORT" 'src/shared/lib/auth'
expect_blocked expo-secure-store "$OBSERVABILITY" 'src/shared/lib/auth'
expect_allowed expo-secure-store "$AUTH"

echo
echo "unencrypted storage — @react-native-async-storage/async-storage belongs to the saved datafile"
expect_blocked @react-native-async-storage/async-storage "$FEATURE" 'datafileCache.ts'
expect_blocked @react-native-async-storage/async-storage "$SCREEN" 'datafileCache.ts'
expect_blocked @react-native-async-storage/async-storage "$TEST" 'datafileCache.ts'
expect_blocked @react-native-async-storage/async-storage "$SUPPORT" 'datafileCache.ts'
# Not even the module that owns credentials, which is the only place anyone
# would argue for it — and the message still says why.
expect_blocked @react-native-async-storage/async-storage "$AUTH" 'credentials'
# Another feature's wire layer, which shares the owning file's baseline block.
expect_blocked @react-native-async-storage/async-storage "$WIRE_LAYER" 'datafileCache.ts'
# One file wide: the flag seam's own fetch, its SDK wrapper and its hooks may not.
expect_blocked @react-native-async-storage/async-storage "$FLAGS_FETCH" 'datafileCache.ts'
expect_blocked @react-native-async-storage/async-storage "$FLAGS_SDK" 'datafileCache.ts'
expect_blocked @react-native-async-storage/async-storage "$FLAGS_HOOK" 'datafileCache.ts'
expect_allowed @react-native-async-storage/async-storage "$FLAGS_CACHE"
# The second owner, and the message names it so a blocked import knows where the door is.
expect_blocked @react-native-async-storage/async-storage "$FEATURE" 'phonePreferences.ts'
expect_blocked @react-native-async-storage/async-storage "$PREFERENCES_OTHER" 'phonePreferences.ts'
expect_blocked @react-native-async-storage/async-storage "$OTHER_PLATFORM_FILE" 'phonePreferences.ts'
expect_allowed @react-native-async-storage/async-storage "$PREFERENCES_STORE"
# And it is exempt from the path ban only: the keychain is still the auth module's.
expect_blocked expo-secure-store "$PREFERENCES_STORE" 'src/shared/lib/auth'

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
expect_blocked expo-image-picker "$LIVE_PORT" 'src/shared/lib/platform'
expect_allowed expo-image-picker "$PICKING_PORT"

echo
echo "the live channel — react-native-sse belongs to platform/liveStream.ts"
expect_blocked react-native-sse "$FEATURE" 'liveStream.ts'
expect_blocked react-native-sse "$SCREEN" 'liveStream.ts'
expect_blocked react-native-sse "$TEST" 'liveStream.ts'
expect_blocked react-native-sse "$SUPPORT" 'liveStream.ts'
expect_blocked react-native-sse "$AUTH" 'liveStream.ts'
# One file wide, again: the two native ports beside it may not open a socket either.
expect_blocked react-native-sse "$LOCATION_PORT" 'liveStream.ts'
expect_blocked react-native-sse "$OTHER_PLATFORM_FILE" 'liveStream.ts'
expect_allowed react-native-sse "$LIVE_PORT"

echo
echo "the motor — expo-haptics belongs to platform/haptics.ts"
expect_blocked expo-haptics "$FEATURE" 'haptics.ts'
expect_blocked expo-haptics "$SCREEN" 'haptics.ts'
expect_blocked expo-haptics "$TEST" 'haptics.ts'
expect_blocked expo-haptics "$AUTH" 'haptics.ts'
# One file wide, as the others are: the three ports beside it may not buzz.
expect_blocked expo-haptics "$LOCATION_PORT" 'haptics.ts'
expect_blocked expo-haptics "$LIVE_PORT" 'haptics.ts'
expect_blocked expo-haptics "$OTHER_PLATFORM_FILE" 'haptics.ts'
expect_allowed expo-haptics "$HAPTICS_PORT"
# And the port itself is still under every other ban.
expect_blocked expo-location "$HAPTICS_PORT" 'src/shared/lib/platform'

echo
echo "the clipboard — expo-clipboard belongs to platform/clipboard.ts"
expect_blocked expo-clipboard "$FEATURE" 'clipboard.ts'
expect_blocked expo-clipboard "$SCREEN" 'clipboard.ts'
expect_blocked expo-clipboard "$TEST" 'clipboard.ts'
expect_blocked expo-clipboard "$AUTH" 'clipboard.ts'
# One file wide: the motor beside it may not read the clipboard.
expect_blocked expo-clipboard "$HAPTICS_PORT" 'clipboard.ts'
expect_blocked expo-clipboard "$OTHER_PLATFORM_FILE" 'clipboard.ts'
expect_allowed expo-clipboard "$CLIPBOARD_PORT"
# And the port itself is still under every other ban.
expect_blocked expo-haptics "$CLIPBOARD_PORT" 'haptics.ts'

echo
echo "the share sheet — { Share } from react-native belongs to platform/share.ts"
expect_name_blocked Share react-native "$FEATURE" 'share.ts'
expect_name_blocked Share react-native "$SCREEN" 'share.ts'
expect_name_blocked Share react-native "$TEST" 'share.ts'
expect_name_blocked Share react-native "$AUTH" 'share.ts'
# One file wide: the clipboard beside it may not share, and neither may the two files that are
# exempt from the other path ban — an exemption subtracts one entry, never the list.
expect_name_blocked Share react-native "$CLIPBOARD_PORT" 'share.ts'
expect_name_blocked Share react-native "$OTHER_PLATFORM_FILE" 'share.ts'
expect_name_blocked Share react-native "$FLAGS_CACHE" 'share.ts'
expect_name_blocked Share react-native "$PREFERENCES_STORE" 'share.ts'
expect_name_allowed Share react-native "$SHARE_PORT"
# The ban is one name wide: every other name out of the module is the app's own drawing.
expect_name_allowed View react-native "$FEATURE"
# And the port itself is still under every other ban, the storage path included.
expect_blocked expo-clipboard "$SHARE_PORT" 'clipboard.ts'
expect_blocked @react-native-async-storage/async-storage "$SHARE_PORT" 'datafileCache.ts'

echo
echo "flag evaluation — @featurevisor/sdk belongs to feature_flags/api/featurevisor.ts"
expect_blocked @featurevisor/sdk "$FEATURE" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$SCREEN" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$TEST" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$WIRE_LAYER" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$OTHER_PLATFORM_FILE" 'featurevisor.ts'
# One file wide: the cache beside it, the fetch and the gate itself go through it.
expect_blocked @featurevisor/sdk "$FLAGS_CACHE" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$FLAGS_FETCH" 'featurevisor.ts'
expect_blocked @featurevisor/sdk "$FLAGS_HOOK" 'featurevisor.ts'
expect_allowed @featurevisor/sdk "$FLAGS_SDK"
# And the SDK wrapper is still under every other ban.
expect_blocked expo-location "$FLAGS_SDK" 'src/shared/lib/platform'

echo
echo "generated wire types — api/ and mappers/, plus the live channel's frame"
expect_blocked @/generated/schema "$FEATURE" "api/ or mappers/"
expect_blocked @/generated/schema "$SCREEN" "api/ or mappers/"
expect_blocked @/generated/schema "$LOCATION_PORT" "api/ or mappers/"
expect_blocked @/generated/schema "$OTHER_PLATFORM_FILE" "api/ or mappers/"
expect_allowed @/generated/schema "$WIRE_LAYER"
# The one file outside a feature that reads one, and it is exempt from a second ban as well —
# which is exactly the shape the `sharedPatternsExcept` subtraction exists to keep honest.
expect_allowed @/generated/schema "$LIVE_PORT"

echo
echo "the one-way edge — features/games may never import features/plans"
# Every layer of the feature, because the ban is three blocks: flat config replaces a rule
# rather than adding to it, so the wire layer and the pure layers each restate the baseline
# block they shadow. A ban that reached only `components/` would be a ban a mapper walks past.
expect_blocked @/features/plans "$GAMES_SCREEN" 'ADR-0149'
expect_blocked @/features/plans "$GAMES_WIRE" 'ADR-0149'
expect_blocked @/features/plans "$GAMES_DOMAIN" 'ADR-0149'
# The other direction is the sanctioned one, and it is asserted so that a later hand at this
# file cannot "tidy" the ban into a symmetric wall — which would delete the composition
# ADR-0149 chose over a second read.
expect_allowed @/features/games/types "$PLANS_SCREEN"
# And the two exemptions the games blocks shadow are still exemptions: a re-listed block
# that dropped either would be silent, and this is the only place it would show.
expect_allowed @/generated/schema "$GAMES_WIRE"
expect_blocked @/generated/schema "$GAMES_SCREEN" "api/ or mappers/"
expect_blocked react-native "$GAMES_DOMAIN" 'pure TypeScript'
# The two declared edges the other way out of `games` (#415): the forecast block cites Play's
# balance words through its public surface, and the players card opens `player_record`'s
# sheet. Asserted so a later hand widening the one-way ban into "games imports no feature"
# goes red here rather than at the first `pnpm lint` after it.
expect_allowed @/features/play/types "$GAMES_SCREEN"
expect_allowed @/features/player_record/types "$GAMES_SCREEN"
# And the deep path is still what it always was: a feature never reaches past another's types.ts.
expect_blocked @/features/play/components/balancePresentation "$GAMES_SCREEN" 'types.ts'
# The yes screen's one new edge (ADR-0167 §3): `challenges` reads the reader's own face through
# `player_record`'s public surface, and nothing deeper.
expect_allowed @/features/player_record/types "$CHALLENGES_SCREEN"
expect_blocked @/features/player_record/hooks/useOwnFace "$CHALLENGES_SCREEN" 'types.ts'

echo
printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ] || exit 1
