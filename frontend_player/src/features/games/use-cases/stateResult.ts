/**
 * *This is the score.* The one write that records a game happened, and the two that argue
 * about it.
 *
 * **The client does not name the act.** The record decides whether this is an entry, a
 * correction or a counter, and that is the contract's own decision rather than a convenience:
 * a mislabelled correction is a proposal nobody may make. What the client decides is what to
 * draw before the tap, which is `domain/conversation.ts`.
 *
 * **The answer is deliberately dropped.** `POST /result` replies with the game as it now
 * stands, and writing that into the list would splice a standing folded against the server's
 * clock into a list folded against an older `read_at` — two readings of the clock in one list,
 * which is the one thing that field exists to prevent. So the caller invalidates and the next
 * read is one fold over everything, which is `challenges`' own answer to the same question.
 */

import { postResult } from '../api/gamesApi';
import type { Score } from '../domain/game';
import { toStateResultRequest } from '../mappers/gameMappers';

export interface StatedResult {
  readonly gameId: string;
  readonly score: Score;
}

export async function stateResult({ gameId, score }: StatedResult): Promise<void> {
  await postResult(gameId, toStateResultRequest(score));
}
