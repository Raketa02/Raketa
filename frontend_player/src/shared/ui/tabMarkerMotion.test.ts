/**
 * **The selection marker's motion, as numbers** (10.2, ADR-0210 §8,
 * [#884](https://github.com/Rakieta02/Rakieta/issues/884)): the spring that carries it, the stretch
 * its motion gives it, a retarget mid-flight, and the colour-in's share of its beat. Pure, so the
 * brief's figures are asserted as figures: jest draws no frame a person could look at.
 */

import {
  colourInAt,
  MARKER_SLIDE,
  MARKER_WIDEST,
  markerAt,
  markerPlacedAt,
  markerTravelling,
  type MarkerPose,
  type MarkerTrip,
} from './tabMarkerMotion';
import { theme } from './theme';

/** A trip set off from rest: the marker standing under `from`, the lit tab turning to `to`. */
const trip = (from: number, to: number): MarkerTrip =>
  markerTravelling(markerPlacedAt(from), MARKER_SLIDE, to);

/** Every millisecond of a trip, with how far along the way it is. */
function frames(of: MarkerTrip): (MarkerPose & { t: number; way: number })[] {
  const out = [];
  for (let t = 0; t <= MARKER_SLIDE; t += 1) {
    const pose = markerAt(of, t);
    out.push({ ...pose, t, way: (pose.at - of.from) / (of.to - of.from) });
  }
  return out;
}

const widest = (of: MarkerTrip) => frames(of).reduce((a, b) => (b.wide > a.wide ? b : a));
const narrowest = (of: MarkerTrip) => frames(of).reduce((a, b) => (b.wide < a.wide ? b : a));

describe('motion.tabMarker', () => {
  it('is a 460 ms slide at damping ratio 0.75, the colour coming in over 300 ms from 140', () => {
    expect(theme.motion.tabMarker).toEqual({
      slide: 460,
      dampingRatio: 0.75,
      colourIn: 300,
      colourInAfter: 140,
    });
    expect(MARKER_SLIDE).toBe(theme.motion.tabMarker.slide);
  });
});

/**
 * **The stretch follows the motion** (Q10): wide and flat as the marker speeds up, narrow and tall
 * as it brakes — calibrated on the brief's own trip, Home → You, two columns.
 */
describe('the stretch', () => {
  it('reaches about 1.30 wide × 0.84 tall near 35% of the way on a two-column trip', () => {
    const peak = widest(trip(0, 2));

    expect(peak.wide).toBeCloseTo(1.3, 2);
    expect(peak.tall).toBeCloseTo(0.84, 2);
    expect(peak.way).toBeGreaterThan(0.3);
    expect(peak.way).toBeLessThan(0.4);
  });

  it('recoils to about 0.94 × 1.06 near 70% of the way', () => {
    const recoil = narrowest(trip(0, 2));

    expect(recoil.wide).toBeCloseTo(0.94, 2);
    expect(recoil.tall).toBeCloseTo(1.06, 2);
    expect(recoil.way).toBeGreaterThan(0.65);
    expect(recoil.way).toBeLessThan(0.75);
  });

  it('stretches about half as much on a one-column trip, both ways', () => {
    const far = trip(0, 2);
    const near = trip(0, 1);

    expect(widest(near).wide - 1).toBeCloseTo((widest(far).wide - 1) / 2, 3);
    expect(1 - widest(near).tall).toBeCloseTo((1 - widest(far).tall) / 2, 3);
    expect(1 - narrowest(near).wide).toBeCloseTo((1 - narrowest(far).wide) / 2, 3);
    expect(narrowest(near).tall - 1).toBeCloseTo((narrowest(far).tall - 1) / 2, 3);
  });

  it('stretches alike whichever way it travels', () => {
    const right = frames(trip(0, 2));
    const left = frames(trip(2, 0));

    right.forEach((pose, at) => {
      expect(left[at]!.wide).toBeCloseTo(pose.wide, 10);
      expect(left[at]!.tall).toBeCloseTo(pose.tall, 10);
    });
  });

  it('is never wider than the widest the dock’s fit holds, even turned mid-flight', () => {
    // Play → Home, sent to You as it swings back from its overshoot: the one press found that would
    // carry it a hair past 1.30 (1.304) if nothing held it.
    const turned = markerTravelling(trip(1, 0), 200, 2);

    expect(MARKER_WIDEST).toBe(1.3);
    for (const pose of frames(turned)) expect(pose.wide).toBeLessThanOrEqual(MARKER_WIDEST);
  });
});

/** **The spring** (ADR-0210 §8): every trip 460 ms whatever its distance; its overshoot. */
describe('the slide', () => {
  /** How far past its tab the marker goes, in points, over columns this wide. */
  const overshoot = (of: MarkerTrip, column: number) =>
    Math.max(...frames(of).map((pose) => (pose.at - of.to) * Math.sign(of.to - of.from))) * column;

  it('overshoots by about 3.4 on a 120-wide column, and 6.8 across two', () => {
    expect(overshoot(trip(0, 1), 120)).toBeCloseTo(3.4, 1);
    expect(overshoot(trip(0, 2), 120)).toBeCloseTo(6.8, 1);
    // e^(−ζπ/√(1−ζ²)) of the trip, the decision log's figure.
    const ratio = theme.motion.tabMarker.dampingRatio;
    const share = Math.exp((-ratio * Math.PI) / Math.sqrt(1 - ratio * ratio));
    expect(overshoot(trip(0, 1), 120)).toBeCloseTo(120 * share, 2);
  });

  it('sets off fast, from where it stood', () => {
    const far = frames(trip(0, 2));

    expect(far[0]).toMatchObject({ at: 0, speed: 0, wide: 1, tall: 1 });
    // A third of the way inside the first 60 ms: it starts fast.
    expect(far.find((pose) => pose.way >= 1 / 3)!.t).toBeLessThan(60);
  });

  it('rests at exactly 1 × 1 under its tab at 460 ms, the far trip and the near one alike', () => {
    for (const of of [trip(0, 2), trip(0, 1), trip(2, 1)]) {
      expect(markerAt(of, MARKER_SLIDE)).toEqual({
        at: of.to,
        speed: 0,
        stretch: 0,
        wide: 1,
        tall: 1,
      });
      expect(markerAt(of, MARKER_SLIDE + 1000)).toEqual(markerAt(of, MARKER_SLIDE));
    }
  });

  it('is settled before it rests — the last step to rest is under a third of a point', () => {
    // A 320 phone's columns are 98.7 wide and the widest phone's about 135: a thousandth of two of
    // them is under a third of a point.
    const far = trip(0, 2);
    const last = markerAt(far, MARKER_SLIDE - 1);

    expect(Math.abs(last.at - far.to)).toBeLessThan(0.001 * 2);
    expect(Math.abs(last.wide - 1)).toBeLessThan(0.001);
    expect(Math.abs(last.tall - 1)).toBeLessThan(0.001);
  });

  it('stands still where it is placed', () => {
    const placed = markerPlacedAt(1);

    expect(markerAt(placed, 0)).toEqual({ at: 1, speed: 0, stretch: 0, wide: 1, tall: 1 });
    expect(markerAt(placed, MARKER_SLIDE)).toEqual(markerAt(placed, 0));
  });
});

/**
 * **A retarget** (the brief's *rapid taps*): a press while the marker travels starts a new spring
 * from where it is, at the speed it has, so its place and its shape carry on rather than snap.
 */
describe('a retarget', () => {
  /** Home → You, turned to Play at `t`, as the pose either side of the press. */
  function turnedAt(t: number) {
    const first = trip(0, 2);
    const second = markerTravelling(first, t, 1);
    return { first, second, before: markerAt(first, t), after: markerAt(second, 0) };
  }

  it.each([20, 51, 95, 200])(
    'carries the place, the speed and the shape across a press at %i ms',
    (t) => {
      const { before, after } = turnedAt(t);

      expect(after.at).toBeCloseTo(before.at, 10);
      expect(after.speed).toBeCloseTo(before.speed, 10);
      expect(after.wide).toBeCloseTo(before.wide, 10);
      expect(after.tall).toBeCloseTo(before.tall, 10);
    },
  );

  it('changes the shape no faster across the press than a frame of a trip does', () => {
    // The steepest a plain trip's shape moves in a 16 ms frame, against the frame after the press.
    const plain = frames(trip(0, 2));
    const steepest = Math.max(
      ...plain.slice(16).map((pose, at) => Math.abs(pose.wide - plain[at]!.wide)),
    );

    for (const t of [20, 51, 95]) {
      const { before, second } = turnedAt(t);
      expect(Math.abs(markerAt(second, 16).wide - before.wide)).toBeLessThanOrEqual(steepest);
    }
  });

  it('heads for the new tab and rests there, never at the first', () => {
    const { second } = turnedAt(95);

    expect(second.to).toBe(1);
    expect(markerAt(second, MARKER_SLIDE)).toMatchObject({ at: 1, wide: 1, tall: 1 });
  });

  it('turns back from where it is, still going the first way at first', () => {
    // Home → You, sent home at its fastest: it does not jump back, it brakes.
    const first = trip(0, 2);
    const back = markerTravelling(first, 51, 0);

    expect(back.from).toBeCloseTo(markerAt(first, 51).at, 10);
    expect(markerAt(back, 16).at).toBeGreaterThan(back.from);
    expect(markerAt(back, MARKER_SLIDE).at).toBe(0);
  });

  it('starts from rest once the trip it left has ended', () => {
    const ended = markerTravelling(trip(0, 2), MARKER_SLIDE, 1);

    expect(ended).toEqual(trip(2, 1));
  });
});

/**
 * **The colour-in** (ADR-0210 §8): the lit tab's selected layer comes in over `colourIn`, starting
 * `colourInAfter` into the slide — its share of that beat, which the bar eases on `easeDecel`.
 */
describe('the colour-in', () => {
  const { colourIn, colourInAfter } = theme.motion.tabMarker;

  it('is nothing until 140 ms into the slide, and whole from 440', () => {
    expect(colourInAt(0)).toBe(0);
    expect(colourInAt(colourInAfter)).toBe(0);
    expect(colourInAt(colourInAfter + colourIn)).toBe(1);
    expect(colourInAt(MARKER_SLIDE)).toBe(1);
  });

  it('runs evenly between, for the bar to ease', () => {
    expect(colourInAt(colourInAfter + colourIn / 2)).toBeCloseTo(0.5, 10);
  });
});
