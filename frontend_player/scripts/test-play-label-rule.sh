#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the Play label rule in eslint.config.mjs.
#
#   bash scripts/test-play-label-rule.sh      # or: pnpm test:labels
#
# `the-words.md` §20.12 books two gates over the accessibility contract, and this
# is the one a type cannot give:
#
#   every Pressable under src/features/play/, src/features/games/ and
#   src/features/proposals/ carries an accessibilityLabel, or hides itself explicitly
#
# Label *coverage* is already a compile error — the copy tables are Records keyed
# by the generated unions, so a code with no words does not build. But the
# historical failure was an OMISSION, and a missing prop is not a missing branch:
# §E6 opens by recording that the prototype has "seven aria-labels in the whole
# file, two of them in this feature." No Record can see that.
#
# A rule that has never fired is indistinguishable from one that cannot, so this
# drives the real linter at code that breaks it and asserts it goes red, at the
# two legitimate shapes and asserts they go green, and at the same violation
# outside Play and asserts it is silent there — a rule that fired everywhere
# would be a design-system rule, which is Part 13's job and a different
# amendment.
#
# It also probes the THREE BASELINE BANS inside features/play/, because the block
# that adds this rule re-declares `no-restricted-syntax` and flat config REPLACES
# a rule rather than extending it. A block that listed only the new entry would
# switch the colour and fontWeight bans off for the whole feature, silently, and
# nothing else in this repository would notice.
#
# The same argument scripts/test-import-boundaries.sh makes for the module bans.
# ESLint is fed each case on stdin under a filename it never opens, so no fixture
# exists on disk for someone to find and helpfully "fix".
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

lint() { # <path> <source>
  printf '%s' "$2" | "$ESLINT" --stdin --stdin-filename "$1" 2>&1
}

expect_blocked() { # <name> <path> <source> <substring the message must name>
  local name="$1" path="$2" source="$3" needle="$4" out status
  out=$(lint "$path" "$source")
  status=$?

  if [ "$status" = 0 ]; then
    bad "$name" "the linter accepted it"
  elif ! printf '%s' "$out" | grep -q -- "$needle"; then
    # A ban that fires without saying what to do instead teaches an agent to
    # delete the control rather than name it.
    bad "$name" "the message never names '$needle'"
  else
    ok "$name"
  fi
}

expect_allowed() { # <name> <path> <source>
  local name="$1" path="$2" source="$3" out status
  out=$(lint "$path" "$source")
  status=$?

  if [ "$status" = 0 ]; then
    ok "$name"
  else
    bad "$name" "$(printf '%s' "$out" | tail -n 3)"
  fi
}

PLAY='src/features/play/components/Seat.tsx'
GAMES='src/features/games/components/ScoreEntry.tsx'
PROPOSALS='src/features/proposals/components/DeckAnswers.tsx'
PLAY_SCREEN='src/features/play/hooks/useSeat.tsx'
ELSEWHERE='src/features/onboarding/components/Step.tsx'
PRIMITIVE='src/shared/ui/Thing.tsx'

IMPORT='import { Pressable, Text, View } from "react-native";'

BARE="$IMPORT
export const A = () => <Pressable onPress={() => undefined}><Text>Add</Text></Pressable>;
"

NAMED="$IMPORT
export const A = () => (
  <Pressable accessibilityLabel=\"Add Marek to the court\" onPress={() => undefined}>
    <Text>Add</Text>
  </Pressable>
);
"

# The court's holding ring and an already-announced toast are legitimately silent:
# what the rule refuses is silence nobody decided on.
HIDDEN="$IMPORT
export const A = () => (
  <Pressable
    accessibilityElementsHidden
    importantForAccessibility=\"no-hide-descendants\"
    onPress={() => undefined}
  >
    <Text>Add</Text>
  </Pressable>
);
"

# Half a hide is not a hide: `accessibilityElementsHidden` is iOS and
# `importantForAccessibility` is Android, so a control carrying one of them is
# hidden on one platform and an unnamed button on the other.
HALF_HIDDEN_IOS="$IMPORT
export const A = () => (
  <Pressable accessibilityElementsHidden onPress={() => undefined}><Text>Add</Text></Pressable>
);
"

HALF_HIDDEN_ANDROID="$IMPORT
export const A = () => (
  <Pressable importantForAccessibility=\"no-hide-descendants\" onPress={() => undefined}>
    <Text>Add</Text>
  </Pressable>
);
"

# The props are the caller's, and the rule cannot see where they came from.
SPREAD="$IMPORT
export const A = (props: object) => <Pressable {...props}><Text>Add</Text></Pressable>;
"

echo "the Play label rule — every Pressable names itself, or says it is hidden"
expect_blocked "an unnamed Pressable is blocked in $PLAY" "$PLAY" "$BARE" 'accessibilityLabel'
expect_blocked "an unnamed Pressable is blocked in $PLAY_SCREEN" "$PLAY_SCREEN" "$BARE" \
  'the-words.md §20'
expect_allowed "a named Pressable is allowed in $PLAY" "$PLAY" "$NAMED"
expect_allowed "an explicitly hidden Pressable is allowed in $PLAY" "$PLAY" "$HIDDEN"
expect_allowed "a spread Pressable is allowed in $PLAY" "$PLAY" "$SPREAD"
expect_blocked "a Pressable hidden on iOS alone is blocked in $PLAY" "$PLAY" \
  "$HALF_HIDDEN_IOS" 'one platform only'
expect_blocked "a Pressable hidden on Android alone is blocked in $PLAY" "$PLAY" \
  "$HALF_HIDDEN_ANDROID" 'one platform only'

# The games feature joined the rule with the result screens: its score grid is the app's
# second surface made of raw Pressables, and a widened selector that fired nowhere new
# would be indistinguishable from one that had not been widened at all.
expect_blocked "an unnamed Pressable is blocked in $GAMES" "$GAMES" "$BARE" 'accessibilityLabel'
expect_allowed "a named Pressable is allowed in $GAMES" "$GAMES" "$NAMED"

# The Games deck's feature joined it when the deck's three answers moved there from Play (#574):
# raw Pressables that were under the rule must not leave it by changing folders.
expect_blocked "an unnamed Pressable is blocked in $PROPOSALS" "$PROPOSALS" "$BARE" 'accessibilityLabel'
expect_allowed "a named Pressable is allowed in $PROPOSALS" "$PROPOSALS" "$NAMED"

echo
echo "and it is scoped to Play, because Part 13 owns the general rule"
expect_allowed "the same violation is silent in $ELSEWHERE" "$ELSEWHERE" "$BARE"
expect_allowed "the same violation is silent in $PRIMITIVE" "$PRIMITIVE" "$BARE"

echo
echo "the three baseline bans survive the block that adds it"
HEX="$IMPORT
export const A = () => <View style={{ backgroundColor: \"#0A3441\" }} />;
"
RGBA="$IMPORT
export const A = () => <View style={{ backgroundColor: \"rgba(0,0,0,0.4)\" }} />;
"
WEIGHT="$IMPORT
export const A = () => <Text style={{ fontWeight: \"700\" }}>x</Text>;
"
expect_blocked "a hex literal is still blocked in $PLAY" "$PLAY" "$HEX" 'theme.ts'
expect_blocked "an rgba() literal is still blocked in $PLAY" "$PLAY" "$RGBA" 'theme.ts'
expect_blocked "fontWeight is still blocked in $PLAY" "$PLAY" "$WEIGHT" 'Android'
expect_blocked "a hex literal is still blocked in $PROPOSALS" "$PROPOSALS" "$HEX" 'theme.ts'

echo
printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ] || exit 1
