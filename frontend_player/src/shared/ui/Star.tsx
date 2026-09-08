/**
 * The star — [6.13](../../../docs/design-system.md#613-the-star-row)'s one drawn mark, in two
 * states.
 *
 * ```
 * ★ ★ ★ ☆ ☆
 *
 * (Three of five. The given star is a solid `ink` fill, the blank one a `muted` outline —
 *  a shape difference and a lightness difference, and never a hue one.)
 * ```
 *
 * ## Geometry, not a glyph, and here the alternative did not exist
 *
 * `Tick.tsx` draws its mark rather than typing one so that it does not scale with Dynamic
 * Type and does not vary by platform font. The same holds here, and one more thing does:
 * **there was no glyph to type.** Archivo ships no U+2605, exactly as it ships no U+2713 —
 * the reason the on-court mark lost its ✓ — and
 * [ADR-0135](../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)
 * fixed the icon family as Feather, which *"is a font with one weight and no filled
 * counterparts"*. A five-star row is precisely the case that limitation binds: the whole
 * control is a filled mark told apart from an unfilled one. So the pair is drawn.
 *
 * The path is a true pentagram — outer radius 11 in the 24pt box, inner radius
 * `11 · sin 18° / sin 126°` — translated so its bounding box is centred in the box rather
 * than its circumcentre, which sits above centre and would hang the row.
 *
 * ## Fill, and the ratios behind it
 *
 * `ink` given and `muted` blank: 3,24:1 between the two and 17,50 / 5,40 against the
 * `surface` the card draws them on, all three clearing
 * [1.4.11](../../../docs/design-system.md#25-contrast--computed)'s 3:1 for a graphical
 * object. It is the run of form's own pair, chosen for the run's own reason — the difference
 * is **lightness** and not hue, so the row survives being read in one colour — and the
 * three ratios are derived in `starRow.test.ts` off `STAR_FILL` rather than off the theme,
 * so repainting a star here goes red.
 *
 * The two states also differ in **shape**, which the run of form's squares could not: solid
 * against outline. [Part 13](../../../docs/design-system.md#part-13--accessibility) is
 * satisfied twice over for the sighted half before the spoken half is reached, and the
 * spoken half is `StarRow`'s.
 *
 * **Neither takes a colour prop.** Each is drawn on exactly one bed and so has exactly one
 * value — `Tick.tsx`'s rule, and for its reason: the bed is a fact about where a mark is
 * drawn, not a decision a caller makes.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from './theme';

/**
 * The pentagram, in the 24pt box. Computed rather than eyeballed — see the module note.
 *
 * One path for both states: a star that was given is the same star, filled.
 */
const STAR =
  'M 12.00 2.05 L 14.47 9.65 L 22.46 9.65 L 16.00 14.35 L 18.47 21.95 ' +
  'L 12.00 17.25 L 5.53 21.95 L 8.00 14.35 L 1.54 9.65 L 9.53 9.65 Z';

/** The outline's weight. `Tick`'s 2pt is a stroke on a 12pt box; this is one on a 24pt box. */
const OUTLINE = 1.5;

/**
 * The two values, as one table rather than two style keys.
 *
 * Exported for `RUN_OF_FORM_FILL`'s reason: the arithmetic that makes them legal belongs to
 * a test, and a test parsing `theme.color.ink` would go on passing the day this component
 * started drawing something else.
 */
export const STAR_FILL = {
  given: theme.color.ink,
  blank: theme.color.muted,
} as const;

export interface StarProps {
  /** Given, or blank. **Not `selected`** — the row's state is a number, not a set of flags. */
  readonly given: boolean;
}

export function Star({ given }: StarProps) {
  const size = theme.size.star.glyph;

  return (
    <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <Path
        d={STAR}
        fill={given ? STAR_FILL.given : 'none'}
        stroke={given ? undefined : STAR_FILL.blank}
        strokeWidth={given ? undefined : OUTLINE}
        strokeLinejoin="round"
      />
    </Svg>
  );
}
