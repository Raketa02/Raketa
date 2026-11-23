/**
 * **The splash's geometry, static part** — where the lockup stands on every phone
 * ([#855](https://github.com/Raketa02/Raketa/issues/855); decision log §4, Q6 and Q7;
 * [ADR-0209](../../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)).
 *
 * Pure: a screen and the wordmark's font constants in, positions out, no renderer. The constants
 * are the module's own, pinned against the font file by `splashWordmark.test.ts`; **the brief's
 * numbers are spelled here** — 42 pt, −1,68, the 9 pt gap, the 12 pt dot, the floor 14 pt below
 * the letters' midline — so a geometry that drifted from them turns this red rather than moving
 * it along.
 *
 * The widths are the four the PRD names (360, 390, 411, 430 pt), each on a short phone (an iPhone
 * SE's 640) and a tall one (the A32's 914 is about the tallest in use; 932 is a Pro Max's).
 */

import { splashGeometry, WORDMARK, WORDMARK_FACE, type SplashPlacement } from './splashGeometry';

/** The brief's wordmark: Archivo 800 at 42 pt, tracked −4 %. */
const SETTING = { face: WORDMARK_FACE, fontSize: 42, letterSpacing: -1.68 } as const;
const GAP = 9;
const DOT = 12;
const FLOOR_BELOW_MIDLINE = 14;

const WIDTHS = [360, 390, 411, 430] as const;
const HEIGHTS = { short: 640, tall: 932 } as const;

/** Every phone the suite stands the lockup on: four widths, each short and tall. */
const PHONES = WIDTHS.flatMap((width) =>
  Object.entries(HEIGHTS).map(([build, height]) => ({ width, height, build })),
);

/** A phone whose view covers its whole screen, as an iPhone's does and an edge-to-edge Android's. */
function fullScreen(width: number, height: number): SplashPlacement {
  return { screen: { width, height }, view: { x: 0, y: 0, width, height } };
}

/** Floating-point arithmetic agrees to far below a pixel; nothing here should be off by more. */
const EXACT = 9;

describe.each(PHONES)('on a $width × $height phone ($build)', ({ width, height }) => {
  const at = splashGeometry(fullScreen(width, height), SETTING);
  const first = at.letters[0]!;
  const last = at.letters[at.letters.length - 1]!;

  it('draws Rakieta as seven letters, each further right than the one before', () => {
    expect(at.letters.map(({ letter }) => letter).join('')).toBe('Rakieta');
    at.letters.slice(1).forEach((letter, i) => {
      expect(letter.x).toBeGreaterThan(at.letters[i]!.x);
    });
  });

  it('centres the lockup — the word, the 9 pt gap and the dot — as one, across the screen', () => {
    expect(at.lockup.x).toBeCloseTo(first.x, EXACT);
    expect(at.lockup.x + at.lockup.width).toBeCloseTo(last.x + last.width + GAP + DOT, EXACT);
    expect(at.lockup.x + at.lockup.width / 2).toBeCloseTo(width / 2, EXACT);
  });

  it('puts the letters’ midline at the screen’s, so the lockup is centred down it too', () => {
    at.letters.forEach((letter) => {
      expect(letter.y + letter.height / 2).toBeCloseTo(height / 2, EXACT);
    });
    expect(at.lockup.y + at.lockup.height / 2).toBeCloseTo(height / 2, EXACT);
  });

  it('lays the floor 14 pt below that midline, and the dot’s centre on it', () => {
    expect(at.floor).toBeCloseTo(height / 2 + FLOOR_BELOW_MIDLINE, EXACT);
    expect(at.dot.y).toBe(at.floor);
    expect(at.dot.size).toBe(DOT);
  });

  it('puts the dot’s centre 9 + 6 pt right of the last a, so it ends the lockup', () => {
    expect(at.dot.x).toBeCloseTo(last.x + last.width + GAP + DOT / 2, EXACT);
    expect(at.dot.x + DOT / 2).toBeCloseTo(at.lockup.x + at.lockup.width, EXACT);
  });

  it('draws the ground over the whole screen', () => {
    expect(at.screen).toEqual({ x: 0, y: 0, width, height });
  });
});

describe('the lockup’s own measure, the same on every phone', () => {
  it('is the font’s: on a 390 pt phone the word is 152,42 pt and the lockup 173,42', () => {
    const at = splashGeometry(fullScreen(390, 844), SETTING);
    const last = at.letters[at.letters.length - 1]!;

    expect(last.x + last.width - at.letters[0]!.x).toBeCloseTo(152.418, 3);
    expect(at.lockup.width).toBeCloseTo(173.418, 3);
    expect(at.letters[0]!.x).toBeCloseTo(108.291, 3);
    expect(at.dot.x).toBeCloseTo(275.709, 3);
  });

  it('kerns R·a as the font does: the a starts 31,5 − 1,68 − 0,63 pt after the R', () => {
    const at = splashGeometry(fullScreen(390, 844), SETTING);

    expect(at.letters[1]!.x - at.letters[0]!.x).toBeCloseTo(29.19, 9);
  });

  it('is a fixed size: a wider phone moves the lockup, never stretches it', () => {
    const narrow = splashGeometry(fullScreen(360, 640), SETTING);
    const wide = splashGeometry(fullScreen(430, 932), SETTING);

    expect(wide.lockup.width).toBeCloseTo(narrow.lockup.width, EXACT);
    expect(wide.lockup.height).toBeCloseTo(narrow.lockup.height, EXACT);
    wide.letters.forEach((letter, i) => {
      expect(letter.x - wide.lockup.x).toBeCloseTo(narrow.letters[i]!.x - narrow.lockup.x, EXACT);
    });
  });

  it('spells the word the splash draws, and no other', () => {
    expect(WORDMARK.join('')).toBe('Rakieta');
  });
});

/**
 * Where the app's view does not cover a system bar — Android's opaque status bar, a three-button
 * navigation bar — the composition is still centred on the screen, not on the view, so every
 * position comes back in the view's own coordinates, offset by where the view starts.
 */
describe('a view that does not cover the whole screen', () => {
  const W = 411;
  const H = 914;
  const STATUS_BAR = 24;
  const NAVIGATION_BAR = 48;

  const onTheScreen = splashGeometry(fullScreen(W, H), SETTING);

  it('moves everything up by an opaque status bar above the view', () => {
    const at = splashGeometry(
      { screen: { width: W, height: H }, view: { x: 0, y: STATUS_BAR, width: W, height: H - 24 } },
      SETTING,
    );

    expect(at.floor).toBeCloseTo(H / 2 + FLOOR_BELOW_MIDLINE - STATUS_BAR, EXACT);
    expect(at.dot.y).toBeCloseTo(onTheScreen.dot.y - STATUS_BAR, EXACT);
    expect(at.dot.x).toBeCloseTo(onTheScreen.dot.x, EXACT);
    at.letters.forEach((letter, i) => {
      expect(letter.y).toBeCloseTo(onTheScreen.letters[i]!.y - STATUS_BAR, EXACT);
      expect(letter.x).toBeCloseTo(onTheScreen.letters[i]!.x, EXACT);
    });
    expect(at.lockup.y + at.lockup.height / 2 + STATUS_BAR).toBeCloseTo(H / 2, EXACT);
  });

  it('centres on the screen, not on the view, above a navigation bar the view stops at', () => {
    const view = { x: 0, y: 0, width: W, height: H - NAVIGATION_BAR };
    const at = splashGeometry({ screen: { width: W, height: H }, view }, SETTING);

    expect(at.floor).toBeCloseTo(H / 2 + FLOOR_BELOW_MIDLINE, EXACT);
    expect(at.floor).not.toBeCloseTo(view.height / 2 + FLOOR_BELOW_MIDLINE, 0);
    expect(at).toEqual(onTheScreen);
  });

  it('takes both bars at once, and draws the ground over the whole screen from above the view', () => {
    const view = { x: 0, y: STATUS_BAR, width: W, height: H - STATUS_BAR - NAVIGATION_BAR };
    const at = splashGeometry({ screen: { width: W, height: H }, view }, SETTING);

    expect(at.dot.y).toBeCloseTo(onTheScreen.dot.y - STATUS_BAR, EXACT);
    expect(at.screen).toEqual({ x: 0, y: -STATUS_BAR, width: W, height: H });
  });
});
