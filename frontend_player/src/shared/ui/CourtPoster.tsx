/**
 * The generated court poster, per design-system 6.9 — the app's fourth drawn object, and
 * what a player with no photograph has instead of an empty box.
 *
 * ```
 * ground   a POSTER_HUES pair    the light stop to the dark, on one hue
 * figure   ink                   one of three poses, flat, at one value
 * ball     volt                  one mark, in the one hue a poster can never be
 *
 * viewBox units, preserveAspectRatio="xMidYMid slice"
 * ```
 *
 * **Nothing here has a size.** The poster is described once in its own units and the caller
 * gives it a box — a 90pt tile, a 27pt avatar, a full-bleed header — so there is no pixel
 * geometry to tokenise and no second copy of the drawing for the small case. The strokes are
 * in those units too: the whole picture scales, limbs included.
 *
 * **It draws a player, and never a likeness** (ADR-0134 §1). A flat silhouette in a single
 * value, with no second value, no gradient on the figure, no skin tone, no hair, **no face
 * and no facial feature of any kind**. That constraint is the line: the moment the figure
 * gains a face, a second value or a likeness, it is a picture of a person again and the
 * record that allows it here does not cover it. The one prop it holds is a racket, which is
 * true of every player on this platform, and it carries nothing that names a Sport.
 *
 * **The pose is not a fact, and nothing may read it as one** (§2). It is chosen by a hash: a
 * player whose pose is `serve` is not a server, and the handedness a pose appears to show is
 * not theirs. A poster is shown and never read.
 *
 * **The hue is one of sixteen designed values, never a hue a hash invented** (§3). Every one
 * is 25° from every hue the palette has named, so a poster cannot claim a Sport its player
 * may not play; `POSTER_HUES` is the whole vocabulary this component has, and `hue` is the
 * one colour prop in this design system that does not come from `theme.color`. Its two stops
 * are ONE hue — sRGB-HSL measures up to 3,3° between them, which is the two colour spaces
 * disagreeing and not a shift anybody drew.
 *
 * **The choice is the feature's, not the theme's.** The design system's contract is that one
 * player id always produces one poster; *which* hue and pose an id maps to belongs to the
 * feature, exactly as the confidence ring's 30% ceiling belongs to the engine.
 */

import { useId } from 'react';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import Svg, { Circle, Defs, Ellipse, G, LinearGradient, Path, Rect, Stop } from 'react-native-svg';

import { theme, type PosterHue } from './theme';

/**
 * The three poses, and the whole of the set.
 *
 * Three because the specification drew three, and because sixteen hues by three poses is the
 * forty-eight distinct posters the retired eight-framings-by-six-balls set produced. A fourth
 * is a drawing, not a constant.
 */
export const COURT_POSTER_POSES = ['forehand', 'serve', 'lunge'] as const;

export type CourtPosterPose = (typeof COURT_POSTER_POSES)[number];

/**
 * Everything a player id decides about a poster, and the whole of it.
 *
 * One type rather than two loose props, because the pair travels together everywhere: the
 * feature derives it, `PhotoTile` passes it on, and this component draws it. It lives here
 * for the reason the retired `CourtPosterFraming` did — the design system owns the
 * vocabulary, and the feature owns which member of it a given id gets.
 */
export interface CourtPosterLook {
  /**
   * One of the sixteen. A member of `POSTER_HUES` by type, so the only way to draw a poster
   * in a colour nobody designed is to add one to that list, where the bounds are held.
   */
  readonly hue: PosterHue;
  readonly pose: CourtPosterPose;
}

export interface CourtPosterProps extends CourtPosterLook {
  /**
   * Required, and it must say the picture is generated.
   *
   * Nobody should have to see a poster to know they are not looking at the player, and a
   * drawing that announced itself as a photo would be the one lie this component could
   * tell. It has no default because there is no wording that is right on both a tile and
   * an avatar.
   */
  readonly accessibilityLabel: string;
  readonly style?: StyleProp<ViewStyle>;
}

/**
 * The square the poster is drawn in, and the composition is fixed and whole inside it.
 *
 * Square rather than the retired court's portrait, because the caller's boxes run from a 27pt
 * avatar to a full-bleed header and `slice` crops whichever axis is short — a composition
 * centred in a square loses the least of itself in both directions.
 */
const SPACE = 100;

/**
 * The figure's dimensions, in poster units — the head's RADIUS, then three line weights.
 *
 * The weights are heavier than the specification's, and that is the 27pt case: at a 27pt
 * avatar one unit is a quarter of a point, and the difference between a silhouette and a
 * smudge is whether the limbs survive the scaling. Nothing else about the drawing changes
 * with size, so this is where the small case is paid for.
 */
const FIGURE = { headRadius: 7.5, body: 6, arm: 5.4, racket: 3.6 } as const;

/** One mark, and the one hue a poster can never be — which is why it can be the mark. */
const BALL = { x: 88, y: 68, r: 3.4 } as const;

interface Pose {
  readonly head: { readonly x: number; readonly y: number };
  /** Torso and both legs in one path, so the figure has one silhouette and not three. */
  readonly body: string;
  readonly arms: readonly [string, string];
  readonly racket: {
    readonly x: number;
    readonly y: number;
    readonly rx: number;
    readonly ry: number;
    readonly rotation: number;
  };
}

/**
 * The three poses, drawn to 6.9's clause rather than copied from the specification.
 *
 * Each is a head, a torso-and-legs path, two arms and a racket — five marks in one value,
 * with no facial feature to omit because there is no face to draw one on. The racket is a
 * stroked ellipse rather than a filled one: a filled oval at the end of an arm reads as a
 * paddle, and the strings are the thing that says racket at any size.
 */
const POSES: Readonly<Record<CourtPosterPose, Pose>> = {
  forehand: {
    head: { x: 58, y: 31 },
    body: 'M55,40 C50,50 48,59 50,71 L45,93 M50,71 L61,91',
    arms: ['M54,45 L76,35', 'M54,49 L42,59'],
    racket: { x: 82, y: 31, rx: 7.2, ry: 10.2, rotation: 28 },
  },
  serve: {
    head: { x: 50, y: 27 },
    body: 'M50,36 C48,49 48,59 50,71 L42,93 M50,71 L58,92',
    arms: ['M50,39 L62,17', 'M50,47 L38,53'],
    racket: { x: 66, y: 10, rx: 6.6, ry: 9.6, rotation: 18 },
  },
  lunge: {
    head: { x: 45, y: 35 },
    body: 'M47,44 C51,54 55,61 61,67 L57,93 M61,67 L81,81',
    arms: ['M49,49 L27,55', 'M51,51 L69,45'],
    racket: { x: 19, y: 56, rx: 7.2, ry: 10.2, rotation: -62 },
  },
};

export function CourtPoster({ hue, pose, accessibilityLabel, style }: CourtPosterProps) {
  // A PER-INSTANCE value, and never one derived from data. The prototype composed this from
  // the player id and the width, so a screen drawing one person twice at one size emitted
  // duplicate ids; composing it from the id, the width AND the height is the same bug one
  // screen further out. React's own uniqueness is the fix that cannot be re-derived wrongly.
  const ground = `${useId()}-ground`;
  const figure = POSES[pose];

  return (
    <View
      // One node, one label: the drawing beneath is decoration in the literal sense, and a
      // screen reader that walked into six SVG shapes would read a rectangle six times.
      accessible
      accessibilityRole="image"
      accessibilityLabel={accessibilityLabel}
      // The ground is also the view's own fill, so a box that is still laying out shows the
      // poster's dark end rather than the paper behind it.
      style={[s.ground, { backgroundColor: hue.dark }, style]}
    >
      <Svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${SPACE} ${SPACE}`}
        // `slice`, so the drawing fills whatever box it is given rather than letterboxing —
        // the poster stands in for a photograph, and a photograph has no margins.
        preserveAspectRatio="xMidYMid slice"
      >
        <Defs>
          <LinearGradient id={ground} x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={hue.light} />
            <Stop offset="1" stopColor={hue.dark} />
          </LinearGradient>
        </Defs>
        <Rect x={0} y={0} width={SPACE} height={SPACE} fill={`url(#${ground})`} />

        <G fill="none" stroke={theme.color.ink} strokeLinecap="round" strokeLinejoin="round">
          <Circle
            cx={figure.head.x}
            cy={figure.head.y}
            r={FIGURE.headRadius}
            fill={theme.color.ink}
            stroke="none"
          />
          <Path d={figure.body} strokeWidth={FIGURE.body} />
          {figure.arms.map((arm) => (
            <Path key={arm} d={arm} strokeWidth={FIGURE.arm} />
          ))}
          <Ellipse
            cx={figure.racket.x}
            cy={figure.racket.y}
            rx={figure.racket.rx}
            ry={figure.racket.ry}
            rotation={figure.racket.rotation}
            originX={figure.racket.x}
            originY={figure.racket.y}
            strokeWidth={FIGURE.racket}
          />
        </G>

        <Circle cx={BALL.x} cy={BALL.y} r={BALL.r} fill={theme.color.volt} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  ground: { flex: 1, overflow: 'hidden' },
});
