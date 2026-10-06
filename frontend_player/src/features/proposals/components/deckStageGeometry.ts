/**
 * The deck drag's arithmetic — which move is a drag, where a release commits, which answer a
 * direction is, and how the stamps and the turn follow the finger. No React in any of it.
 *
 * Kept apart from `DeckStage` for `swipeRowGeometry`'s reason: a rule about numbers is testable
 * as numbers, and a rule that only exists inside a `PanResponder` callback is one a test can
 * reach only by driving touches at a rendered tree. What the component does is attach these to
 * the finger; what is decided is here.
 *
 * ## Which touch is a drag
 *
 * The page scrolls down the screen and the card drags across it, and the same finger begins
 * both. The stage does **not** claim the touch when it lands — a tap has to stay a tap and a
 * long press a long press on the card, which is the door to the record — and does not claim on
 * the first pixel of movement either, because every thumb drifts. It claims once the finger has
 * travelled the swipe row's own intent distance across **and** further across than down, in
 * **either** direction: a drag right is *Let's play* and a drag left is *Not today*
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §3).
 *
 * ## Where a release commits
 *
 * The stamp fades in with the drag and is full at `commit` — the mock's 95 — past which a
 * release commits the answer and the card flies; short of it the card settles back. One number
 * for both, so what a player sees as *full* is exactly what a release acts on.
 *
 * ## A yes goes right
 *
 * The two buttons' own order, and the same sign the leaving animation has always used: the
 * direction is the whole of what the answer changes, and it is held as a sign rather than as
 * two interpolations so the one mid-flight when a refusal returns the card is the one reset.
 *
 * ## The stack, and how it advances
 *
 * Each card behind the top one sits one `step` lower and one `shrink` smaller than the one in
 * front, and **the whole stack draws one step further back while the top card is arriving**:
 * the top card arrives from the place the card behind it stood, and the card behind it from the
 * place the one behind *that* stood, so a card leaving is followed by every card coming forward
 * as one motion, and nothing jumps.
 *
 * **Each card behind is fainter as well as smaller** (Q90 of the Games grilling, #553): one
 * `fade` step of opacity per place back, drawn off the same arrival, so the card coming forward
 * brightens as it grows and the queue reads as behind rather than as three cards of one weight.
 */

import { theme } from '@/shared/ui/theme';

/**
 * The two answers, as the two ways off the stage. **Named for the answer and not for the
 * direction**: which way a yes goes is this file's decision, and a prop spelling it `'right'`
 * would put that decision in every caller.
 */
export type DeckExit = 'yes' | 'no';

const { commit, intent, tilt: TILT } = theme.size.deckSwipe;

/** Where the stamp is full and a release commits — see the module note. */
export const COMMIT = commit;

/** A finger's travel since the touch began, in points — `PanResponder`'s own `dx` and `dy`. */
export interface Travel {
  readonly dx: number;
  readonly dy: number;
}

/**
 * Whether this move makes the touch a drag on the card — see the module note.
 *
 * The comparison is strict: a move exactly as far down as across is the page's. A tie has to go
 * somewhere, and it goes to the gesture that would be the worse one to steal.
 */
export function claimsTheDrag({ dx, dy }: Travel): boolean {
  const across = Math.abs(dx);
  return across >= intent && across > Math.abs(dy);
}

/** Whether the finger is at or past the threshold, either way. */
export function crossedThreshold(dx: number): boolean {
  return Math.abs(dx) >= COMMIT;
}

/** The answer a release at `dx` commits — or nothing, short of the threshold. */
export function committed(dx: number): DeckExit | undefined {
  if (!crossedThreshold(dx)) return undefined;
  return dx > 0 ? 'yes' : 'no';
}

/** A yes goes right and a pass goes left: the sign every departure is multiplied by. */
export function wayOf(said: DeckExit): 1 | -1 {
  return said === 'yes' ? 1 : -1;
}

/**
 * An `Animated` interpolation, as `Animated` takes one. **Mutable arrays**, deliberately: RN's
 * `InterpolationConfigType` is typed over `number[]`, and a `readonly` pair is not assignable
 * to it — `theme.tabular`'s own note, one type over. A fresh object per call, so nothing shares
 * a mutable range.
 */
export interface Interpolation<Out extends number | string> {
  inputRange: number[];
  outputRange: Out[];
  extrapolate: 'clamp';
}

/** From `dx` to the stamp's opacity, invisible at rest and full at the threshold. */
export function stampOpacity(said: DeckExit): Interpolation<number> {
  return said === 'yes'
    ? { inputRange: [0, COMMIT], outputRange: [0, 1], extrapolate: 'clamp' }
    : { inputRange: [-COMMIT, 0], outputRange: [1, 0], extrapolate: 'clamp' };
}

/** From `dx` to the card's turn, full at twice the threshold, in the drag's direction. */
export function tilt(): Interpolation<string> {
  return {
    inputRange: [-2 * COMMIT, 0, 2 * COMMIT],
    outputRange: [`-${TILT}deg`, '0deg', `${TILT}deg`],
    extrapolate: 'clamp',
  };
}

/**
 * The stack behind the top card: each card behind sits one `step` lower and `shrink` smaller
 * than the one in front — see the module note.
 */
export const STACK = { step: theme.space.sm, shrink: 0.05, fade: 0.3 } as const;

/**
 * From the top card's arrival (nought to one) to where a card at `depth` stands — one step
 * further back at nought, in its own place at one. Depth nought is the top card.
 */
export function stackLift(depth: number): Interpolation<number> {
  return {
    inputRange: [0, 1],
    outputRange: [(depth + 1) * STACK.step, depth * STACK.step],
    extrapolate: 'clamp',
  };
}

/** From the top card's arrival to a card's size at `depth` — one shrink smaller at nought. */
export function stackScale(depth: number): Interpolation<number> {
  return {
    inputRange: [0, 1],
    outputRange: [1 - (depth + 1) * STACK.shrink, 1 - depth * STACK.shrink],
    extrapolate: 'clamp',
  };
}

/**
 * From the top card's arrival to a card's opacity at `depth` — one fade fainter at nought, its own
 * at one. The top card is whole; the two behind it are drawn at 0,7 and 0,4.
 */
export function stackOpacity(depth: number): Interpolation<number> {
  return {
    inputRange: [0, 1],
    outputRange: [1 - (depth + 1) * STACK.fade, 1 - depth * STACK.fade],
    extrapolate: 'clamp',
  };
}
