/**
 * The swipe row's arithmetic, per design-system 6.15 — three rules, and no React in any of them.
 *
 * Kept apart from the component for `profileControlGeometry`'s reason: a rule about numbers is
 * testable as numbers, and a rule that only exists inside a `PanResponder` callback is one a test
 * can reach only by driving touches at a rendered tree. What the component does is attach these
 * to the finger; what is decided is here.
 *
 * ## Which touch is a swipe, and it is asked on every move until one answers yes
 *
 * A list scrolls down the screen and a row reveals across it, and the same finger begins both.
 * The row does **not** claim the touch when it lands — a tap has to stay a tap on the card, which
 * is a door — and does not claim it on the first pixel of movement either, because every thumb
 * drifts. It claims once the finger has travelled {@link theme.size.swipeRow.intent} across
 * **and** further across than down. Short of that, or steeper than that, the answer is *no* and
 * the list keeps its scroll: the horizontal threshold is what stops a reveal stealing a scroll,
 * and the comparison is what stops a diagonal doing it.
 *
 * Direction depends on where the card is. A closed row has nothing to its right, so only a move
 * to the left is a swipe on it; a revealed row closes by the opposite move, so either is.
 *
 * ## Where the card sits, and where it settles
 *
 * Under the finger the card follows it exactly — no elastic, no overshoot — between where it
 * started and the far edge of the control behind it. When the finger lifts, the card goes to one
 * of two places and never stays in between: **revealed** once it has been dragged half the
 * control's width, **closed** otherwise, so a nudge reveals nothing and a committed swipe reveals
 * the whole control rather than a sliver of it.
 */

import { theme } from './theme';

/** The two places a row can rest. */
export type SwipeRest = 'closed' | 'revealed';

/** A finger's travel since the touch began, in points — `PanResponder`'s own `dx` and `dy`. */
export interface Travel {
  readonly dx: number;
  readonly dy: number;
}

const { reveal: REVEAL, intent: INTENT } = theme.size.swipeRow;

/**
 * Whether this move makes the touch a swipe on the row — see the module note.
 *
 * The comparison is strict: a move exactly as far down as across is the list's. A tie has to go
 * somewhere, and it goes to the gesture that would be the worse one to steal.
 */
export function claimsTheSwipe({ dx, dy }: Travel, at: SwipeRest): boolean {
  const across = at === 'closed' ? -dx : Math.abs(dx);
  return across >= INTENT && across > Math.abs(dy);
}

/** Where the card sits for a finger at `x` — clamped to the control's width, never to the right. */
export function shifted(x: number): number {
  return Math.min(0, Math.max(-REVEAL, x));
}

/** Where a card released at `x` comes to rest. */
export function settlesTo(x: number): SwipeRest {
  return -x >= REVEAL / 2 ? 'revealed' : 'closed';
}
