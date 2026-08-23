/**
 * Taking the quote.
 *
 * **Not retried, and the idempotency key is not a licence to retry.** The app's
 * default for every mutation is `retry: false`, and this is the case that default
 * was written for: a retry the client makes on its own is a request the player did
 * not authorise, on an act that ends her participation in a match. What the key
 * buys is that a retry **she** makes — the second press after a press that seemed
 * not to land — is answered with what the first one did, rather than applied twice
 * or reported as a refusal.
 *
 * **No `onMutate`.** There is no optimistic update to write and never will be: what
 * leaving does to the card is composed by the server from the record after the
 * write, and a phone that guessed at it would be holding the rules `ADR-0053`
 * leaves it none of.
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
 * player watching the screen she just came back to rebuild itself.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { writeNowUpdate } from '@/features/now/types';
import type { AppError } from '@/shared/errors';

import type { DepartureAnswer } from '../domain/Departure';
import { leaveMatch } from '../use-cases/leaveMatch';

import { departureKeys } from './departureKeys';

export interface LeaveIntent {
  /** The label the screen was showing, carried back unread (`ADR-0033`). */
  readonly quote: string;
  /** One key per visit to the screen, minted by the screen. See `domain/requestKey.ts`. */
  readonly idempotencyKey: string;
}

export function useLeaveMatch(matchId: string) {
  const queryClient = useQueryClient();

  return useMutation<DepartureAnswer, AppError, LeaveIntent>({
    mutationFn: (intent) => leaveMatch({ matchId, ...intent }),
    retry: false,
    onSuccess: (answer) => {
      queryClient.setQueryData(departureKeys.screen(matchId), answer.screen);
      writeNowUpdate(queryClient, answer.update);
    },
  });
}
