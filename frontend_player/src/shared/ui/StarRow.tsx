/**
 * The star row — [6.13](../../../docs/design-system.md#613-the-star-row).
 *
 * Five stars for one person, and the answer is **one number or no number at all**.
 *
 * ```
 * ★ ★ ★ ☆ ☆        three stars
 * ☆ ☆ ☆ ☆ ☆        blank — an absence, and never a zero
 * ```
 *
 * ## Blank is an absence, which is why `stars` is optional and never `0`
 *
 * *Nobody rated them* and *they were rated nought* are different facts, and the second one
 * does not exist on this platform: the scale is one to five with **no zero**, because a
 * rating that reads as *worthless* is a weapon out of proportion to a tap. A row whose value
 * was `number` with `0` meaning blank would be that missing sixth value spelled in the one
 * place a reader would take it for a rating. So the absence is `undefined`, and the row
 * draws five outlines.
 *
 * ## The row reports, and the caller decides — including what a second press means
 *
 * [6.8](../../../docs/design-system.md#68-the-availability-grid)'s cell fires on every press
 * whether or not it is ticked, and this fires on every press whatever is standing. **Whether
 * pressing the star that already stands clears the row is not this component's rule** — it is
 * a rule about what an answer is, it belongs to whoever owns the answer, and a row that
 * decided it here would be the second place it was written. What the row does own is *where*
 * `clearHint` is announced, because that is a fact about which element is the current value.
 *
 * ## One element per action, and five actions
 *
 * `the-words.md` §20.1: one accessibility element per action, and a listener has no picture
 * of the row to count along. So each star is its own element with its own name, the names are
 * the caller's — **a label is never a template inlined in a component** — and the tuple type
 * is what makes *five names or it does not compile* true rather than hoped for. The standing
 * value announces itself as `selected`; the four beside it do not, because *"3 stars,
 * selected; 4 stars; 5 stars"* is the row read once, where marking every filled star selected
 * is it read as a table.
 *
 * ## Geometry reaches 44 by itself
 *
 * Each star is a 44pt target with the 24pt drawing inside it, and the five sit **flush**.
 * [6.5](../../../docs/design-system.md#65-touch-targets) bounds horizontal `hitSlop` by the
 * neighbour, so a gap between the targets would be a strip of the row that answers nothing —
 * and slop around a 24pt glyph would be five targets overlapping. This is 6.8's and 6.11's
 * decision taken a third time: the control reaches the minimum by its own size.
 */

import { Pressable, StyleSheet, View } from 'react-native';

import { Star } from './Star';
import { theme } from './theme';

const geometry = theme.size.star;

/**
 * The five names, ascending — *one star for kasia_w* … *five stars for kasia_w*.
 *
 * A tuple and not an array: the scale is five and a caller handing over four would otherwise
 * draw four stars and call it a rating.
 */
export type StarNames = readonly [string, string, string, string, string];

export interface StarRowProps {
  /**
   * How many stars stand. **Absent is blank** — see the module note — and a value outside
   * one to five cannot be constructed by the feature that owns the answer.
   */
  readonly stars?: number;
  readonly names: StarNames;
  /**
   * Announced on the star that already stands, and on that one alone.
   *
   * Absent when a second press does not clear, which is the caller's rule to have.
   */
  readonly clearHint?: string;
  /** Fires on every press with the value pressed, standing or not. */
  readonly onPress: (stars: number) => void;
  readonly disabled?: boolean;
}

export function StarRow({ stars, names, clearHint, onPress, disabled = false }: StarRowProps) {
  return (
    <View style={s.row}>
      {names.map((name, index) => {
        const value = index + 1;
        const standing = value === stars;

        return (
          <Pressable
            // The position, not the name: `StarNames` guarantees five strings and not five
            // distinct ones, and a caller whose two stars read the same would be two keys.
            key={value}
            accessibilityRole="button"
            accessibilityLabel={name}
            accessibilityHint={standing ? clearHint : undefined}
            // *Not selected* and *not a choice* are different facts, so the four that are
            // neither say nothing — `Button`'s rule about the same prop, for its reason.
            accessibilityState={{ selected: standing || undefined, disabled }}
            disabled={disabled}
            onPress={() => onPress(value)}
            // Touch has no hover, so the pressed appearance is declared (6.6). Opacity is the
            // system's answer for a surface with no darker companion — there is no fill here
            // to darken, only a drawing.
            style={({ pressed }) => [s.target, pressed && !disabled ? s.pressed : undefined]}
          >
            <Star given={stars !== undefined && value <= stars} />
          </Pressable>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center' },
  target: {
    width: geometry.target,
    height: geometry.target,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { opacity: 0.7 },
});
