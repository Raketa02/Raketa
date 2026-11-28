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
 *
 * ## The fill takes a tone, and the tone is the caller's rule rather than the meter's
 *
 * The record card's metered rows were drawn in three fills where the why-fit row's were drawn in
 * one ([#385](https://github.com/Rakieta02/Rakieta/issues/385)), so `tone` is a **step in an
 * existing fill** and invents no colour — [15.2](../../../docs/design-system.md#152-adding-a-colour)'s
 * own licence. What it deliberately does not carry is the ladder: *where* good becomes poor is a
 * fact about the figure being drawn and belongs to whoever knows what the figure means. A meter
 * that banded its own share would be a second opinion.
 *
 * **No surface draws it since [#660](https://github.com/Rakieta02/Rakieta/issues/660)**: the
 * why-fit sheet left with Classic play, and the record card draws Player reliability's counts as
 * words. It stays as 7.3's primitive (`shared/ui/README.md` says until when).
 *
 * **The three fills are derived, never eyeballed** — `meterTone.test.ts` holds each against the
 * track it is drawn on and each pair against the other two, in lightness as well as in hue,
 * because a tone is the third cue behind the bar's own length and the fraction printed two
 * words earlier and must never be the only one.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from './theme';

/** The three steps, named for what the caller's own ladder said rather than for a colour. */
export type MeterTone = 'good' | 'neutral' | 'poor';

/**
 * What each step is drawn in — read by the derivation test, so repainting one goes red rather
 * than going unnoticed.
 *
 * `neutral` is 7.3's own `night`, which is what every meter drew before there was a tone and
 * what one still draws when its caller has no ladder to read.
 */
export const METER_TONE_FILL: Readonly<Record<MeterTone, string>> = {
  good: theme.color.mint,
  neutral: theme.color.night,
  poor: theme.color.red,
};

export interface MeterProps {
  /** How full, 0 to 1. Clamped here; the caller does the arithmetic, not the guarding. */
  readonly share: number;
  /**
   * What the caller's own ladder made of the figure. Defaults to `neutral`, which is 7.3's
   * `night` — a meter whose caller grades nothing is drawn exactly as it always was.
   */
  readonly tone?: MeterTone;
}

export function Meter({ share, tone = 'neutral' }: MeterProps) {
  const filled = Math.min(Math.max(share, 0), 1);

  return (
    // Hidden on both platforms. `accessibilityElementsHidden` is iOS and
    // `importantForAccessibility` is Android; one alone leaves it readable on the other.
    <View
      style={s.track}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View
        style={[s.fill, { width: `${filled * 100}%`, backgroundColor: METER_TONE_FILL[tone] }]}
      />
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
  // The fill's colour is the tone's and is set on the element — see `METER_TONE_FILL`.
  fill: { height: '100%', borderRadius: theme.radius.meter },
});
