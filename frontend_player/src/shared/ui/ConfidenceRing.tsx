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
 * **The ceiling is told, never known**, and it may not be told at all. Where it sits belongs
 * to whoever draws the ring; this component has no opinion about why. Given none, it draws
 * **no tick** rather than a default one — a tick is a claim about what could have been
 * proved, and a caller that cannot make that claim must not have one drawn for it.
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
 * Where there is no tick there is no second number, and the name says the one there is.
 *
 * ## Two more homes, and the figure they print
 *
 * The You tab draws the same ring twice more, still inside a dark card (Part 16, 2026-09-17 —
 * ADR-0179 §1, §2): the Player Score in the header card at `ringSm`, with `SCORE` beneath, and
 * on the reliability screen at `ringLg`, with the band's word beside it (#660) and nothing
 * beneath. A Player Score is *out of a hundred* and not a percentage, so the caller may hand
 * the figure to print — `92` — where the default is the confidence's `92%`. The size changes
 * the diameter and nothing else: one stroke, one tick, one overshoot, one type role for the
 * figure, so the three are one ring drawn three sizes rather than three rings.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';

import { theme } from './theme';

const SCALE = 100;

const stroke = theme.size.ringStroke;
const overshoot = theme.size.ringTickOvershoot;

/** The three diameters the ring is drawn at — 7.8's, and the You tab's two (Part 16). */
export type ConfidenceRingSize = 'md' | 'sm' | 'lg';

const DIAMETER: Readonly<Record<ConfidenceRingSize, number>> = {
  md: theme.size.ring,
  sm: theme.size.ringSm,
  lg: theme.size.ringLg,
};

interface Geometry {
  /** The tick overshoots the stroke outward, so the drawing box is wider than the ring. */
  readonly box: number;
  readonly centre: number;
  readonly radius: number;
  readonly circumference: number;
}

function geometry(size: ConfidenceRingSize): Geometry {
  const ring = DIAMETER[size];
  const box = ring + 2 * overshoot;
  const radius = (ring - stroke) / 2;
  return { box, centre: box / 2, radius, circumference: 2 * Math.PI * radius };
}

export interface ConfidenceRingProps {
  /** 0–100. Drawn on the full scale, never rescaled to the ceiling. */
  readonly value: number;
  /** Where the tick sits, on the same 0–100 scale. Absent draws no tick. */
  readonly ceiling?: number;
  /** The eyebrow beneath, drawn uppercase. Absent draws nothing beneath — see the module note. */
  readonly label?: string;
  /**
   * What is printed in the centre. Defaults to the value as a percentage, which is what a
   * confidence is; a Player Score is out of a hundred and hands its bare figure.
   */
  readonly figure?: string;
  /** Which of the three diameters. 7.8's own by default. */
  readonly size?: ConfidenceRingSize;
  /** Names every number drawn — the value reached, and the ceiling if there is one. */
  readonly accessibilityLabel: string;
}

export function ConfidenceRing({
  value,
  ceiling,
  label,
  figure,
  size = 'md',
  accessibilityLabel,
}: ConfidenceRingProps) {
  const { box, centre, radius, circumference } = geometry(size);
  const held = Math.min(Math.max(value, 0), SCALE);
  const drawn = circumference * (held / SCALE);
  const tick = ceiling === undefined ? undefined : radial(ceiling, geometry(size));

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
        <Svg width={box} height={box}>
          <Circle
            cx={centre}
            cy={centre}
            r={radius}
            stroke={theme.color.onDarkHair}
            strokeWidth={stroke}
            fill="none"
          />
          <Circle
            cx={centre}
            cy={centre}
            r={radius}
            stroke={theme.color.volt}
            strokeWidth={stroke}
            strokeLinecap="butt"
            strokeDasharray={`${drawn} ${circumference}`}
            fill="none"
            // 12 o'clock, sweeping clockwise: SVG's zero is 3 o'clock.
            transform={`rotate(-90 ${centre} ${centre})`}
          />
          {tick === undefined ? null : (
            <Line
              x1={tick.x1}
              y1={tick.y1}
              x2={tick.x2}
              y2={tick.y2}
              stroke={theme.color.volt}
              strokeWidth={theme.size.ringTick}
            />
          )}
        </Svg>

        {/* Over the drawing rather than inside it, so the figure scales with the OS text
            setting like every other number on the screen. */}
        <View style={s.centre} pointerEvents="none">
          <Text style={s.value}>{figure ?? `${Math.round(held)}%`}</Text>
        </View>
      </View>

      {label === undefined ? null : <Text style={s.label}>{label}</Text>}
    </View>
  );
}

/** The ceiling tick: radial, spanning the stroke and overshooting it outward. */
function radial(percent: number, { centre, radius }: Geometry) {
  const angle = 2 * Math.PI * (Math.min(Math.max(percent, 0), SCALE) / SCALE);
  const inner = radius - stroke / 2;
  const outer = radius + stroke / 2 + overshoot;
  return {
    x1: centre + inner * Math.sin(angle),
    y1: centre - inner * Math.cos(angle),
    x2: centre + outer * Math.sin(angle),
    y2: centre - outer * Math.cos(angle),
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
