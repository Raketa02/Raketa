/**
 * The radar's geometry, as pure arithmetic
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §7.2–7.7).
 *
 * Every number the spec states is asserted here as the spec states it — the ladder, the two
 * bounds from the reach, the floor, the three states and the dead-band over their thresholds,
 * the ring rule, a point from a bearing, the in-view rule and the flight's stop — so a build
 * session that nudged one of them fails here rather than on a device.
 */

import {
  FLY_TO_WIDTH_KM,
  RING_SERIES_KM,
  WIDTH_FLOOR_KM,
  WIDTH_LADDER_KM,
  betweenTransforms,
  boundCentre,
  containerTransform,
  dragged,
  flyToView,
  homeView,
  inView,
  nextStopIn,
  nextStopOut,
  openingWidthKm,
  pinched,
  pointOf,
  ptPerKm,
  atFloor,
  fanOut,
  ringsFor,
  stacksAt,
  tileState,
  rubberBand,
  toKm,
  toScreen,
  viewFromTransform,
  widestWidthKm,
  zoomState,
  type FieldBox,
  type RadarView,
} from './radarGeometry';

const FIELD: FieldBox = { width: 390, height: 600 };

describe('the ladder and its two bounds', () => {
  it('is the spec’s eight stops, in order', () => {
    expect(WIDTH_LADDER_KM).toEqual([1.5, 3, 5.4, 10, 18, 30, 55, 110]);
    expect(WIDTH_FLOOR_KM).toBe(1.5);
  });

  it('opens at the first stop at or above 1,8 × the reach, and stops at the first at or above 2,2 ×', () => {
    // The default radius: 18 and 30.
    expect(openingWidthKm(10)).toBe(18);
    expect(widestWidthKm(10)).toBe(30);
    // 12 km: 21,6 → 30 for both.
    expect(openingWidthKm(12)).toBe(30);
    expect(widestWidthKm(12)).toBe(30);
    // The narrowest reach: 1,8 → 3 and 2,2 → 3.
    expect(openingWidthKm(1)).toBe(3);
    expect(widestWidthKm(1)).toBe(3);
    // The widest reach: 90 → 110 and 110 → 110.
    expect(openingWidthKm(50)).toBe(110);
    expect(widestWidthKm(50)).toBe(110);
  });

  it('never opens wider than it may go', () => {
    for (const reach of [1, 2, 3, 5, 8, 10, 12, 20, 25, 30, 40, 50]) {
      expect(openingWidthKm(reach)).toBeLessThanOrEqual(widestWidthKm(reach));
    }
  });

  it('steps in to the next stop below and out to the next stop above, from a stop', () => {
    expect(nextStopIn(18)).toBe(10);
    expect(nextStopOut(18, 30)).toBe(30);
    expect(nextStopIn(10)).toBe(5.4);
    expect(nextStopOut(10, 30)).toBe(18);
  });

  it('snaps to the ladder from wherever a pinch left off', () => {
    expect(nextStopIn(7.83)).toBe(5.4);
    expect(nextStopOut(7.83, 30)).toBe(10);
    expect(nextStopIn(29.4)).toBe(18);
    expect(nextStopOut(29.4, 30)).toBe(30);
  });

  it('greys at the ends: nothing below the floor, nothing above the widest', () => {
    expect(nextStopIn(1.5)).toBeUndefined();
    expect(nextStopOut(30, 30)).toBeUndefined();
    expect(nextStopOut(31, 30)).toBeUndefined();
    // A rounding hair above a stop is that stop, not a stop to step to.
    expect(nextStopIn(1.5000001)).toBeUndefined();
    expect(nextStopOut(29.9999999, 30)).toBeUndefined();
  });
});

describe('the three states by width', () => {
  it('is wide above 10, closer at 10 and below, closest at 5,4 and below', () => {
    expect(zoomState(18)).toBe('wide');
    expect(zoomState(10.5)).toBe('wide');
    expect(zoomState(10)).toBe('closer');
    expect(zoomState(7)).toBe('closer');
    expect(zoomState(5.4)).toBe('closest');
    expect(zoomState(1.5)).toBe('closest');
  });

  /**
   * The dead-band lies **above** each threshold and never below it, so a ± landing exactly on
   * a stop always lands in the state the stop names, and a pinch resting a hair over the
   * threshold does not flicker between two states.
   */
  it('holds a state a pinch is resting just past, and lets the stop itself decide', () => {
    expect(zoomState(10.2, 'closer')).toBe('closer');
    expect(zoomState(10.2, 'wide')).toBe('wide');
    expect(zoomState(10.4, 'closer')).toBe('wide');
    expect(zoomState(5.5, 'closest')).toBe('closest');
    expect(zoomState(5.5, 'closer')).toBe('closer');
    expect(zoomState(5.7, 'closest')).toBe('closer');
    // From nothing held, the threshold alone decides.
    expect(zoomState(10.2)).toBe('wide');
    expect(zoomState(5.5)).toBe('closer');
  });
});

describe('kilometres to points', () => {
  it('scales the field’s width to the view’s width', () => {
    expect(ptPerKm(FIELD, 18)).toBeCloseTo(390 / 18);
    expect(ptPerKm({ width: 780, height: 600 }, 18)).toBeCloseTo(780 / 18);
  });

  it('puts the viewer at the field’s vertical 42 % at home, centred', () => {
    const home = homeView(10);
    expect(home).toEqual({ centre: { x: 0, y: 0 }, widthKm: 18 });
    expect(toScreen({ x: 0, y: 0 }, home, FIELD)).toEqual({ x: 195, y: 252 });
  });

  it('places a row from its distance and bearing, north up', () => {
    // Due east, 9 km, at 18 km across: half the field to the right of the viewer.
    expect(pointOf({ distanceKm: 9, bearingDeg: 90 })).toEqual({ x: 9, y: expect.closeTo(0) });
    const east = toScreen(pointOf({ distanceKm: 9, bearingDeg: 90 }), homeView(10), FIELD);
    expect(east.x).toBeCloseTo(390);
    expect(east.y).toBeCloseTo(252);
    // Due north, 5 km: up the screen.
    const north = toScreen(pointOf({ distanceKm: 5, bearingDeg: 0 }), homeView(10), FIELD);
    expect(north.x).toBeCloseTo(195);
    expect(north.y).toBeCloseTo(252 - 5 * (390 / 18));
    // South-west: left and down.
    const sw = toScreen(pointOf({ distanceKm: 2, bearingDeg: 225 }), homeView(10), FIELD);
    expect(sw.x).toBeLessThan(195);
    expect(sw.y).toBeGreaterThan(252);
  });

  it('moves with the view’s centre', () => {
    const view: RadarView = { centre: { x: 3, y: 0 }, widthKm: 18 };
    // The centre is at the focus; the viewer is 3 km to its west.
    expect(toScreen({ x: 3, y: 0 }, view, FIELD)).toEqual({ x: 195, y: 252 });
    expect(toScreen({ x: 0, y: 0 }, view, FIELD).x).toBeCloseTo(195 - 3 * (390 / 18));
  });
});

describe('the rings', () => {
  it('draws the series at 1 · 2 · 5 · 10 · 20 · 50', () => {
    expect(RING_SERIES_KM).toEqual([1, 2, 5, 10, 20, 50]);
  });

  it('draws a ring whose on-screen radius is at least 26 pt and at most 3,5 field widths', () => {
    // 18 km across on a 390 pt field: 21,67 pt per km. 1 km is 21,7 (too small); 2 km is 43,3;
    // 5 → 108; 10 → 217; 20 → 433; 50 → 1083; 3,5 widths is 1365.
    expect(ringsFor(FIELD, 18).map((ring) => ring.km)).toEqual([2, 5, 10, 20, 50]);
    // 3 km across: 130 pt per km. 1 → 130 … 10 → 1300 (in), 20 → 2600 (out).
    expect(ringsFor(FIELD, 3).map((ring) => ring.km)).toEqual([1, 2, 5, 10]);
    // 110 km across: 3,55 pt per km. 5 → 17,7 (out), 10 → 35,5 (in).
    expect(ringsFor(FIELD, 110).map((ring) => ring.km)).toEqual([10, 20, 50]);
  });

  it('never draws a bullseye: two or more at every stop', () => {
    for (const width of WIDTH_LADDER_KM) {
      expect(ringsFor(FIELD, width).length).toBeGreaterThanOrEqual(2);
    }
  });

  it('carries each ring’s radius in points', () => {
    const [two] = ringsFor(FIELD, 18);
    expect(two).toEqual({ km: 2, radiusPt: expect.closeTo(2 * (390 / 18)) });
  });
});

describe('in view', () => {
  it('counts a point inside the box between the header and the footer, and not one outside', () => {
    expect(inView({ x: 10, y: 10 }, FIELD)).toBe(true);
    expect(inView({ x: 390, y: 600 }, FIELD)).toBe(true);
    expect(inView({ x: -1, y: 10 }, FIELD)).toBe(false);
    expect(inView({ x: 10, y: 601 }, FIELD)).toBe(false);
  });

  it('is the point and not the card: a card hanging off the edge counts by its spot alone', () => {
    // The spot is in; whatever a card drawn from it would overhang is not asked.
    expect(inView({ x: 389, y: 599 }, FIELD)).toBe(true);
  });
});

describe('one player, drawn', () => {
  it('is a face — wide, or with the level — for everybody but the selected, who is the card at every width', () => {
    expect(tileState('wide', false)).toBe('wide');
    expect(tileState('closer', false)).toBe('closer');
    // The closest width hands nobody a card: a field of cards was a field nobody could use.
    expect(tileState('closest', false)).toBe('closer');
    for (const zoom of ['wide', 'closer', 'closest'] as const) {
      expect(tileState(zoom, true)).toBe('card');
    }
  });
});

describe('the flight', () => {
  it('lands at the width already held when that is narrower than 3 km — never zooming out to show a card', () => {
    const row = { distanceKm: 1.2, bearingDeg: 130 };
    expect(flyToView(row, 1.5).widthKm).toBe(1.5);
    expect(flyToView(row, 3).widthKm).toBe(3);
    expect(flyToView(row, 18).widthKm).toBe(3);
    expect(flyToView(row, 1.5).centre).toEqual(pointOf(row));
  });

  it('lands at the 3 km stop, centred on the row', () => {
    expect(FLY_TO_WIDTH_KM).toBe(3);
    const row = { distanceKm: 9, bearingDeg: 90 };
    expect(flyToView(row)).toEqual({ centre: pointOf(row), widthKm: 3 });
  });
});

describe('stacks at the floor', () => {
  // On the 390 pt field at the floor a kilometre is 260 pt; a 34 pt face is 0,131 km.
  const FACE = 34;
  const near = (id: string, distanceKm: number, bearingDeg: number) => ({
    playerId: id,
    distanceKm,
    bearingDeg,
  });
  // Filip and Ola are 60 m apart; Karol is 1,2 km from both.
  const filip = near('filip', 1.9, 47);
  const ola = near('ola', 1.95, 48);
  const karol = near('karol', 1.2, 130);

  it('folds players whose faces would lie on one another at the floor, and nobody else', () => {
    const stacks = stacksAt([karol, filip, ola], WIDTH_FLOOR_KM, FIELD, FACE);
    expect(stacks).toHaveLength(1);
    expect(stacks[0]?.members).toEqual(['filip', 'ola']);
    expect(stacks[0]?.id).toBe('filip+ola');
  });

  it('forms no stack above the floor: closer is always the answer there', () => {
    expect(stacksAt([filip, ola], 3, FIELD, FACE)).toEqual([]);
    expect(stacksAt([filip, ola], WIDTH_FLOOR_KM * 1.02, FIELD, FACE)).toEqual([]);
    expect(atFloor(WIDTH_FLOOR_KM)).toBe(true);
    expect(atFloor(1.6)).toBe(false);
  });

  it('is exactly one face: 0,13 km apart at the floor is a stack and 0,14 is not', () => {
    const a = near('a', 2, 0);
    const within = near('b', 2.13, 0);
    const beyond = near('c', 2.14, 0);
    expect(stacksAt([a, within], WIDTH_FLOOR_KM, FIELD, FACE)).toHaveLength(1);
    expect(stacksAt([a, beyond], WIDTH_FLOOR_KM, FIELD, FACE)).toHaveLength(0);
  });

  it('takes the relation across: A over B and B over C is one stack of three', () => {
    const a = near('a', 2, 0);
    const b = near('b', 2.1, 0);
    const c = near('c', 2.2, 0);
    const stacks = stacksAt([a, b, c], WIDTH_FLOOR_KM, FIELD, FACE);
    expect(stacks).toHaveLength(1);
    expect(stacks[0]?.members).toEqual(['a', 'b', 'c']);
    // Centred on the mean of the three spots.
    expect(stacks[0]?.centre.y).toBeCloseTo(2.1);
    expect(stacks[0]?.centre.x).toBeCloseTo(0);
  });

  it('opens on a ring a touch target from the marker, a step apart, from north clockwise', () => {
    const stack = stacksAt([filip, ola], WIDTH_FLOOR_KM, FIELD, FACE)[0]!;
    const layout = { clearPt: 44, stepPt: 42 };
    const fanned = fanOut(stack, FIELD, layout);
    expect(fanned.map((f) => f.playerId)).toEqual(['filip', 'ola']);
    const scale = ptPerKm(FIELD, WIDTH_FLOOR_KM);
    const [first, second] = fanned;
    // North of the centre, and south of it, each 44 pt away.
    expect((first!.at.y - stack.centre.y) * scale).toBeCloseTo(44);
    expect((first!.at.x - stack.centre.x) * scale).toBeCloseTo(0);
    expect((second!.at.y - stack.centre.y) * scale).toBeCloseTo(-44);
  });

  it('fills a second ring once the first is full, and no two fanned faces overlap', () => {
    const many = Array.from({ length: 12 }, (_, i) => near(`p${i}`, 2 + i * 0.001, 0));
    const stack = stacksAt(many, WIDTH_FLOOR_KM, FIELD, FACE)[0]!;
    const layout = { clearPt: 44, stepPt: 42 };
    const fanned = fanOut(stack, FIELD, layout);
    expect(fanned).toHaveLength(12);
    const scale = ptPerKm(FIELD, WIDTH_FLOOR_KM);
    const radii = fanned.map(
      (f) => Math.hypot(f.at.x - stack.centre.x, f.at.y - stack.centre.y) * scale,
    );
    // The first ring holds six at 44 pt (2π·44 / 42); the rest sit on the next at 86.
    expect(radii.filter((r) => Math.abs(r - 44) < 1e-6)).toHaveLength(6);
    expect(radii.filter((r) => Math.abs(r - 86) < 1e-6)).toHaveLength(6);
    for (let a = 0; a < fanned.length; a += 1) {
      for (let b = a + 1; b < fanned.length; b += 1) {
        const apart =
          Math.hypot(fanned[a]!.at.x - fanned[b]!.at.x, fanned[a]!.at.y - fanned[b]!.at.y) * scale;
        expect(apart).toBeGreaterThanOrEqual(FACE);
      }
    }
  });
});

describe('the field’s transform', () => {
  /**
   * The tiles are laid out once at the home view's scale, and the field's one transform
   * carries them to wherever the view is: identity at home, and for any other view the
   * scale and the offset that put every base position where `toScreen` says it is.
   */
  it('is the identity at home', () => {
    const home = homeView(10);
    expect(containerTransform(home, home, FIELD)).toEqual({ scale: 1, x: 0, y: 0 });
  });

  it('carries a base position to the live position, for a zoom and for a pan', () => {
    const home = homeView(10);
    const point = pointOf({ distanceKm: 4, bearingDeg: 45 });
    const base = toScreen(point, home, FIELD);
    for (const live of [
      { centre: { x: 0, y: 0 }, widthKm: 3 },
      { centre: { x: 2, y: -1 }, widthKm: 18 },
      { centre: { x: 2, y: -1 }, widthKm: 7.5 },
    ]) {
      const { scale, x, y } = containerTransform(live, home, FIELD);
      // A transform about the field's centre: c + t + k·(b − c).
      const cx = FIELD.width / 2;
      const cy = FIELD.height / 2;
      const carried = { x: cx + x + scale * (base.x - cx), y: cy + y + scale * (base.y - cy) };
      const expected = toScreen(point, live, FIELD);
      expect(carried.x).toBeCloseTo(expected.x);
      expect(carried.y).toBeCloseTo(expected.y);
    }
  });
});

describe('the reach’s edge', () => {
  it('lets the centre travel as far as the reach and no further', () => {
    expect(boundCentre({ x: 3, y: 4 }, 10)).toEqual({ x: 3, y: 4 });
    expect(boundCentre({ x: 6, y: 8 }, 10)).toEqual({ x: 6, y: 8 });
    const bound = boundCentre({ x: 9, y: 12 }, 10);
    expect(bound.x).toBeCloseTo(6);
    expect(bound.y).toBeCloseTo(8);
    expect(boundCentre({ x: 0, y: 0 }, 10)).toEqual({ x: 0, y: 0 });
  });

  it('gives a little under the finger past the edge, and none inside it', () => {
    expect(rubberBand({ x: 3, y: 4 }, 10)).toEqual({ x: 3, y: 4 });
    const past = rubberBand({ x: 9, y: 12 }, 10);
    expect(past.x).toBeGreaterThan(6);
    expect(past.x).toBeLessThan(9);
    expect(past.y).toBeGreaterThan(8);
    expect(past.y).toBeLessThan(12);
  });
});

describe('the transform read backwards', () => {
  it('returns the view that produced it, for any view', () => {
    const home = homeView(10);
    for (const live of [
      home,
      { centre: { x: 0, y: 0 }, widthKm: 3 },
      { centre: { x: 2, y: -1 }, widthKm: 18 },
      { centre: { x: -4.5, y: 3.2 }, widthKm: 7.5 },
    ]) {
      const back = viewFromTransform(containerTransform(live, home, FIELD), home, FIELD);
      expect(back.widthKm).toBeCloseTo(live.widthKm);
      expect(back.centre.x).toBeCloseTo(live.centre.x);
      expect(back.centre.y).toBeCloseTo(live.centre.y);
    }
  });

  it('interpolates a flight’s transform linearly, and lands exactly', () => {
    const from = { scale: 1, x: 0, y: 0 };
    const to = { scale: 6, x: -100, y: 50 };
    expect(betweenTransforms(from, to, 0)).toEqual(from);
    expect(betweenTransforms(from, to, 1)).toEqual(to);
    expect(betweenTransforms(from, to, 0.5)).toEqual({ scale: 3.5, x: -50, y: 25 });
  });
});

describe('a drag', () => {
  const home = homeView(10);

  it('follows the finger exactly, with no inertia: the field moves, so the centre moves the other way', () => {
    const start = { at: { x: 200, y: 300 }, view: home };
    const view = dragged(start, { x: 200 + 390 / 18, y: 300 }, FIELD, 10);
    // One kilometre of field dragged to the right: the centre is one kilometre to the west.
    expect(view.centre.x).toBeCloseTo(-1);
    expect(view.centre.y).toBeCloseTo(0);
    expect(view.widthKm).toBe(18);
    // Dragged down: the centre moves north.
    expect(dragged(start, { x: 200, y: 300 + 390 / 18 }, FIELD, 10).centre.y).toBeCloseTo(1);
  });

  it('gives a little past the reach and no more', () => {
    const start = { at: { x: 200, y: 300 }, view: home };
    const far = dragged(start, { x: 200 - 20 * (390 / 18), y: 300 }, FIELD, 10);
    expect(far.centre.x).toBeGreaterThan(10);
    expect(far.centre.x).toBeLessThan(20);
  });
});

describe('a pinch', () => {
  const home = homeView(10);
  const bounds = { reachKm: 10, widestKm: 30 };

  it('halves the width when the fingers spread to twice their distance, and doubles it when they close', () => {
    const start = { spread: 100, mid: { x: 195, y: 252 }, view: home };
    expect(pinched(start, { spread: 200, mid: start.mid }, FIELD, bounds).widthKm).toBeCloseTo(9);
    expect(pinched(start, { spread: 50, mid: start.mid }, FIELD, bounds).widthKm).toBeCloseTo(30);
  });

  it('is held between the floor and the widest stop', () => {
    const start = { spread: 100, mid: { x: 195, y: 252 }, view: home };
    expect(pinched(start, { spread: 10, mid: start.mid }, FIELD, bounds).widthKm).toBe(30);
    expect(pinched(start, { spread: 5000, mid: start.mid }, FIELD, bounds).widthKm).toBe(
      WIDTH_FLOOR_KM,
    );
  });

  it('zooms around the fingers: the point under their first midpoint stays under their midpoint', () => {
    const mid = { x: 300, y: 150 };
    const start = { spread: 100, mid, view: home };
    const view = pinched(start, { spread: 200, mid }, FIELD, bounds);
    const before = toKm(mid, home, FIELD);
    const after = toKm(mid, view, FIELD);
    expect(after.x).toBeCloseTo(before.x);
    expect(after.y).toBeCloseTo(before.y);
  });

  it('follows the fingers’ midpoint as well as their spread', () => {
    const start = { spread: 100, mid: { x: 195, y: 252 }, view: home };
    const view = pinched(start, { spread: 100, mid: { x: 195 + 390 / 18, y: 252 } }, FIELD, bounds);
    expect(view.widthKm).toBe(18);
    expect(view.centre.x).toBeCloseTo(-1);
  });

  it('leaves the view alone while a spread is nought', () => {
    const start = { spread: 0, mid: { x: 195, y: 252 }, view: home };
    expect(pinched(start, { spread: 100, mid: start.mid }, FIELD, bounds)).toEqual(home);
  });

  it('holds the centre inside the reach and never bands it, so a release has nothing to spring back from', () => {
    // Zooming in around fingers 14 km east of the viewer at 30 km across (13 pt per km) asks
    // the centre to travel there; the reach is 10 km, and the centre stops at its edge.
    const wide = { centre: { x: 0, y: 0 }, widthKm: 30 };
    const mid = { x: 195 + 14 * (390 / 30), y: 252 };
    const view = pinched({ spread: 100, mid, view: wide }, { spread: 400, mid }, FIELD, bounds);
    expect(Math.hypot(view.centre.x, view.centre.y)).toBeCloseTo(10);
    expect(boundCentre(view.centre, 10)).toEqual(view.centre);
  });
});
