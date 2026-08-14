/**
 * An assessment's current state, by id — what a resumed run is read back through.
 *
 * Resume survives a force-quit, a reinstall and a new handset because nothing about the
 * transcript ever lived on the device: the server is asked what is outstanding, and the
 * deterministic engine reproduces the question rather than storing it twice.
 */

import { getAssessment } from '../api/onboardingApi';
import type { AssessmentStep } from '../domain/Assessment';
import { toAssessmentStep } from '../mappers/onboardingMappers';

export interface FetchAssessmentOptions {
  readonly signal?: AbortSignal;
}

export function fetchAssessment(
  assessmentId: string,
  { signal }: FetchAssessmentOptions = {},
): Promise<AssessmentStep> {
  return getAssessment(assessmentId, { signal }).then(toAssessmentStep);
}
