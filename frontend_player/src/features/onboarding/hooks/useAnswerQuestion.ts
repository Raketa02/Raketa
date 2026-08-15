/**
 * Submitting one answer.
 *
 * **Not retried**, per the client's default for every mutation. The submission is the one
 * request in this flow that changes the run, and a retry it makes on its own is a request
 * the player did not authorise — one that now carries more than a duplicate answer, since
 * the same route also revises, and a revision discards every answer after the question it
 * names (ADR-0020). Re-sending *this* answer is safe on the wire, because the same option
 * for the same question records nothing; that is the server's guarantee to lean on when
 * the player presses confirm again, not a licence to press it for them. Which is also why
 * a failure must leave their selection where it was.
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

      // Only a run that has *ended* changes what the entry gate would answer, and only a
      // completed one produces a rating. Marking them stale rather than writing them keeps
      // one source of truth for both — the server — and costs nothing while the gate's
      // queries are unmounted, which they are for the whole of onboarding.
      //
      // **Not "no question left"**, which this read once was: a stopped questionnaire has
      // no question and has still rated nothing, so reading it that way would mark a
      // player's ratings stale at a moment none of them changed. Answering cannot finish a
      // run at all now (ADR-0020) — what reaches here ended is the stale-step recovery's
      // re-read, which is exactly the case that must not be missed.
      if (step.status !== 'in_progress') {
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.runInProgress() });
        void queryClient.invalidateQueries({ queryKey: onboardingKeys.ratings() });
      }
    },
  });
}
