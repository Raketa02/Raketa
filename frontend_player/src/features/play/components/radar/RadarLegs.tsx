/**
 * The **legs** of an opened stack — a hairline from the marker to each fanned face, so a face
 * spread out from its spot still says where it came from
 * ([ADR-0177](../../../../../../docs/adr/0177-the-pinch-lets-go-where-it-is-and-a-stack-opens-on-a-tap.md)
 * §2, [`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.10).
 *
 * Drawn as the rings are, and for the rings' reason: a hairline inside the field's transform
 * would be scaled by twelve at the floor into a smear, so each leg is an SVG line in the
 * field's own points whose two ends are **animated props** read off the same three shared
 * values the transform is drawn from, on the UI thread. The stroke is the rings' `onDarkHair`.
 * Under every tile, and no element.
 */

import { StyleSheet, View } from 'react-native';
import Animated, { useAnimatedProps } from 'react-native-reanimated';
import Svg, { Line } from 'react-native-svg';

import { theme } from '@/shared/ui';

import {
  toScreen,
  viewFromTransform,
  type FieldBox,
  type KmPoint,
  type RadarView,
} from '../../domain/radarGeometry';

import type { RadarTransform } from './RadarRings';

/** One leg: from the stack's centre to a fanned face, both kilometre points. */
export interface Leg {
  readonly key: string;
  readonly from: KmPoint;
  readonly to: KmPoint;
}

export interface RadarLegsProps {
  readonly transform: RadarTransform;
  readonly base: RadarView;
  readonly field: FieldBox;
  readonly legs: readonly Leg[];
}

export function RadarLegs({ transform, base, field, legs }: RadarLegsProps) {
  if (legs.length === 0) return null;
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width="100%" height="100%">
        {legs.map((leg) => (
          <OneLeg key={leg.key} leg={leg} transform={transform} base={base} field={field} />
        ))}
      </Svg>
    </View>
  );
}

const AnimatedLine = Animated.createAnimatedComponent(Line);

function OneLeg({
  leg,
  transform,
  base,
  field,
}: {
  readonly leg: Leg;
  readonly transform: RadarTransform;
  readonly base: RadarView;
  readonly field: FieldBox;
}) {
  const animatedProps = useAnimatedProps(() => {
    const live = viewFromTransform(
      { scale: transform.scale.value, x: transform.x.value, y: transform.y.value },
      base,
      field,
    );
    const from = toScreen(leg.from, live, field);
    const to = toScreen(leg.to, live, field);
    return { x1: from.x, y1: from.y, x2: to.x, y2: to.y };
  });
  return (
    <AnimatedLine animatedProps={animatedProps} stroke={theme.color.onDarkHair} strokeWidth={1} />
  );
}
