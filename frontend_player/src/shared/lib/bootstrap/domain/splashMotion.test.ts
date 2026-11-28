/**
 * **The splash's motion, pure** — how the ball and the letters move between the geometry's keyframes
 * ([#856](https://github.com/Rakieta02/Rakieta/issues/856); the brief's §3, decision log §4–§5).
 *
 * The path's keyframes are `splashGeometry.test.ts`'s; this holds the curves through them, sampled
 * at times, with no renderer: every fall accelerates and every rise decelerates, a landing squashes
 * the ball about its bottom and it is round again 0,07 s later, it ends exactly on the dot and stops
 * dead, and each letter rises 10 pt and fades in over 0,32 s with a slight overshoot. **How it looks
 * is not here** — smooth, an impact, the ball as the full stop — and is the product owner's to see
 * on the A32 and an iPhone.
 */

import { splashGeometry, WORDMARK_FACE, type BallKeyframe } from './splashGeometry';
import { ballAt, letterAt, splashStillAt, type BallPose } from './splashMotion';

const SETTING = { face: WORDMARK_FACE, fontSize: 42, letterSpacing: -1.68 } as const;
const RADIUS = 6;
const PRESS = 2;
/** The brief's: the squash rounds back in the 0,07 s after each landing. */
const ROUND_BACK = 70;
/** The brief's letter: 10 pt below its place, over 0,32 s. */
const RISE = 10;
const RISE_TAKES = 320;
const EXACT = 9;

const PHONES = [360, 390, 411, 430].flatMap((width) =>
  [640, 932].map((height) => ({ width, height })),
);

function placed(width: number, height: number) {
  return splashGeometry(
    { screen: { width, height }, view: { x: 0, y: 0, width, height } },
    SETTING,
  );
}

/** The drawn ball's lowest point: its centre plus half its squashed height. */
function bottomOf(pose: BallPose): number {
  return pose.y + RADIUS * pose.scaleY;
}

/** The pose every millisecond from `from` to `to`, both included. */
function sampled(path: readonly BallKeyframe[], from: number, to: number): BallPose[] {
  return Array.from({ length: to - from + 1 }, (_, i) => ballAt(path, from + i));
}

/**
 * Where, in a run of samples, a sample breaks with the one before it: none when `holds` holds all
 * through. One assertion over the whole run, which names the samples that break it.
 */
function breaks<T>(run: readonly T[], holds: (sample: T, before: T) => boolean): number[] {
  return run.flatMap((sample, i) => (i === 0 || holds(sample, run[i - 1]!) ? [] : [i]));
}

/** How far the ball moves down from one sample to the next: negative is up. */
function stepsDown(poses: readonly BallPose[]): number[] {
  return poses.slice(1).map((pose, i) => bottomOf(pose) - bottomOf(poses[i]!));
}

describe.each(PHONES)('the ball on a $width × $height phone', ({ width, height }) => {
  const at = placed(width, height);
  const { ball, dot, floor } = at;
  const of = (kind: BallKeyframe['kind']) => ball.filter((frame) => frame.kind === kind);

  it('is where the keyframes put it, at their times', () => {
    ball.forEach((frame) => {
      const pose = ballAt(ball, frame.at);
      expect(pose.x).toBeCloseTo(frame.x, EXACT);
      expect(bottomOf(pose)).toBeCloseTo(frame.y + RADIUS, EXACT);
      expect(pose.scaleX).toBeCloseTo(frame.squash.width, EXACT);
      expect(pose.scaleY).toBeCloseTo(frame.squash.height, EXACT);
    });
  });

  it('starts out of sight above the top edge, and is on screen, falling, in its first frame', () => {
    expect(bottomOf(ballAt(ball, 0))).toBeLessThanOrEqual(0 + 1e-9);
    expect(bottomOf(ballAt(ball, 16))).toBeGreaterThan(0);
  });

  it('falls straight down to its first landing, accelerating — already falling as it enters', () => {
    const fall = sampled(ball, 0, 390);
    const steps = stepsDown(fall);

    expect(fall.filter((pose) => pose.x !== ball[0]!.x)).toEqual([]);
    expect(steps[0]).toBeGreaterThan(0.1);
    expect(breaks(steps, (step, before) => step > before)).toEqual([]);
  });

  it('accelerates in every fall and decelerates in every rise, as gravity would', () => {
    const peaks = of('peak');
    const liftoffs = of('liftoff');
    const landings = of('landing');

    liftoffs.forEach((liftoff, i) => {
      const rise = stepsDown(sampled(ball, liftoff.at, peaks[i]!.at)).map((step) => -step);
      expect(rise.filter((step) => step <= 0)).toEqual([]);
      expect(breaks(rise, (step, before) => step < before)).toEqual([]);
    });
    peaks.forEach((peak, i) => {
      const next = landings[i + 1] ?? of('settled')[0]!;
      // Up to the frame before the next landing: the landing itself is the squash.
      const fall = stepsDown(sampled(ball, peak.at, next.at - 1));
      expect(fall.filter((step) => step <= 0)).toEqual([]);
      expect(breaks(fall, (step, before) => step > before)).toEqual([]);
    });
  });

  it('carries the ball rightwards all the way, and never back', () => {
    const xs = sampled(ball, 0, 1680).map((pose) => pose.x);

    expect(breaks(xs, (x, before) => x >= before)).toEqual([]);
  });

  it('never jumps: from one millisecond to the next it moves by less than 3 pt', () => {
    const poses = sampled(ball, 0, 1800);

    expect(
      breaks(
        poses,
        (pose, before) =>
          Math.abs(pose.x - before.x) < 3 && Math.abs(bottomOf(pose) - bottomOf(before)) < 3,
      ),
    ).toEqual([]);
  });

  it('is round until the moment it lands, then squashes about its bottom, pressed 2 pt into the floor', () => {
    of('landing').forEach((landing) => {
      const before = ballAt(ball, landing.at - 1);
      const on = ballAt(ball, landing.at);

      expect([before.scaleX, before.scaleY]).toEqual([1, 1]);
      expect(on.scaleX).toBeCloseTo(landing.squash.width, EXACT);
      expect(on.scaleY).toBeCloseTo(landing.squash.height, EXACT);
      expect(bottomOf(on)).toBeCloseTo(floor + RADIUS + PRESS, EXACT);
    });
  });

  it('rounds back to a perfect circle in the 0,07 s after each landing, its bottom on the floor', () => {
    of('landing').forEach((landing) => {
      const back = sampled(ball, landing.at, landing.at + ROUND_BACK);

      const offTheFloor = back.filter(
        (pose) =>
          bottomOf(pose) < floor + RADIUS - 1e-9 || bottomOf(pose) > floor + RADIUS + PRESS + 1e-9,
      );
      expect(offTheFloor).toEqual([]);
      expect(
        breaks(
          back,
          (pose, before) => pose.scaleX <= before.scaleX && pose.scaleY >= before.scaleY,
        ),
      ).toEqual([]);
      const round = back[back.length - 1]!;
      expect([round.scaleX, round.scaleY]).toEqual([1, 1]);
    });
  });

  it('keeps the squash brief: most of the way back to round within 0,03 s of the landing', () => {
    of('landing').forEach((landing) => {
      const { scaleX, scaleY } = ballAt(ball, landing.at + 30);
      const backX = (landing.squash.width - scaleX) / (landing.squash.width - 1);
      const backY = (scaleY - landing.squash.height) / (1 - landing.squash.height);

      expect(backX).toBeGreaterThanOrEqual(0.8);
      expect(backY).toBeGreaterThanOrEqual(0.8);
    });
  });

  it('is round all through each flight: no trail, no stretch, only the landings squash', () => {
    const landings = of('landing').map(({ at: time }) => time);
    const squashedInFlight = sampled(ball, 0, 1800)
      .map((pose, t) => ({ t, pose }))
      .filter(({ t }) => !landings.some((landing) => t >= landing && t < landing + ROUND_BACK))
      .filter(({ pose }) => pose.scaleX !== 1 || pose.scaleY !== 1);

    expect(squashedInFlight).toEqual([]);
  });

  it('comes to rest at 1,68 s exactly on the dot, and stops dead', () => {
    const rest = { x: dot.x, y: dot.y, scaleX: 1, scaleY: 1 };

    expect(ballAt(ball, 1680)).toEqual(rest);
    [1681, 1780, 2600, 60_000].forEach((t) => expect(ballAt(ball, t)).toEqual(rest));
  });

  it('holds its start before the clock has begun', () => {
    expect(ballAt(ball, -16)).toEqual(ballAt(ball, 0));
  });
});

describe('a letter', () => {
  const CUE = 420;

  it('waits below its place, unseen, until its cue', () => {
    [0, 200, CUE].forEach((t) => expect(letterAt(CUE, t)).toEqual({ opacity: 0, below: RISE }));
  });

  it('rises 10 pt into its place and fades from 0 to 1 over 0,32 s', () => {
    expect(letterAt(CUE, CUE + RISE_TAKES)).toEqual({ opacity: 1, below: 0 });
    expect(letterAt(CUE, CUE + RISE_TAKES / 2).opacity).toBeGreaterThan(0);
    expect(letterAt(CUE, CUE + RISE_TAKES / 2).opacity).toBeLessThan(1);
  });

  it('fades in steadily, never back', () => {
    const fades = Array.from({ length: RISE_TAKES + 1 }, (_, i) => letterAt(CUE, CUE + i).opacity);

    expect(breaks(fades, (opacity, before) => opacity >= before)).toEqual([]);
  });

  it('overshoots its place slightly, then settles back', () => {
    const rises = Array.from({ length: RISE_TAKES + 1 }, (_, i) => letterAt(CUE, CUE + i).below);
    const highest = Math.min(...rises);

    expect(highest).toBeLessThan(0);
    expect(highest).toBeGreaterThan(-2);
    expect(rises.indexOf(highest)).toBeLessThan(RISE_TAKES);
  });

  it('is still once risen', () => {
    [CUE + RISE_TAKES, CUE + RISE_TAKES + 1, 60_000].forEach((t) =>
      expect(letterAt(CUE, t)).toEqual({ opacity: 1, below: 0 }),
    );
  });
});

describe('the word', () => {
  const at = placed(390, 844);
  const { letters } = at;
  const still = splashStillAt(at);

  it('is still by 1,78 s: the last a risen, and nothing moving after', () => {
    expect(still).toBe(1780);
    letters.forEach(({ cue }) => {
      expect(letterAt(cue, still)).toEqual({ opacity: 1, below: 0 });
    });
    expect(letterAt(letters[letters.length - 1]!.cue, still - 1).below).not.toBe(0);
  });
});
