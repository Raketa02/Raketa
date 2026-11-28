/**
 * **The drawn ▲ / ▼** — a place moved up or down this week, on the Rankings page's chip (`RankChip`)
 * and on a Top 10 card ([#805](https://github.com/Rakieta02/Rakieta/issues/805)). Drawn, never a
 * character (§30's preamble: Archivo ships neither triangle), in a 10-unit box at the size and ink
 * each caller hands it. Hidden with the chip it stands in: the row or the card names the move.
 */

import Svg, { Path } from 'react-native-svg';

/** The triangles' own 10-unit box. */
const SPACE = 10;
const UP = 'M5 1.5 L9 8.5 L1 8.5 Z';
const DOWN = 'M1 1.5 L9 1.5 L5 8.5 Z';

export function MoveMark({
  up,
  size,
  ink,
  testID,
}: {
  readonly up: boolean;
  readonly size: number;
  readonly ink: string;
  readonly testID?: string;
}) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox={`0 0 ${SPACE} ${SPACE}`}
      {...(testID === undefined ? {} : { testID })}
    >
      <Path d={up ? UP : DOWN} fill={ink} />
    </Svg>
  );
}
