/**
 * [6.8](../../../docs/design-system.md#68-the-availability-grid)'s mark family — one 12 x 12
 * box, one 2pt round-capped stroke, three shapes.
 *
 * The **tick** is the editor's, and the two that join it are the diff variant's: a **plus**
 * for a slot the search added and a **dash** for one it dropped. Three shapes rather than
 * three colours is what makes the diff grid answer
 * [Part 13](../../../docs/design-system.md#part-13--accessibility) — the prototype drew *new*
 * as a volt ring and *dropped* as 45% opacity, which is colour twice over, and a volt ring on
 * paper is 1,3:1 besides. Plus and minus are the diff idiom every reader already has, and
 * 6.9's add glyph is the same crossed pair at 20 x 20, so nothing here is a new drawing.
 *
 * ## The tick
 *
 * A 12 × 12 path with a 2pt round-capped, round-joined stroke: at 2pt, butt caps make a
 * tick read as two bars meeting at a corner. It is **geometry and not a glyph**, so it does
 * not scale with Dynamic Type and does not vary by platform font.
 *
 * It lives here rather than inside the grid because two controls now draw it — the
 * availability cell and the tick box ([6.11](../../../docs/design-system.md#611-the-tick-box))
 * — and a second copy of the path is exactly the drift `README.md` says this barrel exists
 * to prevent.
 *
 * **None of the three takes props, and the colour is not one of them.** Each is drawn on
 * exactly one bed and so has exactly one value, held here with its contrast figure rather
 * than restated at every call site: the tick is `surface` on `ink` (17,50:1), the plus is
 * `volt` on `ink` — volt as a stroke, which is legal only on dark and this is dark — and the
 * dash is `muted` on `surface` (5,40:1). A `color` prop would be a choice offered to callers
 * that none of them has.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from './theme';

const TICK = 'M 2.5 6.5 L 5 9 L 9.5 3.5';
/** The crossed pair, at the tick's box. 6.9's add glyph is this drawing at 20 x 20. */
const PLUS = 'M 6 2.5 V 9.5 M 2.5 6 H 9.5';
/** The plus with its upright taken away, which is what a dropped slot is. */
const DASH = 'M 2.5 6 H 9.5';

function Mark({ d, stroke }: { readonly d: string; readonly stroke: string }) {
  const { tick, tickStroke } = theme.size.availability;
  return (
    <Svg width={tick} height={tick} viewBox={`0 0 ${tick} ${tick}`}>
      <Path
        d={d}
        stroke={stroke}
        strokeWidth={tickStroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}

export function Tick() {
  return <Mark d={TICK} stroke={theme.color.surface} />;
}

/** A slot this search added. Volt on `ink`: a stroke, on the one kind of bed it may be one. */
export function Plus() {
  return <Mark d={PLUS} stroke={theme.color.volt} />;
}

/** A slot this search dropped. Drawn on the unselected cell, so `muted` is the value. */
export function Dash() {
  return <Mark d={DASH} stroke={theme.color.muted} />;
}
