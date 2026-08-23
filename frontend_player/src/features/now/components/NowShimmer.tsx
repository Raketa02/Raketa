/**
 * The cold open: a shimmer, over a screen with nothing on it.
 *
 * `ADR-0054` shows loading twice and differently. **A cold open shows this** —
 * nothing is restored from the last launch, so there is no stale card to tap and
 * no dead offer to resurrect. **A pull keeps the current screen exactly where it
 * is** and shows an indicator at the top instead, because what she is reading is
 * real and we are checking. A shimmer says *there is nothing here yet*; the pull
 * indicator says *this is true and I am checking*. **Neither is a staleness
 * marker**, and there is no third state that admits one.
 *
 * It does not animate, and that is not an omission waiting to be filled: the
 * design system moves four things and this is not one of them, and a pulsing
 * placeholder is the first thing a player who asked the OS to calm motion down
 * would rather not have. It is a set of quiet blocks in the shape the screen is
 * about to take, so the layout does not jump when the answer lands.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from '@/shared/ui';

import { GUTTER } from './nowGeometry';

export const SHIMMER_ID = 'now-shimmer';

/** How many placeholder rows. Enough to fill a phone, few enough to look calm. */
const ROWS = [1, 2, 3];

export function NowShimmer() {
  return (
    <View
      testID={SHIMMER_ID}
      style={s.shimmer}
      accessibilityRole="progressbar"
      accessibilityLabel="Loading your screen"
    >
      {ROWS.map((row) => (
        <View key={row} style={s.block} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  shimmer: { paddingHorizontal: GUTTER, gap: theme.space.sm },
  block: {
    height: theme.size.btnXl * 2,
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.line2,
  },
});
