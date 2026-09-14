/**
 * **The yes screen's ground** — the app's one dark screen, drawn as a radial glow
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2).
 *
 * Two colours and nothing else: the glow's centre and its edge, both the theme's and both
 * recorded as *for this screen only*. Drawn with the SVG the poster already uses rather than a
 * second dependency, and drawn in a fixed box **sliced** to whatever screen it is given, exactly
 * as `CourtPoster` fills its box — so the glow needs no measurement of the phone, and a wide
 * phone crops the picture's sides rather than stretching its circle into an ellipse.
 *
 * **Where the glow sits is measured off the mocks**: the brightest ground pixel is at 36–37 % of
 * the height in all three, which is about where the tiles stand, and the fall-off reaches the
 * edge value roughly six tenths of the height away. Hence a 100 × 200 box with the centre at
 * `(50, 72)` and a radius of 120.
 *
 * It says nothing to a screen reader: the ground is a picture behind a screen whose whole
 * sentence is the header's.
 */

import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui';

/** The box the glow is drawn in — a portrait twice as tall as it is wide, sliced to the screen. */
const SPACE = { width: 100, height: 200 } as const;

/** The glow's centre and reach, in that box — see the module note. */
const GLOW = { cx: 50, cy: 72, r: 120 } as const;

export function YesGround() {
  // Per instance, as the poster's is: an id composed from anything else could collide the day
  // two of these are on one screen, and React's own uniqueness cannot.
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
            <Stop offset="0" stopColor={theme.color.yesGroundCentre} />
            <Stop offset="1" stopColor={theme.color.yesGroundEdge} />
          </RadialGradient>
        </Defs>
        <Rect x={0} y={0} width={SPACE.width} height={SPACE.height} fill={`url(#${glow})`} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  // The edge colour is also the view's own fill, so a frame that is still laying out shows the
  // dark ground rather than the paper behind it — `CourtPoster`'s own line.
  ground: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.yesGroundEdge },
});
