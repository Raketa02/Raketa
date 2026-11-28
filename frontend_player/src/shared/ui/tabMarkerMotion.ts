/**
 * **The selection marker's motion** — where the marker stands and how it is stretched at any moment
 * of a trip between two tabs, and how far the lit tab's colour has come in (10.2, ADR-0210 §8,
 * [#884](https://github.com/Rakieta02/Rakieta/issues/884); the decision log's §10).
 *
 * Pure functions of a trip and a clock. **The bar runs them on the UI thread**, each frame, from one
 * clock that Reanimated moves from 0 to `MARKER_SLIDE`, as the splash runs its own motion module, so
 * the travel, the stretch and the colour-in can never drift apart and the last frame is exactly the
 * rest pose. The `'worklet'` in each function is a string, not an import: Reanimated's Babel plugin
 * copies a function so marked to the UI thread, and under jest it is an ordinary function. This
 * module imports no React, no Reanimated and no device.
 *
 * **Everything is measured in columns**, not points (ADR-0210 §8): 0 is the first column's place, 1
 * the second's, and a speed is columns a millisecond. So a two-column trip stretches alike on every
 * phone, and the bar turns columns into points with the width it lays them out at.
 *
 * ## The spring — the app's first
 *
 * `motion.tabMarker`'s **460 ms at damping ratio 0.75**. It is this module's own rather than
 * Reanimated's `withSpring`, because the stretch is drawn from the marker's speed and braking at
 * every frame, which `withSpring` keeps to itself. Its stiffness is set by its length: **it settles
 * within a thousandth of its trip by 460 ms** — under a third of a point on the widest phone's
 * two-column trip — and from 460 on it is exactly at rest, so the step from the last frame to rest is
 * nothing anyone could see. Released from rest it overshoots by `e^(−ζπ/√(1−ζ²))` of its trip, 2.8 %:
 * 3.4 on a 120-wide column and 6.8 across two. Every trip takes the same 460 ms, so the far jump
 * moves faster.
 *
 * ## The stretch follows the motion, never the share of the trip
 *
 * - **While the marker speeds up it widens and flattens**, by its speed: `PER_SPEED` of it.
 * - **While it brakes it turns that over into a recoil**, narrower and taller, by how hard it brakes
 *   for the speed it has. Its speed over its braking is the time it would take to stop; once that
 *   is under `NARROWS_WITHIN`, the marker narrows, and as it nears a stop the recoil tends to half
 *   the widening its speed alone would give, then goes with the speed.
 * - **Calibrated on the brief's own trip**, Home → You across two columns: the widest is **1.30 ×
 *   0.84 at its fastest, a third of the way**, and the recoil **0.94 × 1.06 near 70 %**. A spring
 *   released from rest is fastest at 34 % of its way, so the brief's *"about a third"* is where the
 *   motion puts it, not a keyframe. A one-column trip moves at half the speed at every moment, so it
 *   stretches exactly half as much.
 * - **Never wider than `MARKER_WIDEST`**, whatever a retarget does to its speed: 10.2's fit holds
 *   the marker at its widest inside the narrowest phone's column.
 *
 * ## A retarget
 *
 * A press while the marker travels starts a new spring **from where it is, at the speed it has**
 * (`markerTravelling`), so it never finishes the first trip first and never snaps. The new pull
 * changes the braking at once, so the shape the marker had is **carried** and eased into the new
 * trip's own over `CARRY`, a few frames: the place, the speed and the shape all carry on.
 */

import { theme } from './theme';

/** A trip: where the marker set off from, how it was moving, and the tab it is going to. */
export interface MarkerTrip {
  /** Where it set off, in columns: 0 is the first column's place. */
  readonly from: number;
  /** Its speed as it set off, in columns a millisecond — + towards the later columns. */
  readonly speed: number;
  /** The stretch it brought from a trip it left mid-way, over this trip's own, eased out. */
  readonly carried: number;
  /** The column it is going to. */
  readonly to: number;
}

/** The marker as it is drawn at a moment of its trip. */
export interface MarkerPose {
  /** Where it stands, in columns. */
  readonly at: number;
  /** Its speed, in columns a millisecond — + towards the later columns. */
  readonly speed: number;
  /** How much wider than at rest it is: + stretched, − recoiling. */
  readonly stretch: number;
  /** Its width as a share of its rest width — `scaleX`. */
  readonly wide: number;
  /** Its height as a share of its rest height — `scaleY`. */
  readonly tall: number;
}

const { slide, dampingRatio, colourIn, colourInAfter } = theme.motion.tabMarker;

/** **How long every trip takes**, near or far — 460 ms. */
export const MARKER_SLIDE: number = slide;

/** **The brief's stretch**, at the two-column trip's widest. */
const STRETCH = { wide: 0.3, flat: 0.16 } as const;
/** **The brief's recoil**, near 70 % of the way: narrower and taller by as much. */
const RECOIL = { narrow: 0.06, tall: 0.06 } as const;

/** **The widest the marker is ever drawn** — 1.30 of its rest width, which 10.2's fit holds. */
export const MARKER_WIDEST = 1 + STRETCH.wide;

/** What is left of a trip from rest by its end — a thousandth, so its last step is never seen. */
const SETTLED = 0.001;

const UNDAMPED = Math.sqrt(1 - dampingRatio * dampingRatio);
/** How fast the spring's swing dies away, a millisecond. */
const DECAY = Math.log(1 / (SETTLED * UNDAMPED)) / MARKER_SLIDE;
/** Its natural frequency, and the frequency it swings at, in radians a millisecond. */
const NATURAL = DECAY / dampingRatio;
const SWING = NATURAL * UNDAMPED;

/**
 * **A one-column trip's top speed**, released from rest: where the spring stops speeding up, at
 * `atan(√(1−ζ²)/ζ)` into its swing.
 */
const PEAK_SPEED =
  NATURAL * Math.exp((-dampingRatio * Math.atan(UNDAMPED / dampingRatio)) / UNDAMPED);
/** **How wide a speed makes the marker** — the two-column trip's top speed gives the brief's 1.30. */
const PER_SPEED = STRETCH.wide / (2 * PEAK_SPEED);
/** **The marker narrows once it would stop within this**, at the braking it has — in ms. Set so the
 *  two-column trip recoils to the brief's 0.94 near 70 % of its way. */
const NARROWS_WITHIN = 222;
/** **How long a retarget's carried shape takes to ease out** — its time constant, a few frames. */
const CARRY = 60;

/** **The marker standing under a column**, at rest: the dock's first draw, and Reduce motion. */
export function markerPlacedAt(column: number): MarkerTrip {
  'worklet';
  return { from: column, speed: 0, carried: 0, to: column };
}

/**
 * **The stretch of a marker moving at `speed` and accelerating at `pull`** — before anything is
 * carried. Its speed widens it; braking for that speed turns the widening over.
 */
function stretchOf(speed: number, pull: number): number {
  'worklet';
  const pace = Math.abs(speed);
  // How hard it brakes: its acceleration against the way it is going, and nothing while it gains.
  const braking = Math.max(0, -pull * Math.sign(speed));
  const over = pace + 2 * NARROWS_WITHIN * braking;
  if (over === 0) return 0;
  return (PER_SPEED * pace * (pace - NARROWS_WITHIN * braking)) / over;
}

/** **How tall a stretch leaves the marker**: flatter as it widens, taller by as much as it narrows. */
function tallFor(stretch: number): number {
  'worklet';
  return stretch >= 0
    ? 1 - (stretch * STRETCH.flat) / STRETCH.wide
    : 1 - (stretch * RECOIL.tall) / RECOIL.narrow;
}

/** **The marker `t` ms into its trip** — from 460 on, exactly at rest under its tab. */
export function markerAt(trip: MarkerTrip, t: number): MarkerPose {
  'worklet';
  if (t >= MARKER_SLIDE) return { at: trip.to, speed: 0, stretch: 0, wide: 1, tall: 1 };
  const time = Math.max(0, t);

  // A damped spring towards `to`, from where it set off and as it was moving then.
  const off = trip.from - trip.to;
  const fading = Math.exp(-DECAY * time);
  const cos = Math.cos(SWING * time);
  const sin = Math.sin(SWING * time);
  const away = fading * (off * cos + ((trip.speed + DECAY * off) / SWING) * sin);
  const speed =
    fading * (trip.speed * cos - ((DECAY * trip.speed + NATURAL * NATURAL * off) / SWING) * sin);
  const pull = -NATURAL * NATURAL * away - 2 * DECAY * speed;

  const stretch = Math.min(
    STRETCH.wide,
    stretchOf(speed, pull) + trip.carried * Math.exp(-time / CARRY),
  );
  return { at: trip.to + away, speed, stretch, wide: 1 + stretch, tall: tallFor(stretch) };
}

/**
 * **The trip a press starts, `t` ms into the trip it interrupts**: towards `to`, from where the
 * marker is and at the speed it has, carrying its shape. A trip that has ended starts from rest.
 */
export function markerTravelling(trip: MarkerTrip, t: number, to: number): MarkerTrip {
  'worklet';
  const now = markerAt(trip, t);
  const fresh = stretchOf(now.speed, -NATURAL * NATURAL * (now.at - to) - 2 * DECAY * now.speed);
  return { from: now.at, speed: now.speed, carried: now.stretch - fresh, to };
}

/**
 * **How far the lit tab's colour has come in, `t` ms into the slide** — nothing for the first
 * `colourInAfter`, then evenly over `colourIn`, which the bar eases on `easeDecel`.
 */
export function colourInAt(t: number): number {
  'worklet';
  const share = (t - colourInAfter) / colourIn;
  return share <= 0 ? 0 : share >= 1 ? 1 : share;
}
