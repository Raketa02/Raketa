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

/**
 * **The ball's path** (#856; decision log §4, Q4 and Q5): the brief's keyframes on every phone. The
 * heights are the brief's as written, and every sideways distance is the brief's times one factor,
 * `k = (dotX − 0.10·W) / 292`, so the first landing sits 10 % in from the left edge, where the mock
 * draws it — 292 pt left of the dot is off-screen on every phone from 360 to 430 pt.
 *
 * **The brief's table, spelled here**: a keyframe that drifted from it turns this red.
 */
const BRIEF = [
  { kind: 'start', at: 0, left: 292 },
  { kind: 'landing', at: 390, left: 292, squash: { width: 1.4, height: 0.65 } },
  { kind: 'liftoff', at: 460, left: 288 },
  { kind: 'peak', at: 720, left: 202, up: 150 },
  { kind: 'landing', at: 980, left: 122, squash: { width: 1.3, height: 0.72 } },
  { kind: 'liftoff', at: 1050, left: 118 },
  { kind: 'peak', at: 1230, left: 62, up: 62 },
  { kind: 'landing', at: 1400, left: 12, squash: { width: 1.2, height: 0.8 } },
  { kind: 'liftoff', at: 1470, left: 10 },
  { kind: 'peak', at: 1580, left: 2, up: 16 },
  { kind: 'settled', at: 1680, left: 0 },
] as const;

/** How far a landing presses the ball into the floor. */
const PRESS = 2;
/** The ball's radius: it is the dot. */
const RADIUS = DOT / 2;

describe.each(PHONES)(
  'the ball’s path on a $width × $height phone ($build)',
  ({ width, height }) => {
    const at = splashGeometry(fullScreen(width, height), SETTING);
    const { ball, dot, floor } = at;
    const kinds = (kind: string) => ball.filter((frame) => frame.kind === kind);

    it('scales every sideways distance by k = (dotX − 0.10·W) / 292', () => {
      expect(at.sideways).toBeCloseTo((dot.x - 0.1 * width) / 292, EXACT);
      expect(at.sideways).toBeGreaterThan(0);
      expect(at.sideways).toBeLessThan(1);
    });

    it('follows the brief’s keyframes: their kinds, their times, and how far left each is, before k', () => {
      expect(ball.map(({ kind, at: time }) => [kind, time])).toEqual(
        BRIEF.map(({ kind, at: time }) => [kind, time]),
      );
      ball.forEach((frame, i) => {
        expect((dot.x - frame.x) / at.sideways).toBeCloseTo(BRIEF[i]!.left, EXACT);
      });
    });

    it('lands first at 10 % of the width, and the start is straight above it', () => {
      const [start, first] = ball;

      expect(first!.x).toBeCloseTo(0.1 * width, EXACT);
      expect(start!.x).toBe(first!.x);
    });

    it('starts just above the top edge, fully hidden, already round', () => {
      const start = ball[0]!;

      expect(start.y + RADIUS).toBeCloseTo(0, EXACT);
      expect(start.y + RADIUS).toBeLessThanOrEqual(0);
      expect(start.squash).toEqual({ width: 1, height: 1 });
    });

    it('peaks 150, 62 and 16 pt above the floor, whatever the width', () => {
      const heights = kinds('peak').map((peak) => floor - peak.y);

      expect(heights).toHaveLength(3);
      [150, 62, 16].forEach((up, i) => expect(heights[i]).toBeCloseTo(up, EXACT));
    });

    it('presses 2 pt into the floor at each landing, squashed as the brief says, and leaves it round', () => {
      kinds('landing').forEach((landing) => expect(landing.y - floor).toBeCloseTo(PRESS, EXACT));
      expect(kinds('landing').map((landing) => landing.squash)).toEqual(
        BRIEF.flatMap((frame) => ('squash' in frame ? [frame.squash] : [])),
      );
      kinds('liftoff').forEach((liftoff) => {
        expect(liftoff.y).toBe(floor);
        expect(liftoff.squash).toEqual({ width: 1, height: 1 });
      });
    });

    it('lands each time lower and further right than the last, each squash gentler', () => {
      const landings = kinds('landing');
      const peaks = kinds('peak');

      landings.slice(1).forEach((landing, i) => {
        expect(landing.x).toBeGreaterThan(landings[i]!.x);
        expect(landing.squash.width).toBeLessThan(landings[i]!.squash.width);
        expect(landing.squash.height).toBeGreaterThan(landings[i]!.squash.height);
      });
      peaks.slice(1).forEach((peak, i) => {
        expect(peak.y).toBeGreaterThan(peaks[i]!.y);
      });
    });

    it('ends exactly on the dot: not close to it — on it', () => {
      const last = ball[ball.length - 1]!;

      expect(last.kind).toBe('settled');
      expect(last.x).toBe(dot.x);
      expect(last.y).toBe(dot.y);
      expect(last.squash).toEqual({ width: 1, height: 1 });
    });
  },
);

/** The letters rise in three groups, one group per landing: Rak · ie · ta. */
describe('the letters’ cues', () => {
  const at = splashGeometry(fullScreen(390, 844), SETTING);
  const landings = at.ball.filter(({ kind }) => kind === 'landing').map(({ at: time }) => time);

  it('are the brief’s: R 0.42, a 0.46, k 0.50 · i 1.00, e 1.04 · t 1.42, a 1.46', () => {
    expect(at.letters.map(({ letter, cue }) => [letter, cue])).toEqual([
      ['R', 420],
      ['a', 460],
      ['k', 500],
      ['i', 1000],
      ['e', 1040],
      ['t', 1420],
      ['a', 1460],
    ]);
  });

  it('come in three groups, each just after its own landing: Rak · ie · ta', () => {
    const groupOf = (cue: number) => landings.filter((landing) => landing < cue).length;
    const groups = [1, 2, 3].map((group) =>
      at.letters
        .filter(({ cue }) => groupOf(cue) === group)
        .map(({ letter }) => letter)
        .join(''),
    );

    expect(groups).toEqual(['Rak', 'ie', 'ta']);
  });

  it('are the same on every phone', () => {
    PHONES.forEach(({ width, height }) => {
      expect(
        splashGeometry(fullScreen(width, height), SETTING).letters.map(({ cue }) => cue),
      ).toEqual(at.letters.map(({ cue }) => cue));
    });
  });
});

/**
 * Below an opaque status bar the view starts the bar's height down, so the screen's top edge is
 * above the view's: the ball still starts above the screen's, and the first landing is still 10 %
 * of the screen's width — in the view's own coordinates, as everything else.
 */
describe('the ball’s path in a view that does not cover the whole screen', () => {
  const W = 411;
  const H = 914;
  const STATUS_BAR = 24;
  const view = { x: 0, y: STATUS_BAR, width: W, height: H - STATUS_BAR - 48 };
  const at = splashGeometry({ screen: { width: W, height: H }, view }, SETTING);
  const onTheScreen = splashGeometry(fullScreen(W, H), SETTING);

  it('starts above the screen’s top edge, not the view’s', () => {
    expect(at.ball[0]!.y + RADIUS).toBeCloseTo(-STATUS_BAR, EXACT);
  });

  it('is the same path on the screen, every keyframe moved up by the bar', () => {
    expect(at.sideways).toBeCloseTo(onTheScreen.sideways, EXACT);
    at.ball.forEach((frame, i) => {
      expect(frame.x).toBeCloseTo(onTheScreen.ball[i]!.x, EXACT);
      expect(frame.y).toBeCloseTo(onTheScreen.ball[i]!.y - STATUS_BAR, EXACT);
    });
  });
});
