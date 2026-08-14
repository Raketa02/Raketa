/**
 * Stop rating this sport: the run ends, its answers are discarded, and the sport is free
 * to be rated again from the beginning.
 *
 * **A state transition, not a deletion.** The run reaches a terminal state and the record
 * of it remains — which is what makes the operation idempotent on the server, and that
 * idempotence is the whole reason a failed abandon can simply be pressed again. A second
 * abandonment of an already-abandoned run is a no-op rather than a conflict, so the retry
 * cannot fail on the ground that the first attempt secretly succeeded.
 *
 * That is also why this is not retried automatically. The endpoint would tolerate it, but
 * a silent retry of the one destructive action in onboarding is not a decision the client
 * gets to make on the player's behalf; the retry is a control they press.
 */

import { abandonAssessment as sendAbandonment } from "../api/onboardingApi";

export interface AbandonAssessmentOptions {
  readonly signal?: AbortSignal;
}

export function abandonAssessment(
  assessmentId: string,
  { signal }: AbandonAssessmentOptions = {},
): Promise<void> {
  return sendAbandonment(assessmentId, { signal });
}
