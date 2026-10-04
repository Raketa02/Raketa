/**
 * **A group's sport dots** — one per sport at least two members are rated in, in the registry's
 * order (play 1, 24, 38; ADR-0183 §6). Drawn with no name beside them, as the mocks draw them:
 * the element they sit in speaks the sports by name, so a listener gets the words and a reader
 * gets the colours next to the group's name (Part 16 records it against 2.3's premise).
 */

import { StyleSheet, View } from 'react-native';

import { sportColour } from '@/features/onboarding/types';
import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

export function SportDots({ sports }: { readonly sports: readonly Sport[] }) {
  if (sports.length === 0) return null;

  return (
    <View style={s.row} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      {sports.map((sport) => (
        <View key={sport} style={[s.dot, { backgroundColor: sportColour(sport) }]} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
});
