/**
 * **A player's answers to a card** — *I'm in*, *Not this time*, *Withdraw*, and the yes again on a
 * payment confirmed in the app. Pass-throughs: the
 * rules that make an answer land — a saved method, a game still filling,
 * everybody In fitting everybody else — are the server's, and each refusal is named in its code.
 */

import {
  deleteYes,
  postNo,
  postPaymentConfirmation,
  postRescueNo,
  postSeat,
  postYes,
} from '../api/proposalsApi';
import type { YesAnswer } from '../domain/fill';
import { toYesAnswer } from '../mappers/fillMappers';

/** Which of the two answers a card was given — named for the answer, as the stage names its exits. */
export type CardAnswer = 'yes' | 'no';

export interface AnswerToCard {
  /** The proposal's id — or, on a rescue, its booking's. */
  readonly proposalId: string;
  readonly said: CardAnswer;
  /** A rescue (#545): the answer is the booking's — the seat taken and paid for, or a no to it. */
  readonly rescue: boolean;
}

/**
 * Send one answer. A yes answers what it left on the game — and, when it was the last, what the fill
 * did (`fillOutcome` reads it); a no answers nothing. **A rescue's yes takes the seat and pays at
 * once**, answered as a yes is.
 */
export async function answerCard({
  proposalId,
  said,
  rescue,
}: AnswerToCard): Promise<YesAnswer | null> {
  if (said === 'yes') {
    return toYesAnswer(await (rescue ? postSeat(proposalId) : postYes(proposalId)));
  }
  await (rescue ? postRescueNo(proposalId) : postNo(proposalId));
  return null;
}

/** *I confirmed my payment* — the player's yes again, answered as a yes is (#541). */
export async function confirmPayment(seatChargeId: string): Promise<YesAnswer> {
  return toYesAnswer(await postPaymentConfirmation(seatChargeId));
}

/** Take a yes back while the game is still filling. */
export function withdrawYes(proposalId: string): Promise<void> {
  return deleteYes(proposalId);
}
