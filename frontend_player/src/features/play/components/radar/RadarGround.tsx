/**
 * The radar's ground — the app's **third** dark surface, a field rather than a card or a
 * screen ([ADR-0174](../../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, design-system Part 16 2026-09-16).
 *
 * `YesGround`'s drawing on the radar's two colours: one radial glow from `radarGroundCentre`
 * out to `radarGroundEdge`, in a box sliced to the pane, so the field is brightest a little
 * above the middle — where the viewer's tile sits at home — and darkest at the footer. Mock 1
 * draws it so, and the two values were measured off it (`theme.ts`, `radarGround.test.ts`).
 * It lies under the whole pane — the header, the field, the cluster and the footer — because
 * the mock draws the *Deck | Radar* toggle over the night too, and the mocks are the design.
 *
 * Its own file rather than a prop on `YesGround` because the two are two records: the yes
 * screen's ground was fenced *for this screen only* and the next dark surface was to argue for
 * its own, which ADR-0174 §7 does. The drawing is the same twelve lines; the colours and the
 * glow's centre are not shared, so neither can move the other.
 */

import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui';

/** The box the glow is drawn in — a portrait, sliced to the pane. */
const SPACE = { width: 100, height: 200 } as const;

/** The glow's centre and reach in that box: a little above the middle, as the viewer is. */
const GLOW = { cx: 50, cy: 84, r: 130 } as const;

export function RadarGround() {
  const glow = `${useId()}-glow`;

  return (
    <View
      style={s.ground}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${SPACE.width} ${SPACE.height}`}
        preserveAspectRatio="xMidYMid slice"
      >
        <Defs>
          <RadialGradient
            id={glow}
            cx={GLOW.cx}
            cy={GLOW.cy}
            r={GLOW.r}
            gradientUnits="userSpaceOnUse"
          >
            <Stop offset="0" stopColor={theme.color.radarGroundCentre} />
            <Stop offset="1" stopColor={theme.color.radarGroundEdge} />
          </RadialGradient>
        </Defs>
        <Rect x={0} y={0} width={SPACE.width} height={SPACE.height} fill={`url(#${glow})`} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  // The edge colour is the view's own fill too, so a frame still laying out shows the night
  // and never the paper behind it.
  ground: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.radarGroundEdge },
});
