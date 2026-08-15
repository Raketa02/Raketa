/**
 * Creating the Skill rating from the reviewed answers.
 *
 * **Not retried**, like every mutation in this feature, and here for the plainest reason
 * of the three: this is the request that makes something irreversible. Re-sending it would
 * cost nothing on the wire — a second completion records nothing and returns the first
 * one's result — but a client that repeats the one irreversible request on its own is a
 * client the player has to trust about a moment they were not consulted on.
 *
 * The cache effect is the flow's own pattern: **write the response, never invalidate and
 * refetch it.** The finished step comes back inline with the result on it, so the result
 * screen renders from what this call already returned. What *is* invalidated is the pair
 * of reads a new rating changes — the gate's unfinished runs and the player's ratings —
 * because those are the server's to answer and this client must not answer them from
 * memory.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentStep } from '../domain/Assessment';
import { completeAssessment } from '../use-cases/completeAssessment';

import { onboardingKeys } from './onboardingKeys';

export function useCompleteAssessment(assessmentId: string) {
  const queryClient = useQueryClient();

  return useMutation<AssessmentStep, AppError, void>({
    mutationFn: () => completeAssessment(assessmentId),
    retry: false,
    onSuccess: (step) => {
      queryClient.setQueryData(onboardingKeys.assessment(assessmentId), step);

      // Marked stale rather than written: one source of truth for both, and it costs
      // nothing while the gate's queries are unmounted, which they are for all of
      // onboarding. Guarded on the run actually having ended, because the stale-step
      // recovery can bring back a run that is still asking.
      if (step.status !== 'in_progress') {
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.ratings() });
      }
    },
  });
}
