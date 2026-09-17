/**
 * **The radar's geometry** — every rule about where something is on the field, as pure
 * arithmetic over a view and a box
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §7.2–7.7).
 *
 * The server serves a **distance** and a **bearing** per row, spot to spot, and the client
 * computes *no geometry beyond scaling* (ADR-0174 §2). This module is that scaling: kilometres
 * to points, a bearing to a point on a plane with north up, and the handful of rules the spec
 * states in numbers — the ladder of widths and its two bounds from the reach, the three states
 * a face is drawn in and the dead-band over their thresholds, which distance rings are drawn,
 * whether a point is in view, and where a tap on a face flies to. Every one of those numbers is
 * the spec's, and `radarGeometry.test.ts` holds each to it.
 *
 * ## The view is two kilometre-facts and nothing in points
 *
 * A {@link RadarView} is the kilometre point sitting at the field's **focus** and the width of
 * the field in kilometres. Nothing in it is a point value, so the same view on a wider phone
 * sees more of the same picture at the same scale — *widths in kilometres are the width of the
 * map field* (§7) — and the view a player left the radar at can be kept for the life of the
 * process without knowing which field it will be drawn on next.
 *
 * ## The focus is not the centre
 *
 * The viewer sits on the field's vertical **42 %** at home, *so the footer covers nobody*
 * (§7.2). That point is the **focus**: the kilometre point the view is centred on is drawn
 * there, ± and the flight zoom around it, and the viewer stands there at home. Zooming around
 * the field's true centre instead would walk the viewer down the screen with every press.
 *
 * ## The field carries its tiles on one transform
 *
 * The tiles are laid out **once**, at the home view's scale, and the field's one native-driven
 * transform carries them to wherever the live view is — a pan, a pinch, ± and the flight are
 * all that transform moving, and nothing is re-laid-out until a gesture ends
 * (`components/RadarField`). {@link containerTransform} is the arithmetic: for a live view and
 * the home view the tiles were laid out under, the scale about the field's centre and the
 * offset that put every base position exactly where {@link toScreen} says the live position
 * is. The test proves the two agree for any view.
 *
 * ## The arithmetic runs on the UI thread, so it is marked
 *
 * The field's pan, pinch and flight run **on the UI thread** (ADR-0176 §2): every function a
 * gesture or an animated style reads is a **worklet** — the `'worklet'` directive is the one
 * word Reanimated's compiler needs to carry a function across — and a worklet may only call
 * worklets. Nothing else about them changes: each is still pure arithmetic over a view and a
 * box, imports nothing, and `radarGeometry.test.ts` holds it on the JavaScript thread exactly as
 * before. The directive is a build fact about the caller, not a rule about the geometry.
 */

/** A row's position, as the server serves it: kilometres to one decimal and a compass bearing. */
export interface RowPosition {
  readonly distanceKm: number;
  /** 0–359, north 0, clockwise (ADR-0174 §2). */
  readonly bearingDeg: number;
}

/** A point on the kilometre plane, the viewer at the origin: `x` east, `y` north. */
export interface KmPoint {
  readonly x: number;
  readonly y: number;
}

/** A point on the field, in points from its top-left corner. */
export interface ScreenPoint {
  readonly x: number;
  readonly y: number;
}

/** The field's box, in points, between the header and the footer. */
export interface FieldBox {
  readonly width: number;
  readonly height: number;
}

/**
 * Where the radar is looking: the kilometre point at the focus, and how wide the field is.
 *
 * Two facts and no third. The selection is not here, because it is not a fact about where the
 * view is — it survives a zoom, a pan and a flight unchanged (`domain/reading`).
 */
export interface RadarView {
  readonly centre: KmPoint;
  readonly widthKm: number;
}

/** The stops of the width ladder, in kilometres across the field (§7.3). */
export const WIDTH_LADDER_KM: readonly number[] = [1.5, 3, 5.4, 10, 18, 30, 55, 110];

/** The narrowest view, at every reach. */
export const WIDTH_FLOOR_KM = 1.5;

/** The stop a tap on a face lands at (§7.5). */
export const FLY_TO_WIDTH_KM = 3;

/** The distance rings, in kilometres (§7.2). */
export const RING_SERIES_KM: readonly number[] = [1, 2, 5, 10, 20, 50];

/** A ring is drawn when its on-screen radius is at least this many points… */
export const RING_MIN_RADIUS_PT = 26;

/** …and at most this many field widths. */
export const RING_MAX_RADIUS_WIDTHS = 3.5;

/** Where the viewer sits at home: this share of the field's height down from the top. */
export const FOCUS_SHARE = 0.42;

/** The widest stop is the first at or above this many reaches… */
const WIDEST_REACHES = 2.2;

/** …and the opening stop the first at or above this many. */
const OPENING_REACHES = 1.8;

/** The two thresholds between the three states, in kilometres across (§7.3). */
const CLOSER_AT_KM = 10;
const CLOSEST_AT_KM = 5.4;

/** How far past a threshold a held state is kept — *about 3 %* — so a pinch resting on it does not flicker. */
const DEAD_BAND = 0.03;

/** A rounding hair: a width this close to a stop is that stop. */
const EPSILON = 1e-6;

/** The first stop at or above `km`, or the last stop where none is. */
function firstStopAtOrAbove(km: number): number {
  return WIDTH_LADDER_KM.find((stop) => stop >= km) ?? WIDTH_LADDER_KM[WIDTH_LADDER_KM.length - 1]!;
}

/** The widest stop the view may reach at this reach: the first at or above 2,2 × it. */
export function widestWidthKm(reachKm: number): number {
  return firstStopAtOrAbove(reachKm * WIDEST_REACHES);
}

/** The stop the radar opens at for this reach: the first at or above 1,8 × it, never past the widest. */
export function openingWidthKm(reachKm: number): number {
  return Math.min(firstStopAtOrAbove(reachKm * OPENING_REACHES), widestWidthKm(reachKm));
}

/** Home: the viewer at the focus, at the opening width. */
export function homeView(reachKm: number): RadarView {
  return { centre: { x: 0, y: 0 }, widthKm: openingWidthKm(reachKm) };
}

/**
 * The next stop **in** from a width — the widest stop strictly narrower than it — or nothing at
 * the floor. From a stop it is the stop below; from a pinch's width it is the snap.
 */
export function nextStopIn(widthKm: number): number | undefined {
  'worklet';
  const below = WIDTH_LADDER_KM.filter((stop) => stop < widthKm - EPSILON);
  return below.length === 0 ? undefined : below[below.length - 1];
}

/**
 * The next stop **out** from a width — the narrowest stop strictly wider than it, and no wider
 * than the reach allows — or nothing at the end.
 */
export function nextStopOut(widthKm: number, widestKm: number): number | undefined {
  'worklet';
  return WIDTH_LADDER_KM.find((stop) => stop > widthKm + EPSILON && stop <= widestKm + EPSILON);
}

/** The three states a player is drawn in (§7.3): a face, a face with their level, the card. */
export type ZoomState = 'wide' | 'closer' | 'closest';

/**
 * Which state a width demands — and, given the state held, whether it is kept.
 *
 * The thresholds are inclusive downwards: 10 is closer and 5,4 is closest, so a ± landing on a
 * stop always lands in the state the stop names. The dead-band lies **above** each threshold
 * only: a state already held survives until the width is 3 % past the threshold, and a state
 * not yet held is entered at the threshold itself. A pinch resting on 10 therefore does not
 * flicker, and the ladder is never contradicted.
 */
export function zoomState(widthKm: number, held?: ZoomState): ZoomState {
  'worklet';
  const closestUntil = held === 'closest' ? CLOSEST_AT_KM * (1 + DEAD_BAND) : CLOSEST_AT_KM;
  if (widthKm <= closestUntil + EPSILON) return 'closest';
  const closerUntil = held === 'closer' ? CLOSER_AT_KM * (1 + DEAD_BAND) : CLOSER_AT_KM;
  if (widthKm <= closerUntil + EPSILON) return 'closer';
  return 'wide';
}

/**
 * How one player is drawn: a face — wide, or with their level — or **the card, which is the
 * selection's alone** (ADR-0176 §3). The closest width draws the closer face for everybody but
 * the one tapped: a field of cards was a field nobody could use, so the card is a thing one
 * player has at a time, at every width, and never a thing a width hands to everybody.
 */
export type TileState = 'wide' | 'closer' | 'card';

/** The tile a row is drawn as, from the zoom state and whether it is the selected one. */
export function tileState(zoom: ZoomState, selected: boolean): TileState {
  if (selected) return 'card';
  return zoom === 'wide' ? 'wide' : 'closer';
}

/** Points per kilometre: the field's width over the view's. */
export function ptPerKm(field: FieldBox, widthKm: number): number {
  'worklet';
  return field.width / widthKm;
}

/** The focus: where the view's centre is drawn, and where the viewer stands at home. */
export function focusOf(field: FieldBox): ScreenPoint {
  'worklet';
  return { x: field.width / 2, y: field.height * FOCUS_SHARE };
}

/** A row's point on the plane from its distance and bearing — north up, clockwise. */
export function pointOf(row: RowPosition): KmPoint {
  'worklet';
  const radians = (row.bearingDeg * Math.PI) / 180;
  return { x: row.distanceKm * Math.sin(radians), y: row.distanceKm * Math.cos(radians) };
}

/** Where a kilometre point is drawn under a view, on a field. */
export function toScreen(point: KmPoint, view: RadarView, field: FieldBox): ScreenPoint {
  'worklet';
  const scale = ptPerKm(field, view.widthKm);
  const focus = focusOf(field);
  return {
    x: focus.x + (point.x - view.centre.x) * scale,
    y: focus.y - (point.y - view.centre.y) * scale,
  };
}

/** The kilometre point under a screen point — the inverse of {@link toScreen}, for the pinch. */
export function toKm(point: ScreenPoint, view: RadarView, field: FieldBox): KmPoint {
  'worklet';
  const scale = ptPerKm(field, view.widthKm);
  const focus = focusOf(field);
  return {
    x: view.centre.x + (point.x - focus.x) / scale,
    y: view.centre.y - (point.y - focus.y) / scale,
  };
}

/** One distance ring, as drawn: its kilometres, and its radius on this field under this view. */
export interface Ring {
  readonly km: number;
  readonly radiusPt: number;
}

/** The rings the rule selects at this width: radius ≥ 26 pt and ≤ 3,5 field widths (§7.2). */
export function ringsFor(field: FieldBox, widthKm: number): readonly Ring[] {
  'worklet';
  const scale = ptPerKm(field, widthKm);
  const widest = field.width * RING_MAX_RADIUS_WIDTHS;
  return RING_SERIES_KM.flatMap((km) => {
    const radiusPt = km * scale;
    return radiusPt >= RING_MIN_RADIUS_PT && radiusPt <= widest ? [{ km, radiusPt }] : [];
  });
}

/** Whether a **point** — the spot, never the card drawn from it — lies inside the field (§7.7). */
export function inView(point: ScreenPoint, field: FieldBox): boolean {
  'worklet';
  return point.x >= 0 && point.x <= field.width && point.y >= 0 && point.y <= field.height;
}

/** How much of a drag past the reach's edge the field follows — the rubber band's give (§7.6). */
const RUBBER = 0.35;

/**
 * The centre held inside the reach: a pan **rubber-bands when the reach's edge reaches the
 * screen's centre** (§7.6), which is the moment the focus would leave the disc of the reach.
 */
export function boundCentre(centre: KmPoint, reachKm: number): KmPoint {
  'worklet';
  const away = Math.hypot(centre.x, centre.y);
  if (away <= reachKm || away === 0) return centre;
  const pull = reachKm / away;
  return { x: centre.x * pull, y: centre.y * pull };
}

/**
 * Where the view is drawn **while the finger is still down** past the edge: the bound, plus a
 * share of what the finger asked for beyond it — resistance, so the edge is felt rather than
 * hit. On release the view settles to {@link boundCentre}.
 */
export function rubberBand(centre: KmPoint, reachKm: number): KmPoint {
  'worklet';
  const bound = boundCentre(centre, reachKm);
  return { x: bound.x + (centre.x - bound.x) * RUBBER, y: bound.y + (centre.y - bound.y) * RUBBER };
}

/**
 * Where a drag started: the finger's travel so far — the recogniser's own translation, which
 * it keeps continuous when a second finger lands or lifts — and the view under it. A travel
 * and not a position, because a position is the fingers' average and jumps by half their
 * spread the moment one of two lifts (ADR-0177 §1).
 */
export interface DragStart {
  readonly at: ScreenPoint;
  readonly view: RadarView;
}

/**
 * The view under a finger whose travel has grown from where a drag started — **no inertia**:
 * the field follows the finger exactly, and past the reach's edge it gives a little
 * (`rubberBand`) until the finger lifts (§7.6).
 */
export function dragged(
  start: DragStart,
  finger: ScreenPoint,
  field: FieldBox,
  reachKm: number,
): RadarView {
  'worklet';
  const scale = ptPerKm(field, start.view.widthKm);
  const centre = {
    x: start.view.centre.x - (finger.x - start.at.x) / scale,
    y: start.view.centre.y + (finger.y - start.at.y) / scale,
  };
  return { centre: rubberBand(centre, reachKm), widthKm: start.view.widthKm };
}

/** Where a pinch started: the fingers' first spread and midpoint, and the view under them. */
export interface PinchStart {
  readonly spread: number;
  readonly mid: ScreenPoint;
  readonly view: RadarView;
}

/**
 * The view under two fingers that have moved from where a pinch started — continuous between
 * the floor and the widest stop, and **around the fingers**: the kilometre point that was under
 * their first midpoint stays under their midpoint now (§7.3, §7.6). **Held inside the reach,
 * not banded**: a pinch that would carry the centre past the reach's edge stops at the edge,
 * so there is nothing to spring back from when the fingers lift — only a drag rubber-bands
 * (ADR-0177 §1).
 */
export function pinched(
  start: PinchStart,
  fingers: { readonly spread: number; readonly mid: ScreenPoint },
  field: FieldBox,
  bounds: { readonly reachKm: number; readonly widestKm: number },
): RadarView {
  'worklet';
  if (start.spread === 0 || fingers.spread === 0) return start.view;
  const widthKm = Math.min(
    bounds.widestKm,
    Math.max(WIDTH_FLOOR_KM, (start.view.widthKm * start.spread) / fingers.spread),
  );
  const under = toKm(start.mid, start.view, field);
  const scale = ptPerKm(field, widthKm);
  const focus = focusOf(field);
  const centre = {
    x: under.x - (fingers.mid.x - focus.x) / scale,
    y: under.y + (fingers.mid.y - focus.y) / scale,
  };
  return { centre: boundCentre(centre, bounds.reachKm), widthKm };
}

/**
 * Where a tap on a face flies: centred on the row, at the 3 km stop — or at the width already
 * held where that is narrower, so a tap at 1,5 km across never zooms **out** to show a card
 * (§7.5 as amended by ADR-0176 §3).
 */
export function flyToView(row: RowPosition, fromWidthKm: number = FLY_TO_WIDTH_KM): RadarView {
  'worklet';
  return { centre: pointOf(row), widthKm: Math.min(fromWidthKm, FLY_TO_WIDTH_KM) };
}

// ---------------------------------------------------------------------------
// Stacks at the floor
// ---------------------------------------------------------------------------

/** A row's id and position — all a stack needs to know about a player. */
export interface PlacedRow extends RowPosition {
  readonly playerId: string;
}

/**
 * A **stack**: players whose faces would still lie on one another at the floor, folded into
 * one marker that says how many (ADR-0177 §2). Two players are *too close* when their spots
 * are nearer, on the field, than one face is wide; the relation is taken across — A over B and
 * B over C is one stack of three — so a stack is exactly the set of faces a finger could not
 * tell apart.
 */
export interface Stack {
  /** The members' ids joined, in the served order: stable for as long as the membership is. */
  readonly id: string;
  /** The members' ids, in the served order — by drawn distance, then id. */
  readonly members: readonly string[];
  /** The mean of the members' spots: where the marker stands and the fan is centred. */
  readonly centre: KmPoint;
}

/** Whether a width is the floor — the narrowest the field goes, where a stack may form. */
export function atFloor(widthKm: number): boolean {
  'worklet';
  return widthKm <= WIDTH_FLOOR_KM + EPSILON;
}

/**
 * The stacks at a width: none above the floor — closer is always the answer there — and at
 * the floor, every group of two or more whose spots lie within `withinPt` of one another on
 * this field, taken across. `withinPt` is the face's own width, so the rule is *would they
 * overlap* and nothing looser; on a 390 pt field at the floor that is about 130 m.
 */
export function stacksAt(
  rows: readonly PlacedRow[],
  widthKm: number,
  field: FieldBox,
  withinPt: number,
): readonly Stack[] {
  if (!atFloor(widthKm) || rows.length < 2) return [];
  const scale = ptPerKm(field, widthKm);
  const points = rows.map(pointOf);
  // Union–find over the rows: two within the distance share a root.
  const root = rows.map((_, index) => index);
  const find = (index: number): number => {
    let at = index;
    while (root[at] !== at) at = root[at]!;
    root[index] = at;
    return at;
  };
  for (let a = 0; a < rows.length; a += 1) {
    for (let b = a + 1; b < rows.length; b += 1) {
      const apart = Math.hypot(points[a]!.x - points[b]!.x, points[a]!.y - points[b]!.y) * scale;
      if (apart < withinPt) root[find(b)] = find(a);
    }
  }
  const groups = new Map<number, number[]>();
  rows.forEach((_, index) => {
    const at = find(index);
    const group = groups.get(at);
    if (group === undefined) groups.set(at, [index]);
    else group.push(index);
  });
  const stacks: Stack[] = [];
  for (const group of groups.values()) {
    if (group.length < 2) continue;
    const members = group.map((index) => rows[index]!.playerId);
    const sum = group.reduce(
      (acc, index) => ({ x: acc.x + points[index]!.x, y: acc.y + points[index]!.y }),
      { x: 0, y: 0 },
    );
    stacks.push({
      id: members.join('+'),
      members,
      centre: { x: sum.x / group.length, y: sum.y / group.length },
    });
  }
  return stacks;
}

/** One member of an opened stack, and the spot they are drawn at while it is open. */
export interface Fanned {
  readonly playerId: string;
  readonly at: KmPoint;
}

/**
 * How a stack **opens**: its members fanned out around the marker on rings, the first ring
 * `clearPt` from the centre and each ring `stepPt` further out, `stepPt` apart along the ring,
 * from north clockwise — so no fanned face lies on the marker, on another face, or on its
 * neighbour. A ring holds as many as fit at that spacing; the next ring takes the rest. Laid
 * out in points at the floor's scale, since a stack exists nowhere else, and returned as
 * kilometre points so the fanned face rides the field's transform like any other tile.
 */
export function fanOut(
  stack: Stack,
  field: FieldBox,
  layout: { readonly clearPt: number; readonly stepPt: number },
): readonly Fanned[] {
  const scale = ptPerKm(field, WIDTH_FLOOR_KM);
  const fanned: Fanned[] = [];
  let next = 0;
  for (let ring = 0; next < stack.members.length; ring += 1) {
    const radiusPt = layout.clearPt + ring * layout.stepPt;
    const capacity = Math.max(1, Math.floor((2 * Math.PI * radiusPt) / layout.stepPt));
    const seats = Math.min(capacity, stack.members.length - next);
    for (let seat = 0; seat < seats; seat += 1) {
      const bearing = (seat * 2 * Math.PI) / seats;
      fanned.push({
        playerId: stack.members[next + seat]!,
        at: {
          x: stack.centre.x + (radiusPt * Math.sin(bearing)) / scale,
          y: stack.centre.y + (radiusPt * Math.cos(bearing)) / scale,
        },
      });
    }
    next += seats;
  }
  return fanned;
}

/** The field's transform: a scale about its centre and an offset, both in points. */
export interface ContainerTransform {
  readonly scale: number;
  readonly x: number;
  readonly y: number;
}

/**
 * The transform that carries tiles laid out under `base` to where `live` draws them.
 *
 * With `c` the field's centre, a tile at base position `b` lands at `c + t + k·(b − c)`; the
 * scale `k` is the ratio of the two widths and `t` is what is left once the focus and the two
 * centres are accounted for. See the module note, and the test that holds it to `toScreen`.
 */
export function containerTransform(
  live: RadarView,
  base: RadarView,
  field: FieldBox,
): ContainerTransform {
  'worklet';
  const scale = base.widthKm / live.widthKm;
  const liveScale = ptPerKm(field, live.widthKm);
  const focus = focusOf(field);
  const centre = { x: field.width / 2, y: field.height / 2 };
  // `live − base` rather than `−(base − live)`, so a view at home is the identity and not a
  // negative nought — `Object.is(-0, 0)` is false, and a store comparing views would see a move.
  const shift = {
    x: (base.centre.x - live.centre.x) * liveScale,
    y: (live.centre.y - base.centre.y) * liveScale,
  };
  return {
    scale,
    x: (1 - scale) * (focus.x - centre.x) + shift.x,
    y: (1 - scale) * (focus.y - centre.y) + shift.y,
  };
}

/**
 * The view a transform draws — {@link containerTransform} run backwards, for the flight.
 *
 * A flight interpolates the **transform** linearly, on the native driver, from where the view
 * is to where the tap sends it; the rings and the footer follow in JavaScript and have to agree
 * with it frame for frame, so they read the view off the same interpolated transform rather
 * than interpolating the view on their own. `radarGeometry.test.ts` holds the round trip.
 */
export function viewFromTransform(
  transform: ContainerTransform,
  base: RadarView,
  field: FieldBox,
): RadarView {
  'worklet';
  const widthKm = base.widthKm / transform.scale;
  const liveScale = ptPerKm(field, widthKm);
  const focus = focusOf(field);
  const centre = { x: field.width / 2, y: field.height / 2 };
  const shiftX = transform.x - (1 - transform.scale) * (focus.x - centre.x);
  const shiftY = transform.y - (1 - transform.scale) * (focus.y - centre.y);
  return {
    centre: { x: base.centre.x - shiftX / liveScale, y: base.centre.y + shiftY / liveScale },
    widthKm,
  };
}

/** A point of the way from one transform to another — the flight's own arithmetic. */
export function betweenTransforms(
  from: ContainerTransform,
  to: ContainerTransform,
  progress: number,
): ContainerTransform {
  'worklet';
  const at = (a: number, b: number) => a + (b - a) * progress;
  return { scale: at(from.scale, to.scale), x: at(from.x, to.x), y: at(from.y, to.y) };
}
