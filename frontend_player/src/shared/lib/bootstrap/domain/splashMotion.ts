/**
 * **The splash's motion** — how the ball and the letters move between the geometry's keyframes, at
 * any moment of the splash's clock ([#856](https://github.com/Rakieta02/Rakieta/issues/856); the
 * brief's §3, decision log §4–§5;
 * [ADR-0209](../../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)).
 *
 * Two pure functions of time: where the ball is and how it is squashed (`ballAt`), and how far a
 * letter has risen and how much of it shows (`letterAt`). **The splash runs them on the UI thread**,
 * each frame, from one clock that Reanimated moves from 0 to `splashStillAt` — so the ball, its
 * landings and the letters they shake up can never drift apart, and the last frame is exactly the
 * keyframes' last. That is what the `'worklet'` directive in each function is: a string, not an
 * import. Reanimated's Babel plugin copies a function so marked to the UI thread; under jest and in
 * the app's own JavaScript it is an ordinary function, and this module still imports no React and
 * no device.
 *
 * **The ball, as the brief describes its feel:**
 *
 * - **every fall accelerates and every rise decelerates**, as gravity would: a rise eases out to
 *   its peak and a fall from a peak eases in from rest there, each a parabola in time;
 * - **the first fall is already falling** as the ball enters: it crosses the top edge at a fifth of
 *   the speed it lands at, as the brief's drop from 460 pt above the dot crosses the top of its own
 *   390 × 844 phone. From rest at the edge it would creep in over several frames instead;
 * - **sideways, the ball keeps its speed** through each stretch, as a thrown ball does: its path
 *   bends only because its height is eased;
 * - **a landing is an impact**: round in the frame before, squashed the moment it lands, four fifths
 *   of the way back to round within 0,03 s — the brief's *"brief (about 0.03 s) and always followed
 *   by an immediate return to a perfect circle"* — and round by the liftoff 0,07 s after.
 *   The squash is drawn **about the ball's bottom**, so the squashed ball's bottom is the round
 *   one's, 2 pt into the floor, and it rises back to the floor as the ball rounds;
 * - **it ends exactly on the dot and stops dead**: from the last keyframe on, the pose is that
 *   keyframe, not a value an easing arrived near.
 *
 * **A letter** rises from 10 pt below its place while fading from nothing to white, over 0,32 s
 * from its cue, with a slight overshoot — about 1 pt past its place — that settles back. Its
 * opacity eases out, so it is mostly there while it is still rising.
 */

import { LOCKUP, type BallKeyframe, type SplashGeometry } from './splashGeometry';

/** The drawn ball: its centre, and how it is scaled about that centre. */
export interface BallPose {
  readonly x: number;
  readonly y: number;
  readonly scaleX: number;
  readonly scaleY: number;
}

/** A letter as it rises: how much of it shows, and how far below its place it is. */
export interface LetterPose {
  readonly opacity: number;
  /** Points below its place; negative while it overshoots above it. */
  readonly below: number;
}

/** The brief's letter: how far below its place it starts, and how long it takes to rise. */
export const LETTER_RISE = { from: 10, takes: 320 } as const;

/** The ball's radius: it is the dot. */
const RADIUS = LOCKUP.dot / 2;

/**
 * The first fall's speed as it enters, as a share of its mean speed over the 0.39 s. Under a
 * constant acceleration it lands at `2 − ENTRY_SPEED` of that mean, `5 / 3`, so at a third it
 * enters at a fifth of its landing speed.
 */
const ENTRY_SPEED = 1 / 3;

/** How far past its place a letter's rise goes: the classic back-out, about 10 % of the rise. */
const OVERSHOOT = 1.70158;

function clamp01(u: number): number {
  'worklet';
  return u < 0 ? 0 : u > 1 ? 1 : u;
}

/** A fall from rest: slow at its top, fastest as it lands. */
function fromRest(u: number): number {
  'worklet';
  return u * u;
}

/** A fall already under way as it starts: the same constant acceleration, from a speed. */
function alreadyFalling(u: number): number {
  'worklet';
  return ENTRY_SPEED * u + (1 - ENTRY_SPEED) * u * u;
}

/** A rise: fastest as it leaves the floor, at rest at its peak. */
function easeOut(u: number): number {
  'worklet';
  return 1 - (1 - u) * (1 - u);
}

/**
 * A landing's return to round: steeper still, so most of the squash is gone within the brief's
 * *"about 0.03 s"* — four fifths of it — and the rest settles by the liftoff.
 */
function snapBack(u: number): number {
  'worklet';
  const v = 1 - u;
  return 1 - v * v * v;
}

/** Past the end and back: how a letter arrives. */
function backOut(u: number): number {
  'worklet';
  const v = u - 1;
  return 1 + (OVERSHOOT + 1) * v * v * v + OVERSHOOT * v * v;
}

/**
 * How the height — and a landing's squash — moves through the stretch from `from` to `to`: up to a
 * peak eases out, back to round off the floor snaps, and down to a landing or to rest falls. The
 * squash and the height share the curve, which is what keeps the squashed ball's bottom on the
 * floor as it rounds.
 */
function heightCurve(from: BallKeyframe, to: BallKeyframe, u: number): number {
  'worklet';
  if (to.kind === 'peak') return easeOut(u);
  if (to.kind === 'liftoff') return snapBack(u);
  return from.kind === 'start' ? alreadyFalling(u) : fromRest(u);
}

/**
 * **Where the ball is at `t`** milliseconds from the splash's first layout, as it is drawn: before
 * the start, its start; from the last keyframe on, exactly that keyframe.
 */
export function ballAt(path: readonly BallKeyframe[], t: number): BallPose {
  'worklet';
  const last = path[path.length - 1]!;
  if (t >= last.at) {
    return { x: last.x, y: last.y, scaleX: last.squash.width, scaleY: last.squash.height };
  }

  let i = 0;
  while (i < path.length - 2 && t >= path[i + 1]!.at) i += 1;
  const from = path[i]!;
  const to = path[i + 1]!;
  const u = clamp01((t - from.at) / (to.at - from.at));
  const e = heightCurve(from, to, u);

  // A fall arrives round, and the ball squashes the moment it lands; only the 0,07 s after a landing
  // move the squash, from the landing's back to round.
  const falling = to.kind === 'landing';
  const scaleX = falling ? 1 : from.squash.width + (to.squash.width - from.squash.width) * e;
  const scaleY = falling ? 1 : from.squash.height + (to.squash.height - from.squash.height) * e;
  const y = from.y + (to.y - from.y) * e;

  return {
    x: from.x + (to.x - from.x) * u,
    // Scaled about its centre, so moved down by what the squash takes off its height: its bottom is
    // the round ball's.
    y: y + RADIUS * (1 - scaleY),
    scaleX,
    scaleY,
  };
}

/** **A letter at `t`**, whose rise is cued at `cue`: unseen below its place until then, still after. */
export function letterAt(cue: number, t: number): LetterPose {
  'worklet';
  const u = (t - cue) / LETTER_RISE.takes;
  if (u <= 0) return { opacity: 0, below: LETTER_RISE.from };
  if (u >= 1) return { opacity: 1, below: 0 };
  return { opacity: easeOut(u), below: LETTER_RISE.from * (1 - backOut(u)) };
}

/**
 * **When the splash is still**: the ball at rest and the last letter risen — 1,78 s on the brief's
 * clock. The splash's clock runs to here and stops, and the lockup holds until the fade.
 */
export function splashStillAt({ ball, letters }: Pick<SplashGeometry, 'ball' | 'letters'>): number {
  const rests = ball[ball.length - 1]?.at ?? 0;
  return letters.reduce((still, { cue }) => Math.max(still, cue + LETTER_RISE.takes), rests);
}
