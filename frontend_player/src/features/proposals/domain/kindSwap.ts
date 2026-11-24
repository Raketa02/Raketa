/**
 * **The Games deck swapped to its other kind, in place** ([#863](https://github.com/Raketa02/Raketa/issues/863),
 * PRD #859; the tab menu log §5.1–§5.2) — the rules of a pick from the Games tab's menu, which
 * `GamesDeck` draws and times. Pure.
 *
 * **Two phases.** The stack **goes out** — the kind left is still the one drawn, sliding down and
 * fading — and then the kind picked **comes in**, rising into the same place once its read is in;
 * until it is, the stack is **away** and today's spinner stands in its place. Then the swap is over,
 * and only then does the deck take an answer: no answer reaches the stack going out, and the stack
 * coming in answers once it has landed.
 *
 * **Only the cards move; the buttons stay** — they mean the same thing on both kinds — wherever
 * both sides of the swap have them: the kind left dealt a card, and the kind picked **promises**
 * one, by the count its line in the menu shows. The count rather than its read, because the read of
 * a kind not picked before is not in yet when the stack goes out, and the menu has already said how
 * many cards it deals. Where one side has none — the group's starting card, *Nothing picked right
 * now* — the buttons fade out with the stack going out, or fade in with the stack coming in. A count
 * the read then contradicts is the read's to settle: cards where it said none fade the buttons in,
 * and none where it said some leave the starting card with no buttons, as ever.
 *
 * **Only a pick moves anything.** A kind moved by a notice, or by finding landing after the door's
 * answer, is drawn directly — no swap is begun for it.
 */

import type { DeckSegment } from './deck';
import type { GameKind } from './vocabulary';

/** Where a swap stands: the stack going out, or the kind picked coming in. */
export type SwapPhase = 'out' | 'in';

/** A pick from the menu, under way — see the module note. */
export interface KindSwap {
  /** The kind drawn when the other was picked — still drawn while its stack goes out. */
  readonly from: GameKind;
  readonly phase: SwapPhase;
  /** The buttons were drawn under the stack going out: it dealt a card. */
  readonly held: boolean;
  /** The kind picked promises a card — its count in the menu is above nought. */
  readonly promised: boolean;
}

/** What stands where the stack stands — the cards, the starting card, or a read on its way. */
export type StackDrawn = 'cards' | 'nothing' | 'reading';

/**
 * How the stack's layer moves: at rest, going out, away while the kind picked is read, or coming in.
 */
export type StackMotion = 'rest' | 'out' | 'away' | 'in';

/** How the buttons are drawn: not at all, kept as they are, fading out, or fading in. */
export type ButtonsMotion = 'none' | 'kept' | 'out' | 'in';

/** The deck as it stands at a pick: the kind drawn, whether it has the buttons, and the counts. */
export interface DrawnAtThePick {
  readonly from: GameKind;
  /** What stands where the stack stands — today's spinner has no stack to send out. */
  readonly stack: StackDrawn;
  /** The buttons are drawn now. */
  readonly held: boolean;
  /** Both kinds' counts — the menu's, off the reads it is drawn from. */
  readonly kinds: readonly DeckSegment[] | undefined;
}

/**
 * **The swap a pick of `to` begins.** While the stack is still going out, the pick only changes
 * where it lands — the kind going out and the clock it goes on are unchanged; otherwise it begins
 * again from what is drawn now. **From today's spinner it comes straight in**: there is no stack to
 * send out, and the kind picked rises as soon as it is read — at once, where it was read before.
 */
export function swapTo(swap: KindSwap | undefined, drawn: DrawnAtThePick, to: GameKind): KindSwap {
  const promised = (drawn.kinds?.find((segment) => segment.kind === to)?.count ?? 0) > 0;
  if (swap?.phase === 'out') return { ...swap, promised };
  const phase = drawn.stack === 'reading' ? 'in' : 'out';
  return { from: drawn.from, phase, held: drawn.held, promised };
}

/** The kind the deck draws: the one it leaves while its stack goes out, else the one chosen. */
export function kindDrawn(swap: KindSwap | undefined, chosen: GameKind): GameKind {
  return swap?.phase === 'out' ? swap.from : chosen;
}

/** How the stack moves now — `landed` is whether the kind drawn has been read. */
export function stackMotion(swap: KindSwap | undefined, landed: boolean): StackMotion {
  if (swap === undefined) return 'rest';
  if (swap.phase === 'out') return 'out';
  return landed ? 'in' : 'away';
}

/** Whether the deck takes an answer — never while a swap is under way. */
export function takesAnswers(swap: KindSwap | undefined): boolean {
  return swap === undefined;
}

/** How the buttons are drawn under what stands where the stack stands — see the module note. */
export function buttonsMotion(swap: KindSwap | undefined, drawn: StackDrawn): ButtonsMotion {
  if (swap === undefined) return drawn === 'cards' ? 'kept' : 'none';
  const stay = swap.held && swap.promised;
  if (drawn === 'nothing') return 'none';
  if (drawn === 'reading') return stay ? 'kept' : 'none';
  if (stay) return 'kept';
  return swap.phase === 'out' ? 'out' : 'in';
}
