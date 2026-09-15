/**
 * A finger on a swipe row, as a test can move it.
 *
 * Jest does no hit testing and moves no finger, so a swipe is driven at the responder handlers
 * the way `RadiusSlider.test.tsx` drives the slider's — but **not through `fireEvent`**, and the
 * reason is the row's own rule: `fireEvent` asks a responder's `onStartShouldSetResponder()`
 * before delivering anything to it and treats *no* as *disabled*, and *no on the press* is
 * exactly what a swipe row answers, because the card under the finger is a door and a tap has to
 * reach it. So the handlers are called directly, in the order the responder system calls them.
 *
 * **That order is the whole of what makes this worth having.** A touch down runs a *capture*
 * negotiation top-down, in which `PanResponder` resets what it knows about the gesture and the
 * card under the finger takes the press; every move runs the capture again, in which
 * `PanResponder` measures the move, and then a *bubble* in which the row is asked whether this
 * move makes the touch its own; a yes is followed by a grant, **from which the card follows the
 * finger** — the grant resets the measured travel — then moves, then a release. A helper that
 * skipped the capture would ask the row about a move it had never measured, and pass against a
 * row that never claims anything.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { act, type screen } from '@testing-library/react-native';

import { theme } from '@/shared/ui/theme';

/** A rendered node, as the queries hand one back. */
type Node = ReturnType<typeof screen.getByLabelText>;

type Responder =
  | 'onStartShouldSetResponderCapture'
  | 'onStartShouldSetResponder'
  | 'onMoveShouldSetResponderCapture'
  | 'onMoveShouldSetResponder'
  | 'onResponderGrant'
  | 'onResponderMove'
  | 'onResponderRelease'
  | 'onResponderTerminationRequest';

type Point = readonly [number, number];

/**
 * The surface a row's gesture is read on — the nearest ancestor of the card that decides whether
 * a move is a swipe. Found by that decision because it has no role and no name: it is not a
 * control, it is where a control's touch is negotiated. `undefined` for a row that does not swipe.
 */
export function gestureSurfaceOf(card: Node): Node | undefined {
  let node: Node | null = card;
  while (node !== null && node.props.onMoveShouldSetResponder === undefined) node = node.parent;
  return node ?? undefined;
}

let tick = 0;

/**
 * One finger, having travelled from `from` to `to` on the page.
 *
 * `touchHistory` is what `PanResponder` reads its `dx` and `dy` from — the difference between the
 * touch's previous and current page positions — and `mostRecentTimeStamp` has to advance on every
 * move or the responder treats the move as one it has already accounted for.
 */
function finger(from: Point, to: Point) {
  tick += 1;
  return {
    nativeEvent: {
      pageX: to[0],
      pageY: to[1],
      touches: [{ pageX: to[0], pageY: to[1] }],
      changedTouches: [],
    },
    touchHistory: {
      touchBank: [
        {
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
        },
      ],
      numberActiveTouches: 1,
      indexOfSingleActiveTouch: 0,
      mostRecentTimeStamp: tick,
    },
  };
}

function deliver(surface: Node, name: Responder, event: ReturnType<typeof finger>): unknown {
  let answer: unknown;
  act(() => {
    answer = (surface.props[name] as (e: unknown) => unknown)(event);
  });
  return answer;
}

const START: Point = [200, 300];

/**
 * The finger lands on `card`, and the card takes the press — the row is asked only in the
 * capture phase, where `PanResponder` resets what it knows about the gesture.
 */
export function touchDown(card: Node): void {
  const surface = gestureSurfaceOf(card);
  if (surface === undefined) return;
  deliver(surface, 'onStartShouldSetResponderCapture', finger(START, START));
}

/**
 * The finger moves `dx` across and `dy` down while the card holds the press, and the row is
 * asked whether that makes the touch its own.
 *
 * @returns whether the row claimed it — `false` for a row that does not swipe at all.
 */
export function moved(card: Node, dx: number, dy = 0): boolean {
  const surface = gestureSurfaceOf(card);
  if (surface === undefined) return false;
  const to: Point = [START[0] + dx, START[1] + dy];
  deliver(surface, 'onMoveShouldSetResponderCapture', finger(START, to));
  return deliver(surface, 'onMoveShouldSetResponder', finger(START, to)) === true;
}

/** Whether the row answers the press itself — a swipe row never does; the card is the door. */
export function claimsThePress(card: Node): boolean {
  const surface = gestureSurfaceOf(card);
  if (surface === undefined) return false;
  return deliver(surface, 'onStartShouldSetResponder', finger(START, START)) === true;
}

/** Whether the row would hand a claimed swipe back to the list mid-gesture. */
export function yieldsToTheList(card: Node): boolean {
  const surface = gestureSurfaceOf(card);
  if (surface === undefined) return true;
  return deliver(surface, 'onResponderTerminationRequest', finger(START, START)) !== false;
}

/**
 * A finger that has **not let go**: down, the move that claims it, and the travel — with the card
 * still under the thumb. What a stamp fading in with the drag is asserted against, since a whole
 * swipe has released before anything can be looked at. `release` lifts it.
 *
 * @returns whether the surface claimed the drag. A surface that does not drag is left untouched.
 */
export function dragTo(card: Node, travel: number): boolean {
  const surface = gestureSurfaceOf(card);
  if (surface === undefined) return false;

  const way = Math.sign(travel);
  const claimed: Point = [START[0] + way * theme.size.swipeRow.intent, START[1]];
  const end: Point = [claimed[0] + travel, START[1]];

  deliver(surface, 'onStartShouldSetResponderCapture', finger(START, START));
  deliver(surface, 'onMoveShouldSetResponderCapture', finger(START, claimed));
  if (deliver(surface, 'onMoveShouldSetResponder', finger(START, claimed)) !== true) return false;

  deliver(surface, 'onResponderGrant', finger(START, claimed));
  deliver(surface, 'onResponderMove', finger(claimed, end));
  held.set(card, end);
  return true;
}

/** The finger lifts where `dragTo` left it. */
export function release(card: Node): void {
  const surface = gestureSurfaceOf(card);
  const at = held.get(card);
  if (surface === undefined || at === undefined) return;
  held.delete(card);
  deliver(surface, 'onResponderRelease', finger(at, at));
}

/** Where each finger `dragTo` has not yet lifted is resting, so `release` lifts it from there. */
const held = new Map<Node, Point>();

/**
 * A whole swipe on `card`: down, the move that claims it, the travel that counts, and up.
 *
 * The claiming move travels exactly the intent distance in the swipe's direction; the grant
 * that follows is where the card starts following the finger, so **`travel` is what the finger
 * does after the row has claimed it** and is what the reveal threshold is measured against.
 *
 * @returns whether the row claimed the swipe. A row that does not swipe is left untouched.
 */
export function swipe(card: Node, travel: number): boolean {
  if (!dragTo(card, travel)) return false;
  release(card);
  return true;
}
