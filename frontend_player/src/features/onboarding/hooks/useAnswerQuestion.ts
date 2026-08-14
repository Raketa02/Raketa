/**
 * Submitting one answer.
 *
 * **Not retried**, per the client's default for every mutation: an answer is append-only
 * and irreversible, and a silent retry of a request that actually succeeded but whose
 * response was lost would record a second answer to a question the run has already moved
 * past. The player retries by pressing confirm again — which is also why a failure must
 * leave their selection where it was.
 *
 * **No `onMutate`.** There is no optimistic update to write here and never will be: the
 * next question is chosen from the whole transcript by the engine, so the client cannot
 * predict it without doing the rating calculation itself.
 *
 * The cache effect is the pattern this flow is built on: **write the response, never
 * invalidate and refetch it.** The server just handed back the next step; asking for it
 * again would be a second round trip for an answer already in hand.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentStep } from '../domain/Assessment';
import { answerQuestion } from '../use-cases/answerQuestion';

import { onboardingKeys } from './onboardingKeys';

export interface AnswerSelection {
  readonly questionId: string;
  readonly optionId: string;
}

export function useAnswerQuestion(assessmentId: string) {
  const queryClient = useQueryClient();

  return useMutation<AssessmentStep, AppError, AnswerSelection>({
    mutationFn: (selection) => answerQuestion({ assessmentId, ...selection }),
    retry: false,
    onSuccess: (step) => {
      queryClient.setQueryData(onboardingKeys.assessment(assessmentId), step);

      // Only a finished run changes what the entry gate would answer, and only a finished
      // run produces a rating. Marking them stale rather than writing them keeps one
      // source of truth for both — the server — and costs nothing while the gate's
      // queries are unmounted, which they are for the whole of onboarding.
      if (step.question === undefined) {
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.ratings() });
      }
    },
  });
}
