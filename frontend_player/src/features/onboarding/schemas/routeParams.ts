/**
 * Route params, validated.
 *
 * Every param arriving from a deep link, a push notification, a universal link or a
 * hand-typed URL is attacker-controlled — and expo-router hands them over as
 * `string | string[] | undefined` whatever the route declared. So the question route
 * validates before it fetches, and a malformed link lands on welcome rather than in a
 * request built from someone else's input.
 *
 * The sport is a closed set and the assessment id is a UUID, which makes both of them
 * cheap to check and pointless to guess at.
 */

import { z } from "zod";

import { SPORTS } from "../domain/Sport";

export const questionRouteParams = z.object({
  assessmentId: z.string().uuid(),
  sport: z.enum(SPORTS),
});

export type QuestionRouteParams = z.infer<typeof questionRouteParams>;

/** `undefined` when the link cannot be trusted. The caller decides where that goes. */
export function parseQuestionRouteParams(
  params: Record<string, string | string[] | undefined>,
): QuestionRouteParams | undefined {
  const result = questionRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
