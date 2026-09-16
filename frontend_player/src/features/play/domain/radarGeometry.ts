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
  const below = WIDTH_LADDER_KM.filter((stop) => stop < widthKm - EPSILON);
  return below.length === 0 ? undefined : below[below.length - 1];
}

/**
 * The next stop **out** from a width — the narrowest stop strictly wider than it, and no wider
 * than the reach allows — or nothing at the end.
 */
export function nextStopOut(widthKm: number, widestKm: number): number | undefined {
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
  const closestUntil = held === 'closest' ? CLOSEST_AT_KM * (1 + DEAD_BAND) : CLOSEST_AT_KM;
  if (widthKm <= closestUntil + EPSILON) return 'closest';
  const closerUntil = held === 'closer' ? CLOSER_AT_KM * (1 + DEAD_BAND) : CLOSER_AT_KM;
  if (widthKm <= closerUntil + EPSILON) return 'closer';
  return 'wide';
}

/** Points per kilometre: the field's width over the view's. */
export function ptPerKm(field: FieldBox, widthKm: number): number {
  return field.width / widthKm;
}

/** The focus: where the view's centre is drawn, and where the viewer stands at home. */
export function focusOf(field: FieldBox): ScreenPoint {
  return { x: field.width / 2, y: field.height * FOCUS_SHARE };
}

/** A row's point on the plane from its distance and bearing — north up, clockwise. */
export function pointOf(row: RowPosition): KmPoint {
  const radians = (row.bearingDeg * Math.PI) / 180;
  return { x: row.distanceKm * Math.sin(radians), y: row.distanceKm * Math.cos(radians) };
}

/** Where a kilometre point is drawn under a view, on a field. */
export function toScreen(point: KmPoint, view: RadarView, field: FieldBox): ScreenPoint {
  const scale = ptPerKm(field, view.widthKm);
  const focus = focusOf(field);
  return {
    x: focus.x + (point.x - view.centre.x) * scale,
    y: focus.y - (point.y - view.centre.y) * scale,
  };
}

/** The kilometre point under a screen point — the inverse of {@link toScreen}, for the pinch. */
export function toKm(point: ScreenPoint, view: RadarView, field: FieldBox): KmPoint {
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
  const scale = ptPerKm(field, widthKm);
  const widest = field.width * RING_MAX_RADIUS_WIDTHS;
  return RING_SERIES_KM.flatMap((km) => {
    const radiusPt = km * scale;
    return radiusPt >= RING_MIN_RADIUS_PT && radiusPt <= widest ? [{ km, radiusPt }] : [];
  });
}

/** Whether a **point** — the spot, never the card drawn from it — lies inside the field (§7.7). */
export function inView(point: ScreenPoint, field: FieldBox): boolean {
  return point.x >= 0 && point.x <= field.width && point.y >= 0 && point.y <= field.height;
}

/** How much of a drag past the reach's edge the field follows — the rubber band's give (§7.6). */
const RUBBER = 0.35;

/**
 * The centre held inside the reach: a pan **rubber-bands when the reach's edge reaches the
 * screen's centre** (§7.6), which is the moment the focus would leave the disc of the reach.
 */
export function boundCentre(centre: KmPoint, reachKm: number): KmPoint {
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
  const bound = boundCentre(centre, reachKm);
  return { x: bound.x + (centre.x - bound.x) * RUBBER, y: bound.y + (centre.y - bound.y) * RUBBER };
}

/** Where a tap on a face flies: centred on the row, at the 3 km stop (§7.5). */
export function flyToView(row: RowPosition): RadarView {
  return { centre: pointOf(row), widthKm: FLY_TO_WIDTH_KM };
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
  const at = (a: number, b: number) => a + (b - a) * progress;
  return { scale: at(from.scale, to.scale), x: at(from.x, to.x), y: at(from.y, to.y) };
}
