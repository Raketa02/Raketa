/**
 * The tick — [6.8](../../../docs/design-system.md#68-the-availability-grid)'s mark, drawn
 * once.
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
 * **It takes no props, and the colour is not one of them.** A tick is only ever drawn on
 * the `ink` fill that 6.8's selected state inverts to, so `surface` is the only value there
 * has ever been — the app's one white, with no separate `white` token, at 17,50:1 on `ink`.
 * A `color` prop would be a choice offered to callers that neither of them has, and the
 * contrast figure would then be stated at every call site instead of held here.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from './theme';

const PATH = 'M 2.5 6.5 L 5 9 L 9.5 3.5';

export function Tick() {
  const { tick, tickStroke } = theme.size.availability;
  return (
    <Svg width={tick} height={tick} viewBox={`0 0 ${tick} ${tick}`}>
      <Path
        d={PATH}
        stroke={theme.color.surface}
        strokeWidth={tickStroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}
