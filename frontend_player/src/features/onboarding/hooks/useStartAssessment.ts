/**
 * Start rating one sport.
 *
 * **Not retried.** Starting an assessment creates a run, and a silent retry of a request
 * that actually succeeded but whose response was lost would open a second one — leaving
 * the player with an assessment they will be routed back into on the next launch. The
 * player retries by tapping the button.
 *
 * The cache effect is the pattern this whole flow is built on: **write the response, do
 * not invalidate and refetch it.** The server just handed back the opening question, and
 * asking for it again would be a second round trip for an answer already in hand.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentStep } from '../domain/Assessment';
import type { Sport } from '@/shared/vocabulary/sport';
import { startAssessment } from '../use-cases/startAssessment';

import { onboardingKeys } from './onboardingKeys';

export function useStartAssessment() {
  const queryClient = useQueryClient();

  return useMutation<AssessmentStep, AppError, Sport>({
    mutationFn: (sport) => startAssessment(sport),
    retry: false,
    onSuccess: (step) => {
      queryClient.setQueryData(onboardingKeys.assessment(step.assessmentId), step);
      // A run now exists, so the gate's answer has changed. Marking it stale rather than
      // writing it keeps one source of truth for "is anything unfinished" — the server.
      void queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
    },
  });
}
