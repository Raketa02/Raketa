/**
 * **The fill, bound to one screen that says yes** — the deck and a game's details ask it the same
 * four things, for the deck the card was dealt in and the screen to leave once a yes books
 * ([#555](https://github.com/Raketa02/Raketa/issues/555)).
 *
 * | | |
 * | --- | --- |
 * | `setUpFirst` | nothing saved: the setup opens, and `then` lands the yes once a method is |
 * | `waits` | this yes would wait behind *Undo* — and `held` that it must wait for another to go first |
 * | `book` | the ten seconds in front of it |
 * | `confirm` | a refused share's confirmation, opened on the details (#557) |
 * | `onAnswered`, `takesRefusal` | the deck's own answer handed to the fill |
 *
 * The screen keeps what differs — the deck's card flies, the details mark the yes in place.
 */

import { usePaymentSetupNeeded } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';

import { waitsForUndo, type DealtIn, type YesAnswer, type YesOn } from '../domain/fill';

import { useFill } from './useFill';
import type { AnswerOnCard } from './useGroupDeck';

export function useFillYes(dealtIn: DealtIn, leave?: () => void) {
  const fill = useFill();
  const setupNeeded = usePaymentSetupNeeded();
  const where = leave === undefined ? { dealtIn } : { dealtIn, leave };

  return {
    /** The proposal counting down behind *Undo*, anywhere — the deck hides its card. */
    counting: fill.counting,
    /** Nothing is saved: open the setup, and run `then` once a method is. `true` when it opened. */
    setUpFirst: (then: () => void): boolean => {
      if (setupNeeded !== true) return false;
      fill.setUpThen(then);
      return true;
    },
    /** A yes on this card moves money, and waits ten seconds behind *Undo*. */
    waits: (card: YesOn): boolean => waitsForUndo(card),
    /** It waits — and another booking is counting already, so it must wait for that one. */
    held: (card: YesOn): boolean => waitsForUndo(card) && fill.counting !== null,
    book: (card: YesOn) => fill.book({ ...where, card }),
    /** A refused share of this player's on this game — the confirmation, and the yes it carries. */
    confirm: (seatChargeId: string, card: YesOn) => fill.confirm({ ...where, card, seatChargeId }),
    onAnswered: (answer: YesAnswer, asked: AnswerOnCard) => {
      if (asked.card !== undefined) fill.answered(answer, { ...where, card: asked.card });
    },
    /** A refusal the fill mends itself; `retry` lands the yes again once it is mended. */
    takesRefusal: (error: AppError, asked: AnswerOnCard, retry: () => void): boolean =>
      asked.card !== undefined && fill.refused(error, { ...where, card: asked.card }, retry),
  };
}
