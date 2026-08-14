/**
 * The wire adapter for onboarding. One of the two layers allowed to read generated types,
 * and the only place these paths are written down.
 *
 * Nothing here decides anything: which sport to start, where a player belongs on launch
 * and what a failure means all belong above.
 */

import type { components, operations } from '@/generated/schema';
import { mapDecodeFailure } from '@/shared/errors';
import { httpRequest } from '@/shared/lib/http';

type RatingsResponse = components['schemas']['RatingsResponse'];
type SportsResponse = components['schemas']['SportsResponse'];
type AssessmentStepResponse = components['schemas']['AssessmentStepResponse'];
type CreateAssessmentRequest = components['schemas']['CreateAssessmentRequest'];
type SubmitAnswerRequest = components['schemas']['SubmitAnswerRequest'];
type InProgressAssessmentsResponse = components['schemas']['InProgressAssessmentsResponse'];

/**
 * The union the route's 200 actually is — taken from the operation rather than assembled
 * here, so an arm the backend adds or drops arrives through `pnpm gen:api` instead of
 * being restated at a second desk.
 */
type FindInProgressResponse =
  operations['find_in_progress_api_v1_assessments_in_progress_get']['responses'][200]['content']['application/json'];

export interface OnboardingApiOptions {
  readonly signal?: AbortSignal;
}

/** Every sport this player is rated at. An unrated player is an empty collection. */
export function listRatings({ signal }: OnboardingApiOptions = {}): Promise<RatingsResponse> {
  return httpRequest<RatingsResponse>({
    method: 'GET',
    path: '/api/v1/ratings',
    authenticated: true,
    signal,
  });
}

/**
 * The sports the platform serves.
 *
 * Read from the server rather than hard-coded: the registry is a closed set in the
 * backend's shared kernel, and this route exists precisely so that neither client
 * restates it.
 */
export function listSports({ signal }: OnboardingApiOptions = {}): Promise<SportsResponse> {
  return httpRequest<SportsResponse>({
    method: 'GET',
    path: '/api/v1/sports',
    authenticated: true,
    signal,
  });
}

/**
 * Every unfinished run this player holds — in **one** request, at most one entry per sport,
 * in sport-registry order, and an empty collection when there are none.
 *
 * Empty arrives as a 200 with an empty list, never a 204 and never a 404: no run in
 * progress is the ordinary state of an account and by far the commonest answer.
 *
 * `sport` is deliberately omitted, and that is what selects the shape. The route answers
 * two ways off one path — that sport's outstanding step when `sport` is supplied, this
 * collection when it is not — so the contract's 200 is a union, and the arm this call asked
 * for is picked out here at the wire boundary rather than carried inward for a mapper to
 * sort out. A body with no `assessments` is the route answering a question this call did
 * not ask: a decode failure, and emphatically not "nothing in progress", because an empty
 * list would send a player with an unfinished run straight past the gate.
 */
export async function listRunsInProgress({
  signal,
}: OnboardingApiOptions = {}): Promise<InProgressAssessmentsResponse> {
  const body = await httpRequest<FindInProgressResponse>({
    method: 'GET',
    path: '/api/v1/assessments/in-progress',
    authenticated: true,
    signal,
  });

  if (!isCollection(body)) {
    throw mapDecodeFailure(
      new Error('GET /assessments/in-progress answered with a step, not the collection.'),
    );
  }
  return body;
}

function isCollection(body: FindInProgressResponse): body is InProgressAssessmentsResponse {
  return Array.isArray((body as InProgressAssessmentsResponse).assessments);
}

/** Start an assessment and receive its opening question in the same round trip. */
export function createAssessment(
  body: CreateAssessmentRequest,
  { signal }: OnboardingApiOptions = {},
): Promise<AssessmentStepResponse> {
  return httpRequest<AssessmentStepResponse>({
    method: 'POST',
    path: '/api/v1/assessments',
    body,
    authenticated: true,
    signal,
  });
}

/**
 * Answer the outstanding question, and receive the next step in the same response.
 *
 * **One round trip, and the response is the next question.** The engine is conversational
 * but stateless — it takes the whole transcript on every call — so choosing what to ask
 * next *is* the rating calculation. There is nothing here for a client to predict.
 */
export function submitAnswer(
  assessmentId: string,
  body: SubmitAnswerRequest,
  { signal }: OnboardingApiOptions = {},
): Promise<AssessmentStepResponse> {
  return httpRequest<AssessmentStepResponse>({
    method: 'POST',
    path: `/api/v1/assessments/${encodeURIComponent(assessmentId)}/answers`,
    body,
    authenticated: true,
    signal,
  });
}

/**
 * End a run without a rating, freeing its sport to be started again.
 *
 * A POST to a sub-resource rather than a `DELETE`, because **nothing is deleted**: the
 * run reaches a terminal state and the record of it stays on its stream. 204 — there is
 * no new step to report, and asking for one would describe a run that no longer exists.
 */
export function abandonAssessment(
  assessmentId: string,
  { signal }: OnboardingApiOptions = {},
): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `/api/v1/assessments/${encodeURIComponent(assessmentId)}/abandonment`,
    authenticated: true,
    signal,
  });
}

/** An assessment's current state — its outstanding question, or nothing left to ask. */
export function getAssessment(
  assessmentId: string,
  { signal }: OnboardingApiOptions = {},
): Promise<AssessmentStepResponse> {
  return httpRequest<AssessmentStepResponse>({
    method: 'GET',
    path: `/api/v1/assessments/${encodeURIComponent(assessmentId)}`,
    authenticated: true,
    signal,
  });
}
