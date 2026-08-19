/**
 * THROWAWAY PROTOTYPE — issue #11. Not production.
 *
 * `glyph(sport, seats, w, dark)` from UI spec §A5.1, in `react-native-svg`. Every
 * derivation below is the spec's, kept as a ratio of `w` exactly as written, so the
 * question "does it survive a narrower phone" is answerable by changing one number.
 *
 * The empty seat is the interesting one: a dashed coral ring on the on-night court fill.
 * ADR-0012 measures that pair at **1.17:1** and moves the stroke to `muted`. Both are
 * drawn here, switched by `fixContrast`, because the ticket asks which one ships.
 */

import Svg, { Circle, Line, Rect } from 'react-native-svg';

import { theme } from '@/shared/ui';

import type { SeatSym } from './data';

export interface CourtGlyphProps {
  readonly sport: 'padel' | 'tennis' | 'squash' | 'badminton';
  readonly seats: readonly SeatSym[];
  readonly w: number;
  readonly dark: boolean;
  /** ADR-0012's correction: the empty-seat stroke moves off coral onto a visible value. */
  readonly fixContrast: boolean;
}

export function CourtGlyph({ sport, seats, w, dark, fixContrast }: CourtGlyphProps) {
  const squash = sport === 'squash';
  const h = w * (squash ? 0.62 : 0.56);
  const p = w * 0.05;

  const fill = dark ? 'rgba(255,255,255,0.1)' : '#EEF2F1';
  const ln = dark ? 'rgba(255,255,255,0.3)' : '#D8DFDD';
  const on = dark ? '#FFFFFF' : theme.color.night;
  const emptyStroke = fixContrast ? (dark ? '#FFFFFF' : theme.color.muted) : theme.color.coral;

  const pos: readonly (readonly [number, number])[] = squash
    ? [
        [0.38 * w, 0.62 * h],
        [0.62 * w, 0.42 * h],
      ]
    : seats.length === 2
      ? [
          [0.22 * w, 0.5 * h],
          [0.78 * w, 0.5 * h],
        ]
      : [
          [0.21 * w, 0.3 * h],
          [0.21 * w, 0.72 * h],
          [0.79 * w, 0.3 * h],
          [0.79 * w, 0.72 * h],
        ];

  return (
    <Svg width={w} height={h} accessibilityRole="image">
      <Rect x={0.5} y={0.5} width={w - 1} height={h - 1} rx={4} fill={fill} stroke={ln} />
      {squash ? (
        <Line x1={p} y1={0.55 * h} x2={w - p} y2={0.55 * h} stroke={ln} strokeWidth={1.2} />
      ) : (
        <>
          <Line x1={w / 2} y1={p} x2={w / 2} y2={h - p} stroke={ln} strokeWidth={1.4} />
          <Line x1={0.3 * w} y1={p} x2={0.3 * w} y2={h - p} stroke={ln} strokeWidth={0.8} />
          <Line x1={0.7 * w} y1={p} x2={0.7 * w} y2={h - p} stroke={ln} strokeWidth={0.8} />
        </>
      )}
      {seats.map((seat, i) => {
        const at = pos[i];
        if (at === undefined) return null;
        const [cx, cy] = at;
        if (seat === 'me') {
          return <Circle key={i} cx={cx} cy={cy} r={0.082 * w} fill={theme.color.coral} />;
        }
        if (seat === 'g') {
          return (
            <Circle
              key={i}
              cx={cx}
              cy={cy}
              r={0.075 * w}
              fill="none"
              stroke={on}
              strokeWidth={1.6}
            />
          );
        }
        if (seat === null) {
          return (
            <Circle
              key={i}
              cx={cx}
              cy={cy}
              r={0.075 * w}
              fill="none"
              stroke={emptyStroke}
              strokeWidth={1.4}
              strokeDasharray="2.5 2.5"
            />
          );
        }
        return <Circle key={i} cx={cx} cy={cy} r={0.075 * w} fill={on} />;
      })}
    </Svg>
  );
}
