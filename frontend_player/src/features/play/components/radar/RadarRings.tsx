/**
 * The distance rings — 1 · 2 · 5 · 10 · 20 · 50 km, centred on the viewer and moving with
 * them, each labelled at the top of its circle
 * ([`the-radar.md`](../../../../../../docs/specs/matchmaking/the-radar.md) §7.2).
 *
 * `react-native-svg` for the circles, as the spec names, and React Native `Text` for the
 * labels — a label is a word in the app's own mono face, and the SVG's text is a second font
 * stack to keep in step. Which rings are drawn is `domain/radarGeometry`'s `ringsFor`: a
 * radius of at least 26 pt and at most 3,5 field widths, so there are two or three at every
 * width and never a bullseye.
 *
 * ## Which rings is JavaScript's; where they are is the UI thread's
 *
 * The tiles ride the field's one transform; a ring cannot — a hairline scaled by twelve under a
 * pinch is a twelve-point smear until the gesture ends — so each circle's centre and radius are
 * **animated props**, read off the same three shared values the transform is drawn from
 * (`viewFromTransform`) on every frame, on the UI thread, and the label's row follows by the
 * same arithmetic. Which rings exist is a sentence — two or three labels — and changes at a
 * threshold, so that is decided in React from the width the field last spoke (ADR-0176 §2).
 *
 * The stroke is `onDarkHair` — a fold on dark, 1,61 on the ground, which is a line and not a
 * word — and the label is the on-dark eyebrow grey, 4,80 (`radarGround.test.ts`). Nothing here
 * is an element: the rings measure and say nothing a listener acts on, and the footer's
 * headline carries the count.
 */

import { StyleSheet, Text, View } from 'react-native';
import Animated, {
  useAnimatedProps,
  useAnimatedStyle,
  type SharedValue,
} from 'react-native-reanimated';
import Svg, { Circle } from 'react-native-svg';

import { theme } from '@/shared/ui';

import {
  ptPerKm,
  ringsFor,
  toScreen,
  viewFromTransform,
  type FieldBox,
  type RadarView,
} from '../../domain/radarGeometry';
import { ringLabel } from '../radarPresentation';

/** The hairline's weight, as the mocks draw it. */
const STROKE = 1;

/** The field's transform, as the field keeps it: three shared values on the UI thread. */
export interface RadarTransform {
  readonly scale: SharedValue<number>;
  readonly x: SharedValue<number>;
  readonly y: SharedValue<number>;
}

export interface RadarRingsProps {
  readonly transform: RadarTransform;
  /** The view the tiles were laid out under — what the transform is read against. */
  readonly base: RadarView;
  readonly field: FieldBox;
  /** The width the field last spoke, which is what decides which rings exist. */
  readonly widthKm: number;
}

export function RadarRings({ transform, base, field, widthKm }: RadarRingsProps) {
  const rings = ringsFor(field, widthKm);
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width="100%" height="100%">
        {rings.map((ring) => (
          <Ring key={ring.km} km={ring.km} transform={transform} base={base} field={field} />
        ))}
      </Svg>
      {rings.map((ring) => (
        <RingLabel key={ring.km} km={ring.km} transform={transform} base={base} field={field} />
      ))}
    </View>
  );
}

interface OneRingProps {
  readonly km: number;
  readonly transform: RadarTransform;
  readonly base: RadarView;
  readonly field: FieldBox;
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

/** One circle: its centre on the viewer and its radius in points, both live. */
function Ring({ km, transform, base, field }: OneRingProps) {
  const animatedProps = useAnimatedProps(() => {
    const live = viewFromTransform(
      { scale: transform.scale.value, x: transform.x.value, y: transform.y.value },
      base,
      field,
    );
    const centre = toScreen(ORIGIN, live, field);
    return { cx: centre.x, cy: centre.y, r: km * ptPerKm(field, live.widthKm) };
  });
  return (
    <AnimatedCircle
      animatedProps={animatedProps}
      stroke={theme.color.onDarkHair}
      strokeWidth={STROKE}
      fill="none"
    />
  );
}

/**
 * One label, centred over the top of its circle: a row as wide as two fields, its own centre
 * on the ring's centre line, letting the label take whatever width its words want.
 */
function RingLabel({ km, transform, base, field }: OneRingProps) {
  const placed = useAnimatedStyle(() => {
    const live = viewFromTransform(
      { scale: transform.scale.value, x: transform.x.value, y: transform.y.value },
      base,
      field,
    );
    const centre = toScreen(ORIGIN, live, field);
    const radiusPt = km * ptPerKm(field, live.widthKm);
    return {
      transform: [
        { translateX: centre.x - FIELD_SPAN },
        { translateY: centre.y - radiusPt - theme.num.tiny.lineHeight },
      ],
    };
  });
  return (
    <Animated.View style={[s.labelRow, placed]}>
      <Text style={s.label} numberOfLines={1}>
        {ringLabel(km)}
      </Text>
    </Animated.View>
  );
}

/** The viewer's kilometre point, which every ring is centred on. */
const ORIGIN = { x: 0, y: 0 } as const;

/**
 * Half the row a label is centred in. Wider than any field, so the row's centre — the ring's
 * centre line — is where the label sits whatever the label's own width; the row is not an
 * element and clips nothing.
 */
const FIELD_SPAN = 1000;

const s = StyleSheet.create({
  labelRow: { position: 'absolute', left: 0, top: 0, width: 2 * FIELD_SPAN, alignItems: 'center' },
  label: {
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.onDarkEyebrow,
  },
});
