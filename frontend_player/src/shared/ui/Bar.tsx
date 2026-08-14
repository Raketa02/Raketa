/**
 * The bar, per design-system 7.3 — a 4pt track with a caller-chosen fill.
 *
 * The caller sets the fill because a bar means whatever the screen using it means; the
 * onboarding progress bar is `coral`. The track is `line2` — a fold inside one thing,
 * not a boundary between two.
 *
 * **A bar is never the only carrier of its own value.** It reports one to a screen reader
 * through `accessibilityValue`, and every screen that uses it also says the number in
 * words nearby, because a filled rectangle is not readable at any font size.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from './theme';

export interface BarProps {
  /** How far along, as a count — `now` of `total`. Both are what the label says. */
  readonly now: number;
  readonly total: number;
  readonly fill: string;
  readonly accessibilityLabel: string;
}

export function Bar({ now, total, fill, accessibilityLabel }: BarProps) {
  const fraction = total <= 0 ? 0 : Math.min(Math.max(now / total, 0), 1);

  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel={accessibilityLabel}
      accessibilityValue={{ min: 0, max: total, now }}
      style={s.track}
    >
      <View
        style={[s.fill, { width: `${fraction * 100}%`, backgroundColor: fill }]}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </View>
  );
}

const s = StyleSheet.create({
  track: {
    height: theme.size.bar,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.line2,
    overflow: 'hidden',
  },
  fill: { height: '100%', borderRadius: theme.radius.bar },
});
