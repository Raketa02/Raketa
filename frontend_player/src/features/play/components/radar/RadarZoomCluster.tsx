/**
 * The zoom cluster — `+`, the counter, `−` and ◉ on the field's right edge, vertically
 * centred ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.3,
 * mock 15).
 *
 * Three 34 pt squares on the cluster's own bed — `radarControl`, ink at half strength, the one
 * dark-on-dark tile in the app, measured off the mock — with the counter between the first
 * two: *18 km across*, mono `tiny`, **always drawn**, so a player always knows where they are
 * in the range. ± step to the next stop of the ladder and are **greyed at the ends**: 6.1's
 * dim for *you may not*, and the counter beside them is the note that says why. ◉ is home —
 * centred on you, the opening width, deselected.
 *
 * Spoken *Zoom in*, *Zoom out*, *Back to you*; the marks on the squares are marks and never
 * the names. The counter is a sentence a listener reaches between the two, and it is a
 * sentence rather than a live region: it changes with every pinch frame, and a region that
 * spoke on every frame would talk over the field.
 *
 * ◉ is drawn rather than typed: Archivo ships no U+25C9, and a ring with a dot is two circles.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { theme } from '@/shared/ui';

import {
  BACK_TO_YOU_LABEL,
  ZOOM_IN_LABEL,
  ZOOM_IN_MARK,
  ZOOM_OUT_LABEL,
  ZOOM_OUT_MARK,
  widthAcross,
} from '../radarPresentation';

export interface RadarZoomClusterProps {
  readonly widthKm: number;
  /** Whether there is a stop to step to, each way. Absent, the square is greyed. */
  readonly canZoomIn: boolean;
  readonly canZoomOut: boolean;
  readonly onZoomIn: () => void;
  readonly onZoomOut: () => void;
  readonly onHome: () => void;
}

export function RadarZoomCluster({
  widthKm,
  canZoomIn,
  canZoomOut,
  onZoomIn,
  onZoomOut,
  onHome,
}: RadarZoomClusterProps) {
  return (
    <View style={s.cluster} pointerEvents="box-none">
      <Square label={ZOOM_IN_LABEL} onPress={onZoomIn} disabled={!canZoomIn}>
        <Text style={s.mark}>{ZOOM_IN_MARK}</Text>
      </Square>
      <Text style={s.counter} numberOfLines={2}>
        {widthAcross(widthKm)}
      </Text>
      <Square label={ZOOM_OUT_LABEL} onPress={onZoomOut} disabled={!canZoomOut}>
        <Text style={s.mark}>{ZOOM_OUT_MARK}</Text>
      </Square>
      <Square label={BACK_TO_YOU_LABEL} onPress={onHome}>
        <HomeMark />
      </Square>
    </View>
  );
}

function Square({
  label,
  onPress,
  disabled = false,
  children,
}: {
  readonly label: string;
  readonly onPress: () => void;
  readonly disabled?: boolean;
  readonly children: React.ReactNode;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      // 34 grown to 44: 6.5's slop, bounded above and below by the neighbour's gap.
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [
        s.square,
        pressed && !disabled ? s.pressed : undefined,
        disabled ? s.disabled : undefined,
      ]}
    >
      {children}
    </Pressable>
  );
}

/** ◉ — a ring and a dot, in the square's own white. */
function HomeMark() {
  return (
    <Svg width={HOME.box} height={HOME.box} viewBox={`0 0 ${HOME.box} ${HOME.box}`}>
      <Circle
        cx={HOME.box / 2}
        cy={HOME.box / 2}
        r={HOME.ring}
        stroke={theme.color.surface}
        strokeWidth={HOME.stroke}
        fill="none"
      />
      <Circle cx={HOME.box / 2} cy={HOME.box / 2} r={HOME.dot} fill={theme.color.surface} />
    </Svg>
  );
}

/** The ◉'s own drawing: a 14 pt box, a ring of 5 at 1,5 and a dot of 2,5. */
const HOME = { box: 14, ring: 5, stroke: 1.5, dot: 2.5 } as const;

const SQUARE = theme.size.radar.cluster;

const s = StyleSheet.create({
  cluster: {
    position: 'absolute',
    right: theme.space.md,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    gap: theme.space.sm,
  },
  square: {
    width: SQUARE,
    height: SQUARE,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.radarControl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { backgroundColor: theme.color.onDarkFillPressed },
  // 6.1's dim for *you may not*: the end of the ladder, said by the counter beside it.
  disabled: { opacity: 0.4 },
  mark: { ...theme.type.h2, color: theme.color.surface },
  counter: {
    width: SQUARE + 2 * theme.space.sm,
    textAlign: 'center',
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.onDarkTiny,
  },
});
