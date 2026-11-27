/**
 * **The splash's geometry** — where everything the drawn splash places stands, on any phone
 * ([ADR-0209](../../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md);
 * `docs/specs/splash-screen/`, decision log §4).
 *
 * One pure function from the full screen and the wordmark's font constants to everything the splash
 * places or moves: the lockup's box, each letter's place and cue, the floor, the dot, the sideways
 * factor *k* and the ball's keyframes. No React and no device access, so it is known before the
 * first frame and tested without a renderer (`splashGeometry.test.ts`). How the ball and the letters
 * move between those keyframes is `splashMotion.ts`'s.
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
 *
 * **The ball's path is the brief's, fitted to the phone** (#856; decision log §4, Q4 and Q5). Every
 * keyframe is the brief's offset from the dot, so the path ends on it by construction:
 *
 * - **sideways, scaled by one factor**, `k = (dotX − 0.10·W) / 292`, the impact nudges included, so
 *   the first landing sits 10 % in from the screen's left edge, where the mock draws it. The brief's
 *   292 pt left of the dot is off-screen on every phone from 360 to 430 pt;
 * - **heights as the brief gives them**: 150, 62 and 16 pt above the floor, and a landing pressed
 *   2 pt into it;
 * - **the start just above the screen's top edge**, fully hidden and straight above the first
 *   landing, on every phone. The brief's 460 pt above the dot is on screen on any phone taller than
 *   about 880 pt. The fall still takes 0,39 s, so a taller phone gets a slightly faster drop.
 */

/** The word the splash draws, letter by letter: the name under the icon too (ADR-0211). */
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

/**
 * **The letters' cues**, in milliseconds from the splash's first layout, in the word's order: each is
 * when that letter starts to rise. Three groups, one per landing, so each impact seems to shake the
 * next letters up out of the floor — *Rak* after the first landing (0,39 s), *ie* after the second
 * (0,98 s), *ta* after the third (1,40 s), staggered 0,04 s apart within a group.
 */
export const LETTER_CUES = [420, 460, 500, 1000, 1040, 1420, 1460] as const satisfies {
  readonly length: (typeof WORDMARK)['length'];
};

/** What the ball is doing at a keyframe. */
export type BallKeyframeKind =
  /** Just above the top edge, already falling. */
  | 'start'
  /** On the floor, squashed and pressed into it: the impact. */
  | 'landing'
  /** Round again, leaving the floor: the landing's 0,07 s are over. */
  | 'liftoff'
  /** The top of a bounce. */
  | 'peak'
  /** At rest on the dot, for good. */
  | 'settled';

/** How a landing squashes the ball: its width and height as fractions of its diameter. */
export interface Squash {
  readonly width: number;
  readonly height: number;
}

const ROUND: Squash = { width: 1, height: 1 };

/**
 * **The brief's path, after the start**: when, how far left of the dot before *k*, how far above the
 * floor, and how a landing squashes. Its landings are 2 pt below the floor — pressed into it — and
 * each landing's nudge to the right (292 → 288, 122 → 118, 12 → 10) is the 0,07 s until its liftoff.
 * The product owner's numbers for one picture, as `LOCKUP`'s are.
 */
const BRIEF_PATH: readonly {
  readonly kind: Exclude<BallKeyframeKind, 'start'>;
  readonly at: number;
  readonly left: number;
  readonly up: number;
  readonly squash?: Squash;
}[] = [
  { kind: 'landing', at: 390, left: 292, up: -2, squash: { width: 1.4, height: 0.65 } },
  { kind: 'liftoff', at: 460, left: 288, up: 0 },
  { kind: 'peak', at: 720, left: 202, up: 150 },
  { kind: 'landing', at: 980, left: 122, up: -2, squash: { width: 1.3, height: 0.72 } },
  { kind: 'liftoff', at: 1050, left: 118, up: 0 },
  { kind: 'peak', at: 1230, left: 62, up: 62 },
  { kind: 'landing', at: 1400, left: 12, up: -2, squash: { width: 1.2, height: 0.8 } },
  { kind: 'liftoff', at: 1470, left: 10, up: 0 },
  { kind: 'peak', at: 1580, left: 2, up: 16 },
  { kind: 'settled', at: 1680, left: 0, up: 0 },
];

/** Where the brief's first landing is, before *k*: the distance *k* is fitted to. */
const FIRST_LANDING_LEFT = 292;

/** How far in from the screen's left edge the first landing sits, as a fraction of its width. */
const FIRST_LANDING_IN = 0.1;

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
  /** When it starts to rise into its place, in milliseconds from the splash's first layout. */
  readonly cue: number;
}

/**
 * **One of the ball's keyframes**, in the view's own coordinates. `x` and `y` are its centre as a
 * round ball; a landing's squash is drawn about the ball's bottom, so the squashed ball keeps the
 * bottom that centre gives it (`splashMotion.ts`).
 */
export interface BallKeyframe extends Point {
  readonly kind: BallKeyframeKind;
  /** When, in milliseconds from the splash's first layout. */
  readonly at: number;
  readonly squash: Squash;
}

/** Everything the splash places, in the view's own coordinates. */
export interface SplashGeometry {
  /** The full screen: what the ground and its glow are drawn over. */
  readonly screen: Box;
  /** The word, the gap and the dot, as one box: centred on the full screen. */
  readonly lockup: Box;
  /** R · a · k · i · e · t · a, in order: each one's pen position, advance and line box. */
  readonly letters: readonly PlacedLetter[];
  /** The floor along the word's baseline: where the dot's centre sits, and the ball lands. */
  readonly floor: number;
  /** The dot: its centre, and its diameter. */
  readonly dot: Point & { readonly size: number };
  /** *k*: what every sideways distance in the brief is multiplied by on this phone. */
  readonly sideways: number;
  /** The ball's path, from its start above the top edge to its rest on the dot, in time order. */
  readonly ball: readonly BallKeyframe[];
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
  const dot = { x: left + word + LOCKUP.gap + LOCKUP.dot / 2, y: floor, size: LOCKUP.dot };

  // k, from where the dot is on the screen: the first landing, 292 pt left of it before k, is then
  // 10 % of the screen's width in from its left edge.
  const sideways = (dot.x + view.x - FIRST_LANDING_IN * screen.width) / FIRST_LANDING_LEFT;
  // Every keyframe is an offset from the dot, so the last — none at all — is the dot itself.
  const path: BallKeyframe[] = BRIEF_PATH.map(({ kind, at, left: offLeft, up, squash }) => ({
    kind,
    at,
    x: dot.x - offLeft * sideways,
    y: dot.y - up,
    squash: squash ?? ROUND,
  }));
  // Straight above the first landing, its bottom on the screen's top edge: fully hidden, and on
  // screen in the first frame of its fall.
  const start: BallKeyframe = {
    kind: 'start',
    at: 0,
    x: path[0]!.x,
    y: 0 - view.y - LOCKUP.dot / 2,
    squash: ROUND,
  };

  return {
    screen: { x: 0 - view.x, y: 0 - view.y, width: screen.width, height: screen.height },
    lockup: { x: left, y: top, width: lockupWidth, height: lineBox },
    letters: WORDMARK.map((letter, i) => ({
      letter,
      x: left + pens[i]!,
      y: top,
      width: face.advance[letter] * scale,
      height: lineBox,
      cue: LETTER_CUES[i]!,
    })),
    floor,
    dot,
    sideways,
    ball: [start, ...path],
  };
}
