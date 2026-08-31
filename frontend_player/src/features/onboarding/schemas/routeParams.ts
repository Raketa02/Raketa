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
 * **One schema, all three assessment routes.** The question, review and result routes carry
 * the same two params for the same reason — the wire does not say which sport a step
 * belongs to, because `/assessments/{id}` is asked about a run rather than about a sport —
 * so the parser is named for the params it checks and not for the screen that reads them.
 */

import { z } from 'zod';

import { SPORTS } from '@/shared/vocabulary/sport';

export const assessmentRouteParams = z.object({
  assessmentId: z.string().uuid(),
  sport: z.enum(SPORTS),
  /**
   * Which question to stand on, 1-based — what a review entry opens, and the one param
   * only the questionnaire reads.
   *
   * **Navigation input, not state.** It says where the player starts standing; every move
   * after it is local to the screen and costs nothing. Absent means *wherever the run
   * stands*, which is the question being asked — and a number pointing outside the run is
   * clamped to it rather than rejected, because the run it names is served fresh and may
   * be shorter than the one the link was made from.
   */
  at: z.coerce.number().int().positive().optional(),
});

export type AssessmentRouteParams = z.infer<typeof assessmentRouteParams>;

/** `undefined` when the link cannot be trusted. The caller decides where that goes. */
export function parseAssessmentRouteParams(
  params: Record<string, string | string[] | undefined>,
): AssessmentRouteParams | undefined {
  const result = assessmentRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
