/**
 * Finish the assessment: the reviewed answers become a Skill rating.
 *
 * **This is the irreversible one.** Answering never creates a rating and a stopped
 * questionnaire has created nothing, so until this request lands every answer is still the
 * player's to change ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)).
 * After it, the rating is proved and the answers behind it are settled.
 *
 * **One round trip, and the result comes back inline.** Completion appends the assessment's
 * completion and the rating's initialisation in one transaction and returns the finished
 * step, so there is nothing to refetch — the same rule the answer path follows, for the
 * same reason.
 *
 * **A second call is safe on the wire** — it records nothing and returns the first one's
 * result — which is what makes a double-tapped submit produce one rating. The client still
 * owns not firing two navigations; that is the screen's latch, not this.
 *
 * **The one conflict here is not a failure.** `assessment_not_stopped` says this device is
 * looking at a run the server has moved on from: it is still asking, or it was abandoned
 * elsewhere. Neither is anything the player did wrong and neither is retryable as sent, so
 * the recovery is the one the answer path already uses — re-read the step and render
 * whatever is genuinely outstanding, which is a question in the first case and a way out in
 * the second.
 */

import { isAppError } from '@/shared/errors';

import { completeAssessment as requestCompletion } from '../api/onboardingApi';
import type { AssessmentStep } from '../domain/Assessment';
import { isStaleStepConflict } from '../domain/answerRecovery';
import { toAssessmentStep } from '../mappers/onboardingMappers';

import { fetchAssessment } from './fetchAssessment';

export interface CompleteAssessmentOptions {
  readonly signal?: AbortSignal;
}

export async function completeAssessment(
  assessmentId: string,
  { signal }: CompleteAssessmentOptions = {},
): Promise<AssessmentStep> {
  try {
    const step = await requestCompletion(assessmentId, { signal });
    return toAssessmentStep(step);
  } catch (error) {
    if (isAppError(error) && isStaleStepConflict(error)) {
      return fetchAssessment(assessmentId, { signal });
    }
    throw error;
  }
}
