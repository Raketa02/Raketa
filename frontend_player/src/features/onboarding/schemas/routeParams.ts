/**
 * Route params, validated.
 *
 * Every param arriving from a deep link, a push notification, a universal link or a
 * hand-typed URL is attacker-controlled — and expo-router hands them over as
 * `string | string[] | undefined` whatever the route declared. So a route validates before
 * it fetches, and a malformed link lands on welcome rather than in a request built from
 * someone else's input.
 *
 * The sport is a closed set and the assessment id is a UUID, which makes both of them
 * cheap to check and pointless to guess at.
 *
 * **One schema, both assessment routes.** The question route and the result route carry
 * the same two params for the same reason — the wire does not say which sport a step
 * belongs to, because `/assessments/{id}` is asked about a run rather than about a sport —
 * so the parser is named for the params it checks and not for the screen that reads them.
 */

import { z } from 'zod';

import { SPORTS } from '../domain/Sport';

export const assessmentRouteParams = z.object({
  assessmentId: z.string().uuid(),
  sport: z.enum(SPORTS),
});

export type AssessmentRouteParams = z.infer<typeof assessmentRouteParams>;

/** `undefined` when the link cannot be trusted. The caller decides where that goes. */
export function parseAssessmentRouteParams(
  params: Record<string, string | string[] | undefined>,
): AssessmentRouteParams | undefined {
  const result = assessmentRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
