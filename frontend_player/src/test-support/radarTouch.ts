/**
 * Fingers on the radar's field, as a test can move them — one for a drag, two for a pinch.
 *
 * The field's pan and pinch are `react-native-gesture-handler`'s (ADR-0176 §2), and Jest does
 * no hit testing and moves no finger, so the two gestures are fired through the library's own
 * `fireGestureHandler`, found by the test ids the field gives them, in the order the recogniser
 * would call them: began, active, the moves, ended. Under reanimated's jest setup every
 * callback runs on the JavaScript thread against the same shared values the field draws from,
 * so what a walk reads afterwards is the field as the gesture left it.
 *
 * The pan claims a touch only after the intent distance, and where it is claimed is where the
 * drag is anchored (§7.6): a `drag` therefore lands its first active event one step past the
 * intent distance along the drag's own line, and the travel that moves the view is `to` less
 * that step — the recogniser's own arithmetic, kept so a walk's kilometres mean what they say.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { act } from '@testing-library/react-native';
import { State } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';
import type {
  PanGesture,
  PinchGesture,
  PanGestureHandlerEventPayload,
  PinchGestureHandlerEventPayload,
} from 'react-native-gesture-handler';

export type Point = readonly [number, number];

/** The field's two gestures, by the test ids `radar/RadarField` gives them. */
const RADAR_PAN_GESTURE = 'radar-pan';
const RADAR_PINCH_GESTURE = 'radar-pinch';

/** The step past the intent distance at which the pan is claimed and the drag anchored. */
const CLAIMED_AT = 13;

/** One finger, dragged from `from` to `to` and lifted there. */
export function drag(from: Point, to: Point): void {
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const way = Math.hypot(dx, dy);
  if (way === 0) return;
  const step: Point = [from[0] + (dx / way) * CLAIMED_AT, from[1] + (dy / way) * CLAIMED_AT];
  const at = (point: Point) => ({
    x: point[0],
    y: point[1],
    absoluteX: point[0],
    absoluteY: point[1],
    translationX: point[0] - from[0],
    translationY: point[1] - from[1],
    velocityX: 0,
    velocityY: 0,
  });
  act(() => {
    fireGestureHandler<PanGesture>(getByGestureTestId(RADAR_PAN_GESTURE), [
      { state: State.BEGAN, ...at(from) },
      { state: State.ACTIVE, ...at(step) },
      at(to),
      { state: State.END, ...at(to) },
    ] satisfies Partial<PanGestureHandlerEventPayload & { state: State }>[]);
  });
  spoken();
}

/**
 * Two fingers, from one spread to another, and lifted.
 *
 * The pinch is claimed where the fingers first are — their midpoint is the point the zoom is
 * around — and every later event carries the spread as a factor of the first, which is what
 * the recogniser reports.
 */
/**
 * A pinch, as either recogniser reports one: began and active at the fingers' first spread,
 * one move to their last, ended there — both fingers lifting together.
 *
 * `activatesAt` is the scale the recogniser has already reached when it activates — 1 by
 * default, as the jest utilities and iOS report it; Android activates only once the fingers
 * have moved a slop, so it reports the ratio it has reached by then, and every later scale is
 * measured from the true start rather than from that activation.
 */
export function pinch(
  from: readonly [Point, Point],
  to: readonly [Point, Point],
  options: { readonly activatesAt?: number } = {},
): void {
  const activatesAt = options.activatesAt ?? 1;
  const scale = activatesAt * spreadRatio(from, to);
  act(() => {
    fireGestureHandler<PinchGesture>(getByGestureTestId(RADAR_PINCH_GESTURE), [
      { state: State.BEGAN, scale: 1, velocity: 0, ...mid(from) },
      { state: State.ACTIVE, scale: activatesAt, velocity: 0, ...mid(from) },
      { scale, velocity: 0, ...mid(to) },
      { state: State.END, scale, velocity: 0, ...mid(to) },
    ] satisfies Partial<PinchGestureHandlerEventPayload & { state: State }>[]);
  });
  spoken();
}

/**
 * A pinch whose fingers lift one after the other, as **Android** reports it: the recogniser
 * does not end when the first finger lifts — it stays active on the one that remains, with
 * one pointer, and reports *that finger* as the focal point, half a spread from the midpoint
 * it was reporting a frame earlier. `stays` is the index of the finger that lifts last; its
 * last position is the one-pointer event's focal point, and the end's.
 */
export function pinchLiftingOneFingerFirst(
  from: readonly [Point, Point],
  to: readonly [Point, Point],
  stays: 0 | 1,
): void {
  const scale = spreadRatio(from, to);
  const finger = { focalX: to[stays][0], focalY: to[stays][1] };
  act(() => {
    fireGestureHandler<PinchGesture>(getByGestureTestId(RADAR_PINCH_GESTURE), [
      { state: State.BEGAN, scale: 1, velocity: 0, ...mid(from) },
      { state: State.ACTIVE, scale: 1, velocity: 0, ...mid(from) },
      { scale, velocity: 0, ...mid(to) },
      { scale, velocity: 0, numberOfPointers: 1, ...finger },
      { state: State.END, scale, velocity: 0, numberOfPointers: 1, ...finger },
    ] satisfies Partial<
      PinchGestureHandlerEventPayload & { state: State; numberOfPointers: number }
    >[]);
  });
  spoken();
}

const spread = (pair: readonly [Point, Point]) =>
  Math.hypot(pair[0][0] - pair[1][0], pair[0][1] - pair[1][1]);

/** The fingers' spread now over their spread at first — the recogniser's `scale`. */
function spreadRatio(from: readonly [Point, Point], to: readonly [Point, Point]): number {
  const first = spread(from);
  return first === 0 ? 1 : spread(to) / first;
}

/** The fingers' midpoint, as the recogniser reports the focal point while both are down. */
const mid = (pair: readonly [Point, Point]) => ({
  focalX: (pair[0][0] + pair[1][0]) / 2,
  focalY: (pair[0][1] + pair[1][1]) / 2,
});

/**
 * Let the field's words land: the UI thread tells JavaScript the width and the count through
 * `runOnJS`, which under jest is a microtask the fake clock holds until it is advanced — by
 * nothing at all, since the words are not an animation.
 */
function spoken(): void {
  act(() => {
    jest.advanceTimersByTime(0);
  });
}

/** How far a finger has to travel before the pan claims it — a press is never claimed. */
export function panClaimsAfter(): number | undefined {
  const pan = getByGestureTestId(RADAR_PAN_GESTURE) as PanGesture;
  return pan.config.minDist;
}
