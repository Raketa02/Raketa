/**
 * The confidence ring, per design-system 7.8 — the app's second drawn object, and the
 * only component that needs vector drawing.
 *
 * ```
 * ring     size.ring 72        stroke size.ringStroke 6, butt caps
 *                              starts at 12 o'clock, sweeps clockwise
 * track    full circle         color.onDarkHair
 * arc      0 → value           color.volt          ← 10,60:1 on night
 * ceiling  at the ceiling      size.ringTick 2, in color.volt, spanning the stroke
 *                              and overshooting size.ringTickOvershoot 3 outward
 * value    num.xl mono, tabular, #fff, optically centred in the ring
 * label    type.eyebrow beneath — repainted .52 by the dark card
 * ```
 *
 * **It appears only inside a dark card**, because `volt` is legible nowhere else.
 *
 * **The scale is always the full 0–100**, exactly as the level bar's is always 1,00–5,00,
 * and the ceiling tick is what makes that survivable. Onboarding cannot produce confidence
 * above its ceiling — the questionnaire is the entire evidence surface — so every player
 * leaves it with an arc covering under a third of the circle, and a bare arc that short
 * reads as failure. The tick turns "nearly empty" into *as far as a questionnaire can
 * prove*, and when matches later push confidence to 75% the same ring means the same thing
 * with the tick simply sitting behind the arc.
 *
 * **The ceiling is told, never known.** Where it sits is a domain constant belonging to
 * whoever draws the ring; this component has no opinion about why.
 *
 * **Butt caps, not round.** A round cap adds half a stroke width at each end, which on a
 * 3% arc is most of the arc — it would inflate the smallest values, exactly where the
 * number is least certain, and overhang the tick. The arc's drawn length is its value.
 *
 * **The tick is radial where the arc is tangential.** A difference in shape, not in
 * colour, which is what Part 13 requires: the mark survives being unable to tell volt from
 * white.
 *
 * **The ring is not pressable.** Its meaning is carried by the adjacent information mark
 * and its popover; it has no press state and no touch target of its own. Its role is
 * `progressbar`, and its accessible name has to state both numbers — the confidence
 * reached and the ceiling that applies — because the tick is invisible to a screen reader.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';

import { theme } from './theme';

const SCALE = 100;

const ring = theme.size.ring;
const stroke = theme.size.ringStroke;
const overshoot = theme.size.ringTickOvershoot;

/** The tick overshoots the stroke outward, so the drawing box is wider than the ring. */
const BOX = ring + 2 * overshoot;
const CENTRE = BOX / 2;
const RADIUS = (ring - stroke) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export interface ConfidenceRingProps {
  /** 0–100. Drawn on the full scale, never rescaled to the ceiling. */
  readonly value: number;
  /** Where the tick sits, on the same 0–100 scale. */
  readonly ceiling: number;
  /** The eyebrow beneath, drawn uppercase. */
  readonly label: string;
  /** Names both numbers — the value reached and the ceiling that applies. */
  readonly accessibilityLabel: string;
}

export function ConfidenceRing({ value, ceiling, label, accessibilityLabel }: ConfidenceRingProps) {
  const held = Math.min(Math.max(value, 0), SCALE);
  const drawn = CIRCUMFERENCE * (held / SCALE);
  const tick = radial(ceiling);

  return (
    <View style={s.ring}>
      <View
        // One element, not a drawing with a number floating over it: `accessible` is what
        // makes the role and the value reach a screen reader as one thing.
        accessible
        accessibilityRole="progressbar"
        accessibilityLabel={accessibilityLabel}
        accessibilityValue={{ min: 0, max: SCALE, now: Math.round(held) }}
      >
        <Svg width={BOX} height={BOX}>
          <Circle
            cx={CENTRE}
            cy={CENTRE}
            r={RADIUS}
            stroke={theme.color.onDarkHair}
            strokeWidth={stroke}
            fill="none"
          />
          <Circle
            cx={CENTRE}
            cy={CENTRE}
            r={RADIUS}
            stroke={theme.color.volt}
            strokeWidth={stroke}
            strokeLinecap="butt"
            strokeDasharray={`${drawn} ${CIRCUMFERENCE}`}
            fill="none"
            // 12 o'clock, sweeping clockwise: SVG's zero is 3 o'clock.
            transform={`rotate(-90 ${CENTRE} ${CENTRE})`}
          />
          <Line
            x1={tick.x1}
            y1={tick.y1}
            x2={tick.x2}
            y2={tick.y2}
            stroke={theme.color.volt}
            strokeWidth={theme.size.ringTick}
          />
        </Svg>

        {/* Over the drawing rather than inside it, so the figure scales with the OS text
            setting like every other number on the screen. */}
        <View style={s.centre} pointerEvents="none">
          <Text style={s.value}>{`${Math.round(held)}%`}</Text>
        </View>
      </View>

      <Text style={s.label}>{label}</Text>
    </View>
  );
}

/** The ceiling tick: radial, spanning the stroke and overshooting it outward. */
function radial(percent: number) {
  const angle = 2 * Math.PI * (Math.min(Math.max(percent, 0), SCALE) / SCALE);
  const inner = RADIUS - stroke / 2;
  const outer = RADIUS + stroke / 2 + overshoot;
  return {
    x1: CENTRE + inner * Math.sin(angle),
    y1: CENTRE - inner * Math.cos(angle),
    x2: CENTRE + outer * Math.sin(angle),
    y2: CENTRE - outer * Math.cos(angle),
  };
}

const s = StyleSheet.create({
  ring: { alignItems: 'center', gap: theme.space.xxs },
  centre: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: { ...theme.num.xl, ...theme.tabular, color: theme.color.surface },
  label: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
  },
});
