/**
 * A player on the field as a **face** — the two of the three states that are not the card
 * ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.3).
 *
 * **Wide**, above 10 km across: a 24 pt face — photograph or poster — and nothing else.
 * **Closer**, at 10 and below: a 30 pt face with their level in the reading's sport beneath,
 * mono `tiny`. The corner is `PlayerPhoto`'s — a third of the box, which is the one owner of
 * that rule — inside a 2 pt `surface` ring, as mocks 5 and 8 draw every face.
 *
 * ## A button, and its press is a flight
 *
 * Every face is one accessibility element with the §26 sentence for its name — *Filip N., 1,9
 * km, Padel 2,60* — and a `button` role, because a tap on it **flies** to them and selects
 * (§7.5). The level under the face is inside the element; the poster's own sentence is inside
 * the box `PlayerPhoto` hides. The reachable area is the face grown by `hitSlop` to 6.5's 44,
 * because a 24 pt square is a target only a stylus hits.
 *
 * The face is drawn at its natural size and the field places it: it is counter-scaled by the
 * field's own transform so it is always 24 or 30 pt whatever the pinch is doing (§7.9).
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, playerPhotoRadius, theme } from '@/shared/ui';

import type { ZoomState } from '../../domain/radarGeometry';

export interface RadarFaceProps {
  readonly playerId: string;
  readonly photoUrl?: string;
  /** Their level in the reading's sport — drawn under the face in the closer state only. */
  readonly level: number;
  /** `wide` or `closer`; the card is the third state and its own component. */
  readonly state: Exclude<ZoomState, 'closest'>;
  /** The §26 sentence — composed by the field, so one label names one person in every state. */
  readonly accessibilityLabel: string;
  readonly onPress: () => void;
}

export function RadarFace({
  playerId,
  photoUrl,
  level,
  state,
  accessibilityLabel,
  onPress,
}: RadarFaceProps) {
  const size = SIZE[state];
  const slop = Math.max(0, (theme.size.minTouch - size) / 2);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      hitSlop={{ top: slop, bottom: slop, left: slop, right: slop }}
      style={({ pressed }) => [s.tile, pressed ? s.pressed : undefined]}
    >
      <View style={[s.ring, { borderRadius: playerPhotoRadius(size) + STROKE }]}>
        <PlayerPhoto playerId={playerId} photoUrl={photoUrl} box={{ kind: 'face', size }} />
      </View>
      {state === 'closer' ? <Text style={s.level}>{formatLevel(level)}</Text> : null}
    </Pressable>
  );
}

/** The face at each of its two sizes. */
const SIZE = {
  wide: theme.size.radar.faceWide,
  closer: theme.size.radar.faceCloser,
} as const satisfies Readonly<Record<RadarFaceProps['state'], number>>;

const STROKE = theme.size.radar.stroke;

/** The tile's box at each state, so the field can centre it on the point without measuring. */
export function radarFaceBox(state: RadarFaceProps['state']): { width: number; height: number } {
  const face = SIZE[state] + 2 * STROKE;
  return {
    width: face,
    height: state === 'closer' ? face + theme.space.xxs + theme.num.tiny.lineHeight : face,
  };
}

const s = StyleSheet.create({
  tile: { alignItems: 'center', gap: theme.space.xxs },
  pressed: { opacity: 0.7 },
  ring: { borderWidth: STROKE, borderColor: theme.color.surface },
  level: { ...theme.num.tiny, ...theme.tabular, color: theme.color.onDarkTiny },
});
