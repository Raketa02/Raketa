/**
 * The one param this route carries, validated.
 *
 * Every param arriving from a deep link, a push notification, a universal link or
 * a hand-typed URL is attacker-controlled, and expo-router hands them over as
 * `string | string[] | undefined` whatever the route declared. So the route
 * validates before it fetches, and a malformed link goes home rather than issuing
 * a request built from somebody else's string.
 *
 * A match id is a UUID, which makes it cheap to check and pointless to guess at.
 * Checking it is not a security boundary — the server answers a stranger with a
 * 404 whatever the phone believes — it is what keeps a hand-typed URL from
 * becoming a request path.
 */

import { z } from 'zod';

export const departureRouteParams = z.object({
  matchId: z.string().uuid(),
});

export type DepartureRouteParams = z.infer<typeof departureRouteParams>;

/** `undefined` when the link cannot be trusted. The caller decides where that goes. */
export function parseDepartureRouteParams(
  params: Record<string, string | string[] | undefined>,
): DepartureRouteParams | undefined {
  const result = departureRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
