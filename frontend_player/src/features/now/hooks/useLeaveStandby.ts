/**
 * Leaving standby: the second write Now makes for itself, and the one that
 * removes a card.
 *
 * **One tap, and no confirmation** (`ADR-0087`). Nothing is lost — no money moves,
 * no Player Score is touched, and there is no *place* to forfeit, because a
 * standby position is deliberately not a fact the platform shows. A dialog here
 * would imply a cost the model says does not exist, which is worse than a mis-tap:
 * a mis-tap is one tap to undo, and a false warning teaches a player that standby
 * is something she is giving up.
 *
 * **Not retried, on the app's own initiative or otherwise.** The route is
 * idempotent by its own nature, so a retry would be *safe* — and it would still be
 * a command she did not give. The app's default is `retry: false` and this hook
 * keeps it, in the same breath as the seat write beside it: what a repeat would
 * answer is *did my tap land*, and the screen answers that by whether the card is
 * still there.
 *
 * **No `onMutate` and no optimistic removal.** Taking the card away before the
 * server has answered is the phone deciding a card's place (`ADR-0053`,
 * `ADR-0070`), and it fails in the direction that matters: a write that did not
 * land would leave her looking at a screen that says she is off a queue she is
 * still on.
 *
 * **One cache write and no invalidation** (`ADR-0074`): the answer was composed by
 * the server at the instant of the write, so asking Now for the whole screen again
 * would pay the full funnel for something already in hand.
 *
 * **Every sport's screen, not the chip she is holding** — which is `writeNowUpdate`
 * unchanged, and is why this hook takes no sport where `useTakeSeat` does. That
 * write answers two whole *regions*, composed under one chip; this one answers a
 * card, and a card she has left the queue of is gone from `all` and from its own
 * sport's screen alike.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { NowUpdate } from '../domain/ComposedScreen';
import { leaveStandby } from '../use-cases/leaveStandby';

import { writeNowUpdate } from './writeNowUpdate';

export interface LeaveStandbyIntent {
  /** The match whose queue she is leaving. There is nothing else to send. */
  readonly matchId: string;
}

export function useLeaveStandby() {
  const queryClient = useQueryClient();

  return useMutation<NowUpdate, AppError, LeaveStandbyIntent>({
    mutationFn: (intent) => leaveStandby({ matchId: intent.matchId }),
    retry: false,
    onSuccess: (update) => writeNowUpdate(queryClient, update),
  });
}
