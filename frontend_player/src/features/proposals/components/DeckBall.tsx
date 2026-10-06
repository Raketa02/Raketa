/**
 * The tennis ball — the deck's yes button's mark, drawn.
 *
 * ```
 *   ╭───────╮
 *  (  )   (  )      A circle, and the two seams: each is an arc of the ball's own circle, its
 *   ╰───────╯       centre carried four thirds of the radius to one side, drawn where it
 *                   crosses the ball. The classic pictogram, and nothing a reader has to learn.
 * ```
 *
 * ## Geometry, not a glyph — and the glyph it replaces was an emoji
 *
 * The yes drew the 🎾 as text until 2026-09-15 — the emoji the mocks pasted, in `num.levelLarge`'s
 * 26pt. An emoji is whatever the platform substitutes: Apple's ball on iOS, Google's on Android,
 * each in its own greens and its own shading on a disc whose colour it knows nothing about, and
 * clipped besides where the line box is the font size. `Tick.tsx` and `Star.tsx` draw their marks
 * for the same reason, and the design system's rule for a mark Feather does not have — which is
 * every sport — is that it is **drawn** (Part 0; [ADR-0135](../../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)
 * fixed the family, and Feather has no ball). So the ball is a path: it does not scale with
 * Dynamic Type, does not vary by platform, and takes the colour its bed is owed.
 *
 * ## One bed, one value
 *
 * It is drawn on exactly one thing, the yes disc's `coralInk`, and so has exactly one colour:
 * `surface`, **6.1 `primary`'s own white mark at 5,89:1** — the treatment the ⚡Play disc and the
 * Chats badge already take on the same fill. Not volt because a tennis ball is volt-coloured:
 * colour is picked by meaning and never by appearance (`theme.ts`), and the meaning here is *the
 * primary act's mark*. No `color` prop, for `Tick.tsx`'s reason — the bed is a fact about where
 * the mark is drawn, not a decision a caller makes.
 *
 * The box is `size.deckAnswer.ball`, the 26pt footprint the emoji had, so the disc's proportion
 * is the mock's. The stroke is 2 in the 24-unit box — Feather's own proportion, the family the ✕
 * two discs over is drawn in — so the ball is as heavy for its size as the ✕ is for its.
 *
 * **Decorative, always.** The button carries the name (`deckAnswerLabels`, *Let's play, Marek*)
 * and the ball is hidden from assistive technology as the emoji was — §E6's *"otherwise it
 * announces as 'tennis ball let's play'"*, kept by the drawing having no words at all.
 */

import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

/** The drawing's box; the ball is scaled to `size.deckAnswer.ball` from it. */
const BOX = 24;
const CENTRE = BOX / 2;
/** The ball's radius — a 2-unit stroke leaves one unit clear of the box on every side. */
const RADIUS = 10;
/** Feather's proportion: 2 in a 24 box. */
const STROKE = 2;
/**
 * How far each seam circle's centre sits from the ball's. Four thirds of the radius puts the
 * seams' ends at ±R/3 off the centre and their bulge at R/3 from it, which is the pictogram
 * everybody draws.
 */
const SEAM_OFFSET = (4 / 3) * RADIUS;

/** Where a seam crosses the ball: on the line half-way between the two centres. */
const seamX = SEAM_OFFSET / 2;
const seamY = Math.sqrt(RADIUS * RADIUS - seamX * seamX);

const at = (n: number) => n.toFixed(2);

/**
 * The three paths — the ball, then the left seam bulging right, then the right seam bulging
 * left. **Exported for the test** that holds the seams to the ball, and for nothing else.
 */
export const BALL_PATHS = {
  ball:
    `M ${at(CENTRE - RADIUS)} ${at(CENTRE)} ` +
    `A ${RADIUS} ${RADIUS} 0 1 0 ${at(CENTRE + RADIUS)} ${at(CENTRE)} ` +
    `A ${RADIUS} ${RADIUS} 0 1 0 ${at(CENTRE - RADIUS)} ${at(CENTRE)}`,
  leftSeam:
    `M ${at(CENTRE - seamX)} ${at(CENTRE - seamY)} ` +
    `A ${RADIUS} ${RADIUS} 0 0 1 ${at(CENTRE - seamX)} ${at(CENTRE + seamY)}`,
  rightSeam:
    `M ${at(CENTRE + seamX)} ${at(CENTRE - seamY)} ` +
    `A ${RADIUS} ${RADIUS} 0 0 0 ${at(CENTRE + seamX)} ${at(CENTRE + seamY)}`,
} as const;

/** The one colour, held beside the paths so the test reads the pair from one place. */
export const BALL_STROKE = theme.color.surface;

export function DeckBall() {
  const box = theme.size.deckAnswer.ball;
  return (
    <Svg
      width={box}
      height={box}
      viewBox={`0 0 ${BOX} ${BOX}`}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      {Object.values(BALL_PATHS).map((d) => (
        <Path
          key={d}
          d={d}
          stroke={BALL_STROKE}
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      ))}
    </Svg>
  );
}
