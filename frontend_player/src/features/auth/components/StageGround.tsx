/**
 * **The stage's ground** — the hero's flat night, and the glow at its foot where the sheet meets it
 * ([#784](https://github.com/Raketa02/Raketa/issues/784); design system 12.2, Part 16 2026-11-08).
 *
 * Two colours and nothing else, both the theme's and both fenced as the stage's alone:
 * `stageGround`, the one flat value mock 1 draws from the status bar to the sheet, and `stageGlow`,
 * the light under the middle of the screen at the sheet's edge. Drawn with the SVG the yes screen's
 * ground already uses rather than a second dependency, in a 100 × 100 box **stretched** to the
 * hero, because the glow is a share of the hero's width and height rather than a circle: measured
 * off mock 1, it reaches 0,45 of the width either side of the centre and a tenth of the hero's
 * height above the sheet.
 *
 * It says nothing to a screen reader: the hero around it is hidden whole (ADR-0198).
 */

import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui';

/** The box the glow is drawn in, stretched to the hero. */
const SPACE = { width: 100, height: 100 } as const;

/** The glow's centre and reach in that box — centred at the foot; see the module note. */
const GLOW = { cx: 50, cy: 100, rx: 45, ry: 10 } as const;

export function StageGround() {
  // Per instance, as the yes ground's is: React's own uniqueness, so two never collide.
  const glow = `${useId()}-glow`;

  return (
    <View style={s.ground} pointerEvents="none">
      <Svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${SPACE.width} ${SPACE.height}`}
        preserveAspectRatio="none"
      >
        <Defs>
          <RadialGradient
            id={glow}
            cx={GLOW.cx}
            cy={GLOW.cy}
            fx={GLOW.cx}
            fy={GLOW.cy}
            rx={GLOW.rx}
            ry={GLOW.ry}
            gradientUnits="userSpaceOnUse"
          >
            <Stop offset="0" stopColor={theme.color.stageGlow} />
            <Stop offset="1" stopColor={theme.color.stageGround} />
          </RadialGradient>
        </Defs>
        <Rect x={0} y={0} width={SPACE.width} height={SPACE.height} fill={`url(#${glow})`} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  // The ground is also the view's own fill, so a frame still laying out shows the night rather
  // than whatever is behind it — the yes ground's own line.
  ground: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.stageGround },
});
