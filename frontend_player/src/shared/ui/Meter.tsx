/**
 * The meter, per design-system [7.3](../../../docs/design-system.md#73-meter-and-bar) — a 5pt
 * `line2` track with a `night` fill.
 *
 * 7.3 specifies two rows and only the second was built: `Bar` states a fraction to a screen
 * that names its denominator, and reports one through `accessibilityValue`. **This is the
 * other row, and it is the opposite object.**
 *
 * ## It is decoration, and that is its whole contract
 *
 * `the-words.md` §20.8: the why-fit row draws a label, a mono `×{weight} → {value}`, **then**
 * this meter. The number is already text two words earlier.
 *
 * > **The meter is hidden and the row's words carry it.**
 *
 * That is [6.8](../../../docs/design-system.md#68-the-availability-grid)'s argument again —
 * *"the column heads are therefore decoration to assistive technology and are hidden from it;
 * without that, every cell is announced twice."* A bar visualising a printed number is that
 * same double announcement. §E6 asked for the opposite — *"expose it as a progress indicator
 * with its current, minimum and maximum values"* — and it is the fifth of its rows rewritten:
 * it would publish a precision the row already states, in a shape the row already chose.
 *
 * So the component takes **no `accessibilityLabel` and no value**, and there is nothing to
 * pass one through. `SH.player`'s three meters were the only others in the prototype and K-7
 * ruled them out, which is what makes the rule flat: **`progressbar` appears nowhere in the
 * Play contract.** A caller who needs a bar that announces wants `Bar`, on a screen that says
 * its number in words nearby.
 *
 * The share is clamped here rather than at the call site, for
 * [7.5](../../../docs/design-system.md#75-the-level-bar)'s reason: a value must land in the
 * same place everywhere, and a clamp per caller is how one number ends up drawn two ways.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from './theme';

export interface MeterProps {
  /** How full, 0 to 1. Clamped here; the caller does the arithmetic, not the guarding. */
  readonly share: number;
}

export function Meter({ share }: MeterProps) {
  const filled = Math.min(Math.max(share, 0), 1);

  return (
    // Hidden on both platforms. `accessibilityElementsHidden` is iOS and
    // `importantForAccessibility` is Android; one alone leaves it readable on the other.
    <View
      style={s.track}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View style={[s.fill, { width: `${filled * 100}%` }]} />
    </View>
  );
}

const s = StyleSheet.create({
  track: {
    height: theme.size.meter,
    borderRadius: theme.radius.meter,
    backgroundColor: theme.color.line2,
    overflow: 'hidden',
  },
  fill: { height: '100%', borderRadius: theme.radius.meter, backgroundColor: theme.color.night },
});
