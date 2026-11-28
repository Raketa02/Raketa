/**
 * ***It's a game!*, in sign-in's hero** — what the swiped card becomes
 * ([#787](https://github.com/Rakieta02/Rakieta/issues/787), PRD #783; design system 12.2, mocks 7–8).
 *
 * ```
 *                 ● Rakieta                          the wordmark stays in its corner, over it
 *
 *        [KT] [  ]   vs   [AK] [KW]                  the front card's four, You bare
 *             It’s a game!                           yesWord, volt
 *   Saturday 16:00 · Ogrody 33 · Court 6 · 27 zł each   tiny, onDarkTiny
 * ```
 *
 * ## The yes screen's picture, copied, over the hero only
 *
 * The live yes screen (`proposals`' `ItsAGame`, `YesGround`, `YesTile`, `YesEntrance`) is not made
 * public and not changed: auth may not import `proposals`, for the deck's reason. So its **ground,
 * tiles and entrance are redrawn here**, as #786 redrew the card: the radial night on the yes ground's
 * two colours, the faces as posters with two letters over each — **none over You**, whose own face is
 * not the hero's to draw — the *vs*, the word in the yes screen's role, and the line under it in its
 * line's. **No buttons**: it is a picture, and a listener never meets it (the hero is hidden whole,
 * ADR-0198). Those three values are fenced to the yes screen by ADR-0167; its note of 2026-11-08
 * extends the fence to this picture of it, and to nothing else.
 *
 * **It fills the dark hero and nothing more** — `StageHero` draws it over the cards and the headline
 * and under the wordmark, and the sheet is never under it. Centred between the status bar and the
 * sheet's edge, which is where mocks 7–8 put it.
 *
 * ## Its entrance is the yes screen's
 *
 * Under a `fade`, the two sides slide in from the phone's edges and meet over `yesEntrance.sides`;
 * the *vs* and the word rise after `wordAfter`, through one `space.xxl`. The loop drives all three
 * (`useStageLoop`): `shown`, `meet`, `rise`.
 *
 * ## Its words are capped as the hero's are
 *
 * At `textMaxScale`, and the line wraps in the gutter rather than running off a narrow phone. The
 * letters shrink to their tile past it, the yes tile's own rule.
 */

import { useContext, useId } from 'react';
import { Animated, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaInsetsContext } from 'react-native-safe-area-context';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui';

import { StageFace } from './StageFace';
import { STAGE_SPLASH, type SplashFace } from './stageSplashPresentation';
import type { StageSplashMotion } from './useStageLoop';

const CAP = theme.size.stage.textMaxScale;
const TILE = theme.size.stage.splashTile;

export function StageSplash({ shown, meet, rise }: StageSplashMotion) {
  const { width } = useWindowDimensions();
  // The root's insets, as `AuthStage` reads them: none where a suite draws the screen bare.
  const top = useContext(SafeAreaInsetsContext)?.top ?? 0;
  const from = (edge: number) => meet.interpolate({ inputRange: [0, 1], outputRange: [edge, 0] });

  return (
    <Animated.View
      style={[s.splash, { opacity: shown }]}
      pointerEvents="none"
      testID="stage-splash"
    >
      <SplashGround />
      <View style={[s.column, { paddingTop: top }]}>
        <View style={s.picture}>
          <Animated.View style={{ transform: [{ translateX: from(-width) }] }}>
            <Side faces={STAGE_SPLASH.yours} />
          </Animated.View>
          <Animated.View style={{ opacity: rise }}>
            <Text style={s.vs} maxFontSizeMultiplier={CAP}>
              {STAGE_SPLASH.versus}
            </Text>
          </Animated.View>
          <Animated.View style={{ transform: [{ translateX: from(width) }] }}>
            <Side faces={STAGE_SPLASH.theirs} />
          </Animated.View>
        </View>
        <Animated.View
          testID="stage-splash-word"
          style={[
            s.words,
            {
              opacity: rise,
              transform: [
                {
                  translateY: rise.interpolate({
                    inputRange: [0, 1],
                    outputRange: [theme.space.xxl, 0],
                  }),
                },
              ],
            },
          ]}
        >
          <Text style={s.word} numberOfLines={1} maxFontSizeMultiplier={CAP}>
            {STAGE_SPLASH.word}
          </Text>
          <Text style={s.line} maxFontSizeMultiplier={CAP}>
            {STAGE_SPLASH.line}
          </Text>
        </Animated.View>
      </View>
    </Animated.View>
  );
}

/** One side — two tiles a small step apart. */
function Side({ faces }: { readonly faces: readonly SplashFace[] }) {
  return (
    <View style={s.side}>
      {faces.map((face) => (
        <StageFace
          key={face.key}
          look={face.look}
          size={TILE}
          {...(face.letters === undefined
            ? { testID: 'stage-splash-you' }
            : { letters: face.letters })}
        />
      ))}
    </View>
  );
}

/** The box the glow is drawn in — the hero's own shape, near enough, sliced to it. */
const SPACE = { width: 100, height: 90 } as const;

/**
 * The glow's centre and reach in that box, measured off mocks 7–8: the brightest ground sits in the
 * hero's middle and has fallen to the edge value by its sides and its foot.
 */
const GLOW = { cx: 50, cy: 45, r: 55 } as const;

/** The yes screen's ground, redrawn for the hero: its two colours, as a radial glow. */
function SplashGround() {
  const glow = `${useId()}-glow`;
  return (
    <View style={s.ground}>
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
  // The whole hero, under the status bar too; the picture centres below the bar's inset.
  splash: { ...StyleSheet.absoluteFillObject },
  // The edge colour is the view's own fill too, so a frame still laying out shows the night.
  ground: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.yesGroundEdge },
  column: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: theme.space.xxl,
    gap: theme.space.md,
  },
  // The yes screen's: the two sides and the *vs*, the gutter's 15 either side of it.
  picture: { flexDirection: 'row', alignItems: 'center', gap: theme.space.lg },
  side: { flexDirection: 'row', gap: theme.space.xs },
  vs: { ...theme.type.h2, color: theme.color.onDarkEyebrow },
  words: { alignItems: 'center', gap: theme.space.xs },
  word: { ...theme.type.yesWord, color: theme.color.volt },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
});
