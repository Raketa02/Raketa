/**
 * **An official group's mark** — a small seal with a tick in it, beside the group's name wherever
 * a search row or the group's page draws the name (#529). It replaced the *official* tag the
 * 2026-09-27 mocks drew: the product owner asked for a mark in the word's place.
 *
 * **No bigger than a lowercase letter**, which was the ask: the box is Archivo's x-height as a
 * share of the name's own font size (`size.officialMark`), so the mark is 6,84pt beside a row's
 * `cardTitle` and 7,89 beside the header's `h2`. The row that draws the name centres it on the
 * name's line.
 *
 * **Drawn, and `Tick`'s own path** in the seal — one mark family, one tick. `mintInk` is the colour
 * the *official* tag's words were drawn in (the `ok` variant), and white on it is 5,84.
 *
 * **Hidden from a screen reader.** The row and the header both say *official* in their spoken
 * name, so the mark would be the word twice.
 */

import { View } from 'react-native';
import Svg, { G, Path } from 'react-native-svg';

import { theme, TICK_PATH, TICK_SPACE } from '@/shared/ui';

/** The seal's own units — the box it is drawn in, scaled by the `viewBox`. */
const SPACE = 24;
/** Twelve rounded points: fewer than a badge drawn large, so they still read at 7pt. */
const LOBES = 12;
/** The seal's middle radius and how far each point stands out of it — 11,8 at the tips. */
const RADIUS = 10.8;
const DEPTH = 1;
/** Enough straight steps that the seal is a curve at any size it is drawn. */
const STEPS = 96;
/** How much bigger the tick is here than in its own 12-unit box, and its stroke before that. */
const TICK_SCALE = 1.5;
const TICK_STROKE = 2;

function sealPath(): string {
  const centre = SPACE / 2;
  const points = Array.from({ length: STEPS }, (_, at) => {
    const angle = (2 * Math.PI * at) / STEPS;
    const reach = RADIUS + DEPTH * Math.cos(LOBES * angle);
    const x = centre + reach * Math.sin(angle);
    const y = centre - reach * Math.cos(angle);
    return `${x.toFixed(2)} ${y.toFixed(2)}`;
  });
  return `M ${points.join(' L ')} Z`;
}

const SEAL = sealPath();

/** The tick's box centred in the seal, then scaled about that centre. */
const TICK_PLACEMENT =
  `translate(${SPACE / 2} ${SPACE / 2}) scale(${TICK_SCALE}) ` +
  `translate(${-TICK_SPACE / 2} ${-TICK_SPACE / 2})`;

export interface OfficialMarkProps {
  /** The font size of the name the mark stands beside — what its box is a share of. */
  readonly fontSize: number;
}

export function OfficialMark({ fontSize }: OfficialMarkProps) {
  const box = fontSize * theme.size.officialMark.share;

  return (
    <View
      testID="official-mark"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={box} height={box} viewBox={`0 0 ${SPACE} ${SPACE}`}>
        <Path d={SEAL} fill={theme.color.mintInk} />
        <G transform={TICK_PLACEMENT}>
          <Path
            d={TICK_PATH}
            stroke={theme.color.surface}
            strokeWidth={TICK_STROKE}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </G>
      </Svg>
    </View>
  );
}
