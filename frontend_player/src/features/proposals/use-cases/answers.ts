/**
 * **A player's answers to a card** — *I'm in*, *Not this time*, and *Withdraw*. Pass-throughs: the
 * rules that make an answer land — a saved method, a live yes to spare, a game still filling,
 * everybody In fitting everybody else — are the server's, and each refusal is named in its code.
 */

import { deleteYes, postNo, postYes } from '../api/proposalsApi';

/** Which of the two answers a card was given — named for the answer, as the stage names its exits. */
export type CardAnswer = 'yes' | 'no';

export interface AnswerToCard {
  readonly proposalId: string;
  readonly said: CardAnswer;
}

/** Send one answer. A yes answers how many seats are still open with it counted; a no, nothing. */
export async function answerCard({ proposalId, said }: AnswerToCard): Promise<void> {
  if (said === 'yes') {
    await postYes(proposalId);
    return;
  }
  await postNo(proposalId);
}

/** Take a yes back while the game is still filling. */
export function withdrawYes(proposalId: string): Promise<void> {
  return deleteYes(proposalId);
}
