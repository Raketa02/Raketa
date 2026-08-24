/**
 * The two writes this screen can make, and what each one does to the caches.
 *
 * **Neither is retried.** The app's default for every mutation is `retry: false`,
 * and both of these are writes into an argument between four people: a retry the
 * client makes on its own is a request the player did not authorise. Neither
 * carries an idempotency key either, and that is the contract's own shape rather
 * than an omission — a second identical score from the same side is a **correction**
 * of her own live proposal, and a second acceptance comes back as the situation with
 * `mayAccept` false. Both are answered rather than applied twice, so there is
 * nothing for a key to protect.
 *
 * **Two cache writes and no invalidation**, which is `ADR-0074` end to end:
 *
 * - this screen's own answer, written straight in — the server has just recomposed
 *   it at the instant of the write, and asking again would be a second round trip
 *   for an answer already in hand;
 * - Now's update, handed to Now unread. Where a card sits on Now is Now's
 *   knowledge, so this hands over the card and never touches the composed screen
 *   itself.
 *
 * Invalidating either would turn every action into a refetch on the next focus,
 * which is the cost `ADR-0074` refused by name — and on Now it would also mean the
 * player watching the screen she came from rebuild itself.
 *
 * **No `onMutate`.** There is no optimistic update to write and never will be: what
 * a score does to the card is composed by the server from the record after the
 * write, and a phone that guessed at it would be holding the rules `ADR-0053`
 * leaves it none of — including the one that decides whether her tap settled the
 * result or merely put a second score on the table.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { writeNowUpdate } from '@/features/now/types';
import type { AppError } from '@/shared/errors';

import type { ResultAnswer } from '../domain/Result';
import { acceptResult } from '../use-cases/acceptResult';
import { proposeScore } from '../use-cases/proposeScore';

import { resultKeys } from './resultKeys';

/** What a write's answer corrects: this screen, and the card behind it. */
function applyAnswer(client: QueryClient, matchId: string, answer: ResultAnswer): void {
  client.setQueryData(resultKeys.screen(matchId), answer.screen);
  writeNowUpdate(client, answer.update);
}

/** The sets she typed, her side first. One send for entering, correcting and countering. */
export interface ScoreIntent {
  readonly sets: readonly (readonly [number, number])[];
}

export function useProposeScore(matchId: string) {
  const queryClient = useQueryClient();

  return useMutation<ResultAnswer, AppError, ScoreIntent>({
    mutationFn: (intent) => proposeScore({ matchId, sets: intent.sets }),
    retry: false,
    onSuccess: (answer) => applyAnswer(queryClient, matchId, answer),
  });
}

export function useAcceptResult(matchId: string) {
  const queryClient = useQueryClient();

  return useMutation<ResultAnswer, AppError, void>({
    mutationFn: () => acceptResult({ matchId }),
    retry: false,
    onSuccess: (answer) => applyAnswer(queryClient, matchId, answer),
  });
}
