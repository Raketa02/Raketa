/**
 * Fingers on the radar's field, as a test can move them — one for a drag, two for a pinch.
 *
 * `swipe.ts`'s discipline, over a surface that reads **two** touches: Jest does no hit testing
 * and moves no finger, so the field's `PanResponder` handlers are called directly, in the order
 * the responder system calls them — the capture negotiation on the touch down, the capture and
 * bubble on each move (the field claims on a move, never on the press, because a face and a
 * card are doors), the grant, the moves, the release. The field reads the fingers off
 * `nativeEvent.touches` and the responder reads its own arithmetic off `touchHistory`, so both
 * are built for every event.
 *
 * Page coordinates are field coordinates here: the field measures its place in the window
 * through `measureInWindow`, which the renderer never answers, so the origin stays at nought.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { act, type screen } from '@testing-library/react-native';

/** A rendered node, as the queries hand one back. */
type Node = ReturnType<typeof screen.getByTestId>;

type Responder =
  | 'onStartShouldSetResponderCapture'
  | 'onStartShouldSetResponder'
  | 'onMoveShouldSetResponderCapture'
  | 'onMoveShouldSetResponder'
  | 'onResponderGrant'
  | 'onResponderMove'
  | 'onResponderRelease';

export type Point = readonly [number, number];

let tick = 0;

/** Every finger on the glass, each having travelled from its `from` to its `to`. */
function fingers(moves: readonly (readonly [Point, Point])[]) {
  tick += 1;
  const touches = moves.map(([, to]) => ({ pageX: to[0], pageY: to[1] }));
  const [first] = touches;
  return {
    nativeEvent: {
      pageX: first?.pageX ?? 0,
      pageY: first?.pageY ?? 0,
      touches,
      changedTouches: touches,
    },
    touchHistory: {
      touchBank: moves.map(([from, to]) => ({
        touchActive: true,
        currentPageX: to[0],
        currentPageY: to[1],
        currentTimeStamp: tick,
        previousPageX: from[0],
        previousPageY: from[1],
        previousTimeStamp: tick - 1,
        startPageX: from[0],
        startPageY: from[1],
        startTimeStamp: 0,
      })),
      numberActiveTouches: moves.length,
      indexOfSingleActiveTouch: moves.length === 1 ? 0 : -1,
      mostRecentTimeStamp: tick,
    },
  };
}

function deliver(field: Node, name: Responder, event: ReturnType<typeof fingers>): unknown {
  let answer: unknown;
  act(() => {
    answer = (field.props[name] as (e: unknown) => unknown)(event);
  });
  return answer;
}

/** The touch lands, and the field is asked in the capture phase — where it resets what it knows. */
function down(field: Node, at: readonly Point[]): void {
  deliver(field, 'onStartShouldSetResponderCapture', fingers(at.map((p) => [p, p] as const)));
}

/**
 * A move, and whether it makes the touch the field's own.
 *
 * @returns whether the field claimed it.
 */
function claim(field: Node, moves: readonly (readonly [Point, Point])[]): boolean {
  deliver(field, 'onMoveShouldSetResponderCapture', fingers(moves));
  return deliver(field, 'onMoveShouldSetResponder', fingers(moves)) === true;
}

/**
 * One finger, dragged from `from` to `to` and lifted there.
 *
 * The claiming move is the first step; the field anchors the pan where it is granted, so the
 * travel that moves the view is `to` less that step. `steps` between the two lets a walk assert
 * a resting position mid-drag by reading the field between calls.
 *
 * @returns whether the field claimed the drag.
 */
export function drag(field: Node, from: Point, to: Point): boolean {
  down(field, [from]);
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const way = Math.hypot(dx, dy);
  if (way === 0) return false;
  // A step past the intent distance, along the drag's own line.
  const step: Point = [from[0] + (dx / way) * 13, from[1] + (dy / way) * 13];
  if (!claim(field, [[from, step]])) return false;
  deliver(field, 'onResponderGrant', fingers([[from, step]]));
  deliver(field, 'onResponderMove', fingers([[from, step]]));
  deliver(field, 'onResponderMove', fingers([[step, to]]));
  deliver(field, 'onResponderRelease', fingers([[to, to]]));
  return true;
}

/**
 * Two fingers, from one spread to another, and lifted.
 *
 * The first finger lands alone; the second joins on the first move, which is the move that
 * claims the touch for the field (two fingers claim at once, however little they travelled).
 * The field records the pair's first spread and midpoint on its first move as the responder,
 * and every later move is read against them.
 *
 * @returns whether the field claimed the pinch.
 */
export function pinch(
  field: Node,
  from: readonly [Point, Point],
  to: readonly [Point, Point],
): boolean {
  down(field, [from[0]]);
  const rest = [
    [from[0], from[0]],
    [from[1], from[1]],
  ] as const;
  if (!claim(field, rest)) return false;
  deliver(field, 'onResponderGrant', fingers(rest));
  deliver(field, 'onResponderMove', fingers(rest));
  deliver(
    field,
    'onResponderMove',
    fingers([
      [from[0], to[0]],
      [from[1], to[1]],
    ]),
  );
  deliver(
    field,
    'onResponderRelease',
    fingers([
      [to[0], to[0]],
      [to[1], to[1]],
    ]),
  );
  return true;
}

/** Whether the field answers the press itself — it never does; a face and a card are doors. */
export function claimsThePress(field: Node, at: Point): boolean {
  return deliver(field, 'onStartShouldSetResponder', fingers([[at, at]])) === true;
}
