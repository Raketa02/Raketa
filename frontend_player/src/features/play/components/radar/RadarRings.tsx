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
 * ## Drawn from the live view, in JavaScript, and outside the field's transform
 *
 * The tiles ride the field's one native-driven transform; the rings do not, and cannot: a
 * hairline scaled by twelve under a pinch is a twelve-point smear until the gesture ends.
 * So this layer is re-drawn from the live view on every move — a handful of circles and
 * labels, which is cheap — and sits under the tiles rather than among them. During a flight it
 * follows the JavaScript-side progress the field keeps beside its native one; the two agree
 * on the same easing and land together.
 *
 * The stroke is `onDarkHair` — a fold on dark, 1,61 on the ground, which is a line and not a
 * word — and the label is the on-dark eyebrow grey, 4,80 (`radarGround.test.ts`). Nothing here
 * is an element: the rings measure and say nothing a listener acts on, and the footer's
 * headline carries the count.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { theme } from '@/shared/ui';

import type { Ring, ScreenPoint } from '../../domain/radarGeometry';
import { ringLabel } from '../radarPresentation';

/** The hairline's weight, as the mocks draw it. */
const STROKE = 1;

export interface RadarRingsProps {
  /** The viewer's position on the field, under the live view. */
  readonly centre: ScreenPoint;
  readonly rings: readonly Ring[];
}

export function RadarRings({ centre, rings }: RadarRingsProps) {
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width="100%" height="100%">
        {rings.map((ring) => (
          <Circle
            key={ring.km}
            cx={centre.x}
            cy={centre.y}
            r={ring.radiusPt}
            stroke={theme.color.onDarkHair}
            strokeWidth={STROKE}
            fill="none"
          />
        ))}
      </Svg>
      {rings.map((ring) => (
        // Centred over the top of the circle: a row as wide as two fields, its own centre on
        // the ring's centre line, letting the label take whatever width its words want.
        <View
          key={ring.km}
          style={[
            s.labelRow,
            {
              left: centre.x - FIELD_SPAN,
              width: 2 * FIELD_SPAN,
              top: centre.y - ring.radiusPt - theme.num.tiny.lineHeight,
            },
          ]}
        >
          <Text style={s.label} numberOfLines={1}>
            {ringLabel(ring.km)}
          </Text>
        </View>
      ))}
    </View>
  );
}

/**
 * Half the row a label is centred in. Wider than any field, so the row's centre — the ring's
 * centre line — is where the label sits whatever the label's own width; the row is not an
 * element and clips nothing.
 */
const FIELD_SPAN = 1000;

const s = StyleSheet.create({
  labelRow: { position: 'absolute', alignItems: 'center' },
  label: {
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.onDarkEyebrow,
  },
});
