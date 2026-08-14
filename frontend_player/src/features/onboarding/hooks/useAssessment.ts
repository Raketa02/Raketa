/**
 * The outstanding step of one assessment.
 *
 * Starting an assessment writes its opening question straight into this key, so the
 * questionnaire does not refetch what the server just handed back. A **resumed** run has
 * nothing in the cache — the queue was never persisted and neither was the transcript —
 * so it is read from the server, which is the only place it ever lived.
 */

import { useQuery } from "@tanstack/react-query";

import type { AppError } from "@/shared/errors";

import type { AssessmentStep } from "../domain/Assessment";
import { fetchAssessment } from "../use-cases/fetchAssessment";

import { onboardingKeys } from "./onboardingKeys";

export function useAssessment(assessmentId: string) {
  return useQuery<AssessmentStep, AppError>({
    queryKey: onboardingKeys.assessment(assessmentId),
    queryFn: ({ signal }) => fetchAssessment(assessmentId, { signal }),
  });
}
