/**
 * **⇅, drawn** — the switcher chip's mark (club 7): an arrow up beside an arrow down, in `muted`.
 * Geometry and not a glyph, for the tick's reasons: Feather ships no up-and-down pair, Archivo is
 * never asked for a mark, and a drawn mark does not vary by platform font. Hidden from assistive
 * technology — the chip's name says what it does.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

/** Two arrows in a 16-unit box: up on the left, down on the right. */
const ARROWS = 'M 5 13 V 3 M 2 6 L 5 3 L 8 6 M 11 3 V 13 M 8 10 L 11 13 L 14 10';
const BOX = 16;

export function SwapMark() {
  const { mark, markStroke } = theme.size.switcher;
  return (
    <Svg
      width={mark}
      height={mark}
      viewBox={`0 0 ${BOX} ${BOX}`}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Path
        d={ARROWS}
        stroke={theme.color.muted}
        strokeWidth={markStroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}
