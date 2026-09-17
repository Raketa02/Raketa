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
export function pinch(from: readonly [Point, Point], to: readonly [Point, Point]): void {
  const spread = (pair: readonly [Point, Point]) =>
    Math.hypot(pair[0][0] - pair[1][0], pair[0][1] - pair[1][1]);
  const mid = (pair: readonly [Point, Point]) => ({
    focalX: (pair[0][0] + pair[1][0]) / 2,
    focalY: (pair[0][1] + pair[1][1]) / 2,
  });
  const first = spread(from);
  const scale = first === 0 ? 1 : spread(to) / first;
  act(() => {
    fireGestureHandler<PinchGesture>(getByGestureTestId(RADAR_PINCH_GESTURE), [
      { state: State.BEGAN, scale: 1, velocity: 0, ...mid(from) },
      { state: State.ACTIVE, scale: 1, velocity: 0, ...mid(from) },
      { scale, velocity: 0, ...mid(to) },
      { state: State.END, scale, velocity: 0, ...mid(to) },
    ] satisfies Partial<PinchGestureHandlerEventPayload & { state: State }>[]);
  });
  spoken();
}

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
