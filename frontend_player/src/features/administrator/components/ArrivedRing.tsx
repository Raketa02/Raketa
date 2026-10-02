/**
 * **How much of the group has arrived, drawn as a ring** — the players card's right side on an
 * official group's page (#529). The product owner's: an empty circle, its line filling clockwise as
 * players join, round the percentage it stands for — the players over the group size the
 * Administrator gave the group (`whatsAppShare`).
 *
 * The confidence ring's geometry on a light card (design-system 7.8 is dark-only, because of volt):
 * a full `line2` track, a `mint` arc from 12 o'clock, **butt caps** for 7.8's reason — a round cap
 * inflates the smallest values, where a group has only begun — and the figure over the drawing so it
 * scales with the OS text size. **The arc stops at full; the figure does not**: a group size limits
 * nothing (ADR-0183 §3), so a crowd past it reads *117%* round a closed ring.
 *
 * It speaks nothing of its own. The card it sits in is one element, and says the share in words.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { formatPercent } from '@/shared/formatting/ratingFormat';
import { theme } from '@/shared/ui';

const { diameter, stroke } = theme.size.arrivedRing;
const CENTRE = diameter / 2;
const RADIUS = (diameter - stroke) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/** `share` is a percentage, and may pass 100. */
export function ArrivedRing({ share }: { readonly share: number }) {
  const drawn = CIRCUMFERENCE * (Math.min(Math.max(share, 0), 100) / 100);

  return (
    <View
      testID="arrived-ring"
      style={s.ring}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={diameter} height={diameter}>
        <Circle
          cx={CENTRE}
          cy={CENTRE}
          r={RADIUS}
          stroke={theme.color.line2}
          strokeWidth={stroke}
          fill="none"
        />
        {drawn > 0 ? (
          <Circle
            testID="arrived-arc"
            cx={CENTRE}
            cy={CENTRE}
            r={RADIUS}
            stroke={theme.color.mint}
            strokeWidth={stroke}
            strokeLinecap="butt"
            strokeDasharray={`${drawn} ${CIRCUMFERENCE}`}
            fill="none"
            // 12 o'clock, sweeping clockwise: SVG's zero is 3 o'clock.
            transform={`rotate(-90 ${CENTRE} ${CENTRE})`}
          />
        ) : null}
      </Svg>
      <View style={s.centre} pointerEvents="none">
        <Text style={s.figure}>{formatPercent(share)}</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  ring: { width: diameter, height: diameter },
  centre: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center' },
  // A share is a figure: mono and tabular (1.4), in `ink` as the card's count is.
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
