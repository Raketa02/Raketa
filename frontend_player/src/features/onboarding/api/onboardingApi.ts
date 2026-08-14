/**
 * The wire adapter for onboarding. One of the two layers allowed to read generated types,
 * and the only place these paths are written down.
 *
 * Nothing here decides anything: which sport to start, where a player belongs on launch
 * and what a failure means all belong above.
 */

import type { components } from "@/generated/schema";
import { httpRequest } from "@/shared/lib/http";

type RatingsResponse = components["schemas"]["RatingsResponse"];
type SportsResponse = components["schemas"]["SportsResponse"];
type AssessmentStepResponse = components["schemas"]["AssessmentStepResponse"];
type CreateAssessmentRequest = components["schemas"]["CreateAssessmentRequest"];
type SubmitAnswerRequest = components["schemas"]["SubmitAnswerRequest"];
type WireSport = components["schemas"]["Sport"];

export interface OnboardingApiOptions {
  readonly signal?: AbortSignal;
}

/** Every sport this player is rated at. An unrated player is an empty collection. */
export function listRatings({
  signal,
}: OnboardingApiOptions = {}): Promise<RatingsResponse> {
  return httpRequest<RatingsResponse>({
    method: "GET",
    path: "/api/v1/ratings",
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
export function listSports({
  signal,
}: OnboardingApiOptions = {}): Promise<SportsResponse> {
  return httpRequest<SportsResponse>({
    method: "GET",
    path: "/api/v1/sports",
    authenticated: true,
    signal,
  });
}

/**
 * The sport's unfinished run, or nothing.
 *
 * 204 is the "nothing" answer and is not an error: no run in progress is the normal state
 * of a sport. `httpRequest` decodes an empty body as `undefined`.
 */
export function findInProgress(
  sport: WireSport,
  { signal }: OnboardingApiOptions = {},
): Promise<AssessmentStepResponse | undefined> {
  return httpRequest<AssessmentStepResponse | undefined>({
    method: "GET",
    path: `/api/v1/assessments/in-progress?sport=${encodeURIComponent(sport)}`,
    authenticated: true,
    signal,
  });
}

/** Start an assessment and receive its opening question in the same round trip. */
export function createAssessment(
  body: CreateAssessmentRequest,
  { signal }: OnboardingApiOptions = {},
): Promise<AssessmentStepResponse> {
  return httpRequest<AssessmentStepResponse>({
    method: "POST",
    path: "/api/v1/assessments",
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
    method: "POST",
    path: `/api/v1/assessments/${encodeURIComponent(assessmentId)}/answers`,
    body,
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
    method: "GET",
    path: `/api/v1/assessments/${encodeURIComponent(assessmentId)}`,
    authenticated: true,
    signal,
  });
}
