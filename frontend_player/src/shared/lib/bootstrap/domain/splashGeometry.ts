/**
 * **The splash's geometry** — where everything the drawn splash places stands, on any phone
 * ([ADR-0209](../../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md);
 * `docs/specs/splash-screen/`, decision log §4).
 *
 * One pure function from the full screen and the wordmark's font constants to the lockup: its box,
 * each letter's place, the floor and the dot. No React and no device access, so it is known before
 * the first frame and tested without a renderer (`splashGeometry.test.ts`). The ball's keyframes
 * join it with the motion (#856), from the same floor and dot.
 *
 * **The lockup is centred as one** — the word, a 9 pt gap and the 12 pt dot, as the mock draws it,
 * not the word alone — horizontally and vertically, on the **full physical screen**:
 *
 * - the letters' vertical midline, the middle of their line box, is the screen's;
 * - **the floor is 14 pt below it**, and the dot's centre sits on it. In Archivo 800 at 42 pt that
 *   is the word's baseline (to 0,03 pt): the dot is the word's full stop;
 * - the dot's centre is 9 + 6 pt right of the last *a*'s right edge — its advance, where a next
 *   letter would start — so the dot's far side is the lockup's.
 *
 * **Where the app's view does not cover a system bar** — Android's opaque status bar, a three-button
 * navigation bar — the view is not the screen. Every position comes back in the **view's** own
 * coordinates, offset by where the view starts on the screen, so the composition stays centred on
 * the screen. A bar below the view moves nothing; one above it moves everything up by its height.
 *
 * **The letters are placed, not laid out.** Each is set at its own pen position: the font's own
 * advances, its kerning, and the role's tracking between letters — never after the last, which has
 * no next letter to come closer to. So the word's width is known before any text is measured, and
 * nothing a platform's text layout does to a run of letters reaches it.
 */

/** The word the splash draws, letter by letter: the one place the app spells it so (ADR-0209 §5). */
export const WORDMARK = ['R', 'a', 'k', 'i', 'e', 't', 'a'] as const;

export type WordmarkLetter = (typeof WORDMARK)[number];

/** The word's six neighbouring pairs, as the font kerns them. */
export type WordmarkPair = 'Ra' | 'ak' | 'ki' | 'ie' | 'et' | 'ta';

/** A face's own numbers for the word, in its font units. */
export interface WordmarkFace {
  /** The em square every number below is in. */
  readonly unitsPerEm: number;
  /** How far the line box reaches above the baseline. */
  readonly ascender: number;
  /** How far it reaches below — negative, as the font stores it. */
  readonly descender: number;
  /** Each letter's advance: from its pen position to the next letter's, before tracking. */
  readonly advance: Readonly<Record<WordmarkLetter, number>>;
  /** How much each pair's second letter moves towards the first; negative tightens. */
  readonly kerning: Readonly<Record<WordmarkPair, number>>;
}

/**
 * **Archivo 800's numbers for *Rakieta***, in its 1000-unit em. Read once off
 * `Archivo_800ExtraBold.ttf` — `hhea` for the line box, `hmtx` for the advances, `GPOS`'s `kern`
 * feature for the pairs — and **pinned against the file** by `splashWordmark.test.ts`, so a font
 * release that redraws a letter turns that red and these are read again. The face kerns R·a and
 * no other pair in the word.
 */
export const WORDMARK_FACE: WordmarkFace = {
  unitsPerEm: 1000,
  ascender: 878,
  descender: -210,
  advance: { R: 750, a: 616, k: 610, i: 288, e: 619, t: 385 },
  kerning: { Ra: -15, ak: 0, ki: 0, ie: 0, et: 0, ta: 0 },
};

/** The face, and the `splashWord` role's size and tracking it is set at, in points. */
export interface WordmarkSetting {
  readonly face: WordmarkFace;
  readonly fontSize: number;
  /** Tracking between letters: the role's `letterSpacing`, applied here rather than by the text. */
  readonly letterSpacing: number;
}

/**
 * The brief's lockup, in points: the gap after the word, the dot, and the floor under the word.
 *
 * **Here and not in `theme.ts`**, on `LAUNCH_CLOCK`'s argument: they are the product owner's
 * numbers for one picture, played once per process, and not steps of the design system's spacing
 * scale that another surface could reach for. The geometry is their one reader; the splash draws
 * the dot from what it returns.
 */
export const LOCKUP = {
  /** From the last *a*'s right edge to the dot. */
  gap: 9,
  /** The dot's diameter, which is the ball's. */
  dot: 12,
  /** From the letters' vertical midline down to the floor, where the dot's centre sits. */
  floorBelowMidline: 14,
} as const;

interface Point {
  readonly x: number;
  readonly y: number;
}

interface Size {
  readonly width: number;
  readonly height: number;
}

export interface Box extends Point, Size {}

/** The phone, as the splash finds it. */
export interface SplashPlacement {
  /** The full physical screen, status bar and navigation bar included, in points. */
  readonly screen: Size;
  /**
   * The splash's own view on that screen. Only where it starts matters: below an opaque status bar
   * it starts that bar's height down, and above a navigation bar it simply stops short.
   */
  readonly view: Box;
}

/** One letter, set at its pen position in its own line box. */
export interface PlacedLetter extends Box {
  readonly letter: WordmarkLetter;
}

/** Everything the splash places, in the view's own coordinates. */
export interface SplashGeometry {
  /** The full screen: what the ground and its glow are drawn over. */
  readonly screen: Box;
  /** The word, the gap and the dot, as one box: centred on the full screen. */
  readonly lockup: Box;
  /** R · a · k · i · e · t · a, in order: each one's pen position, advance and line box. */
  readonly letters: readonly PlacedLetter[];
  /** The floor along the word's baseline: where the dot's centre sits, and the ball lands (#856). */
  readonly floor: number;
  /** The dot: its centre, and its diameter. */
  readonly dot: Point & { readonly size: number };
}

/** Where the lockup stands on this phone. */
export function splashGeometry(
  { screen, view }: SplashPlacement,
  { face, fontSize, letterSpacing }: WordmarkSetting,
): SplashGeometry {
  const scale = fontSize / face.unitsPerEm;
  const lineBox = (face.ascender - face.descender) * scale;

  // Pen positions from the word's own left edge: each letter's advance, then the tracking and the
  // pair's kerning before the next. Past the last letter's advance is the word's right edge.
  const pens: number[] = [];
  let word = 0;
  WORDMARK.forEach((letter, i) => {
    pens.push(word);
    word += face.advance[letter] * scale;
    const next = WORDMARK[i + 1];
    if (next === undefined) return;
    word += face.kerning[`${letter}${next}` as WordmarkPair] * scale + letterSpacing;
  });
  const lockupWidth = word + LOCKUP.gap + LOCKUP.dot;

  // On the screen, then into the view's coordinates.
  const left = screen.width / 2 - lockupWidth / 2 - view.x;
  const midline = screen.height / 2 - view.y;
  const top = midline - lineBox / 2;
  const floor = midline + LOCKUP.floorBelowMidline;

  return {
    screen: { x: 0 - view.x, y: 0 - view.y, width: screen.width, height: screen.height },
    lockup: { x: left, y: top, width: lockupWidth, height: lineBox },
    letters: WORDMARK.map((letter, i) => ({
      letter,
      x: left + pens[i]!,
      y: top,
      width: face.advance[letter] * scale,
      height: lineBox,
    })),
    floor,
    dot: { x: left + word + LOCKUP.gap + LOCKUP.dot / 2, y: floor, size: LOCKUP.dot },
  };
}
