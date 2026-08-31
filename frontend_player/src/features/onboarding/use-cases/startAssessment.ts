/**
 * Start rating one sport, and receive its opening question in the same round trip.
 *
 * The opening "have you played this sport" question is an ordinary question from the
 * engine's bank, not a screen of its own — which is also why a first-timer can finish the
 * whole assessment in a single answer.
 */

import { createAssessment } from '../api/onboardingApi';
import type { AssessmentStep } from '../domain/Assessment';
import type { Sport } from '@/shared/vocabulary/sport';
import { toAssessmentStep, toWireSport } from '../mappers/onboardingMappers';

export interface StartAssessmentOptions {
  readonly signal?: AbortSignal;
}

export function startAssessment(
  sport: Sport,
  { signal }: StartAssessmentOptions = {},
): Promise<AssessmentStep> {
  return createAssessment({ sport: toWireSport(sport) }, { signal }).then(toAssessmentStep);
}
