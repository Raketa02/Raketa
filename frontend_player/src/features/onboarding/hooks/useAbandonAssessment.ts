/**
 * Abandoning the run in front of the player.
 *
 * **Not retried**, like every mutation in this feature — but for the opposite reason to
 * the others. Answering must not repeat because it is not idempotent; abandoning would
 * survive a repeat perfectly well, and is still not retried because the one destructive
 * action in onboarding is the player's to re-press, not the client's to re-send behind
 * their back.
 *
 * **The assessment's cached step is deliberately left alone.** Writing an abandoned step
 * into it, or removing the key, would make the question screen this was called from
 * re-read a run that no longer exists — and race the navigation that is already under
 * way. Nothing resumes from that cache either: resume goes through the gate, which asks
 * the server. The entry is stale and unreachable, and it ages out.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { abandonAssessment } from '../use-cases/abandonAssessment';

import { onboardingKeys } from './onboardingKeys';

export function useAbandonAssessment(assessmentId: string) {
  const queryClient = useQueryClient();

  return useMutation<void, AppError, void>({
    mutationFn: () => abandonAssessment(assessmentId),
    retry: false,
    onSuccess: () => {
      // **Removed, not invalidated** — the one place this feature departs from its two
      // sibling mutations, and deliberately.
      //
      // An invalidated query still answers from its old data for the render before the
      // refetch lands. The old answer here is "this run is unfinished", which is exactly
      // what the gate resumes on — so a warm cache would route the player straight back
      // into the run they just abandoned. Onboarding runs well inside the 5-minute
      // `gcTime`, so warm is the normal case on a real device. Removing the entry leaves
      // the gate nothing to answer from, and its "wait for both queries" rule turns that
      // into a pause rather than a wrong turn.
      //
      // Nothing is written in its place, for the same reason the other hooks invalidate:
      // a client that answered "nothing in progress" from memory would strand a player
      // who started one on another device.
      queryClient.removeQueries({ queryKey: onboardingKeys.runInProgress() });
    },
  });
}
