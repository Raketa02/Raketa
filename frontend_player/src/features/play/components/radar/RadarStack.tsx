/**
 * A **stack** on the field — players too close to tell apart at the floor, folded into one
 * marker that says how many
 * ([ADR-0177](../../../../../../docs/adr/0177-the-pinch-lets-go-where-it-is-and-a-stack-opens-on-a-tap.md)
 * §2, [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.10).
 *
 * A face-sized square — the closer face's 30 pt inside the same 2 pt ring every face wears, at
 * the photo's own corner — on paper, with the count in mono `num.s`: a number where a face
 * would be, which is the one thing on the field that is not a person. **Open, it is volt**: a
 * fill anywhere, and 13,96 under ink, so the marker whose players are spread around it reads as
 * the thing that was pressed.
 *
 * ## A button whose press opens or folds
 *
 * One accessibility element, a `button`, named *3 players close together*, with the hint
 * saying what the press does — spread them, or fold them back — and `expanded` carrying which.
 * The reachable area is the square grown to 6.5's 44. The field places it at the stack's
 * centre and counter-scales it like every tile, so it is always 30 pt.
 */

import { Pressable, StyleSheet, Text } from 'react-native';

import { playerPhotoRadius, theme } from '@/shared/ui';

import { stackCount, stackHint, stackLabel } from '../radarPresentation';

export interface RadarStackProps {
  readonly members: number;
  readonly open: boolean;
  readonly onPress: () => void;
}

export function RadarStack({ members, open, onPress }: RadarStackProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={stackLabel(members)}
      accessibilityHint={stackHint(open)}
      accessibilityState={{ expanded: open }}
      onPress={onPress}
      hitSlop={{ top: SLOP, bottom: SLOP, left: SLOP, right: SLOP }}
      style={({ pressed }) => [
        s.square,
        open ? s.open : undefined,
        pressed ? s.pressed : undefined,
      ]}
      testID="radar-stack"
    >
      <Text style={s.count}>{stackCount(members)}</Text>
    </Pressable>
  );
}

const SIZE = theme.size.radar.faceCloser;
const STROKE = theme.size.radar.stroke;
const SLOP = Math.max(0, (theme.size.minTouch - SIZE - 2 * STROKE) / 2);

/** The marker's box, so the field can centre it on the stack's centre without measuring. */
export const RADAR_STACK_BOX = { width: SIZE + 2 * STROKE, height: SIZE + 2 * STROKE } as const;

const s = StyleSheet.create({
  square: {
    width: SIZE + 2 * STROKE,
    height: SIZE + 2 * STROKE,
    borderWidth: STROKE,
    borderColor: theme.color.surface,
    borderRadius: playerPhotoRadius(SIZE) + STROKE,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  open: { backgroundColor: theme.color.volt },
  pressed: { opacity: 0.7 },
  count: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
