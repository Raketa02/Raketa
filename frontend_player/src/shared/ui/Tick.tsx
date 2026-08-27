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
 * The colour is the caller's, because it is always the inverse of whatever it sits on and
 * only the caller knows that. Both callers fill with `ink`, so both pass `surface`.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from './theme';

const PATH = 'M 2.5 6.5 L 5 9 L 9.5 3.5';

export interface TickProps {
  /** The stroke colour. `surface` on an `ink` fill is 17,50:1. */
  readonly color: string;
}

export function Tick({ color }: TickProps) {
  const { tick, tickStroke } = theme.size.availability;
  return (
    <Svg width={tick} height={tick} viewBox={`0 0 ${tick} ${tick}`}>
      <Path
        d={PATH}
        stroke={color}
        strokeWidth={tickStroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}
