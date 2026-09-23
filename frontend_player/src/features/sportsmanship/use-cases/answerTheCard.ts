/**
 * **One card, answered once** — and the court is what the answer is read against.
 *
 * The stars a player gave are held as a draft keyed by player id; what crosses is that draft
 * **read through the card's own list**, in the line-up's order. That is the whole of the rule
 * here and it is the reason this is a use-case rather than a direct call: stars for somebody
 * who was not on that court cannot be sent, because they are never assembled.
 *
 * The answer is dropped because there is none — a `204`, and *nothing is returned, and nothing
 * ever will be*: there is no route through which an individual answer reaches anybody,
 * including the person who gave it.
 */

import { postCardAnswer } from '../api/sportsmanshipApi';
import type { OpenCard } from '../domain/card';
import { starsGiven, type StarsDraft } from '../domain/stars';
import { toAnswerTheCardRequest } from '../mappers/sportsmanshipMappers';

export interface CardAnswer {
  readonly card: OpenCard;
  readonly draft: StarsDraft;
}

export async function answerTheCard({ card, draft }: CardAnswer): Promise<void> {
  await postCardAnswer(card.gameId, toAnswerTheCardRequest(starsGiven(draft, card.players)));
}
