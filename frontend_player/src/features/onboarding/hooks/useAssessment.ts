/**
 * The outstanding step of one assessment.
 *
 * Starting an assessment writes its opening question straight into this key, so the
 * questionnaire does not refetch what the server just handed back. A **resumed** run has
 * nothing in the cache — the queue was never persisted and neither was the transcript —
 * so it is read from the server, which is the only place it ever lived.
 *
 * **The options are a factory because two screens read the same run.** The question and
 * result screens read one; the done screen reads every run this pass produced, through
 * `useQueries`. A second literal would be a second key and a second `queryFn` for one
 * read — which is how a screen ends up refetching what another already has.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentStep } from '../domain/Assessment';
import { fetchAssessment } from '../use-cases/fetchAssessment';

import { onboardingKeys } from './onboardingKeys';

export function assessmentQuery(assessmentId: string) {
  return {
    queryKey: onboardingKeys.assessment(assessmentId),
    queryFn: ({ signal }: { signal: AbortSignal }) => fetchAssessment(assessmentId, { signal }),
  };
}

export function useAssessment(assessmentId: string) {
  return useQuery<AssessmentStep, AppError>(assessmentQuery(assessmentId));
}
