/**
 * The generated court poster, per design-system 6.9 — the app's fourth drawn object, and
 * what a player with no photograph has instead of an empty box.
 *
 * ```
 * ground   night          the surface
 * court    onDarkHair     the lines — the same structural line the dark card uses
 * ball     onDarkTiny     one mark
 *
 * viewBox units, preserveAspectRatio="xMidYMid slice"
 * ```
 *
 * **Nothing here has a size.** The court is described once in its own units and the caller
 * gives it a box — a 90pt tile, a 27pt avatar, a full-bleed header — so there is no pixel
 * geometry to tokenise and no second copy of the drawing for the small case. The strokes
 * are in those units too, which is why a tight crop draws heavier lines: the whole picture
 * scales, lines included.
 *
 * **It varies in geometry and never in colour.** The three colours above are the whole
 * palette this component has, and there is no prop that changes one. Every colour in the
 * system already means something, so a hue chosen by a hash would be assigning meaning to
 * a hash — and the four sport colours would have a poster claim a sport its player may not
 * play.
 *
 * **It is never a person.** No face, no silhouette, no initials. A poster that gestured at
 * a human is one somebody mistakes for a photograph, in the single place a photograph
 * answers a question a drawing cannot — *do I want to play this person?*
 *
 * **The framing is the caller's**, and deliberately: the design system's contract is that
 * one player id always produces one poster, and *which* crop an id maps to is the photos
 * feature's, exactly as the confidence ring's 30% ceiling belongs to the engine.
 */

import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import Svg, { Circle, Line, Rect } from 'react-native-svg';

import { theme } from './theme';

/**
 * The court's own coordinate space. A framing is a window onto this and must lie inside it.
 *
 * Portrait, because the court is seen from above and read on a phone. The numbers are
 * arbitrary in the way a viewBox always is — what matters is that everything else in this
 * file, and every framing a caller writes, is expressed in them.
 */
export const COURT_POSTER_SPACE = { width: 100, height: 140 } as const;

/** A window onto the court, and where the one mark sits inside it. Both in court units. */
export interface CourtPosterFraming {
  readonly view: {
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
  };
  readonly ball: { readonly x: number; readonly y: number };
}

export interface CourtPosterProps {
  readonly framing: CourtPosterFraming;
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
 * The court, in `COURT_POSTER_SPACE` units.
 *
 * A singles court seen from above: the outer lines, the net across the middle, the two
 * service lines and the centre line between them. Enough for the shape to be recognised at
 * 27pt, and no more — a poster is a mark, not a diagram.
 */
const COURT = {
  outer: { x: 10, y: 10, width: 80, height: 120 },
  sideline: { left: 22, right: 78 },
  net: 70,
  service: { near: 95, far: 45 },
  centre: 50,
  stroke: 1.6,
  ball: 3.4,
} as const;

export function CourtPoster({ framing, accessibilityLabel, style }: CourtPosterProps) {
  const { view, ball } = framing;

  return (
    <View
      // One node, one label: the drawing beneath is decoration in the literal sense, and a
      // screen reader that walked into four SVG shapes would read a rectangle four times.
      accessible
      accessibilityRole="image"
      accessibilityLabel={accessibilityLabel}
      style={[s.ground, style]}
    >
      <Svg
        width="100%"
        height="100%"
        viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`}
        // `slice`, so the crop fills whatever box it is given rather than letterboxing —
        // the poster stands in for a photograph, and a photograph has no margins.
        preserveAspectRatio="xMidYMid slice"
      >
        <Rect
          x={COURT.outer.x}
          y={COURT.outer.y}
          width={COURT.outer.width}
          height={COURT.outer.height}
          fill="none"
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.sideline.left}
          y1={COURT.outer.y}
          x2={COURT.sideline.left}
          y2={COURT.outer.y + COURT.outer.height}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.sideline.right}
          y1={COURT.outer.y}
          x2={COURT.sideline.right}
          y2={COURT.outer.y + COURT.outer.height}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.outer.x}
          y1={COURT.net}
          x2={COURT.outer.x + COURT.outer.width}
          y2={COURT.net}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.sideline.left}
          y1={COURT.service.far}
          x2={COURT.sideline.right}
          y2={COURT.service.far}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.sideline.left}
          y1={COURT.service.near}
          x2={COURT.sideline.right}
          y2={COURT.service.near}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Line
          x1={COURT.centre}
          y1={COURT.service.far}
          x2={COURT.centre}
          y2={COURT.service.near}
          stroke={theme.color.onDarkHair}
          strokeWidth={COURT.stroke}
        />
        <Circle cx={ball.x} cy={ball.y} r={COURT.ball} fill={theme.color.onDarkTiny} />
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  // The ground is the view's own fill rather than a rect inside the viewBox: a crop that
  // sat outside the court would otherwise leave the paper showing through.
  ground: { flex: 1, backgroundColor: theme.color.night, overflow: 'hidden' },
});
