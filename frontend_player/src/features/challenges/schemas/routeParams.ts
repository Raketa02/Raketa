/**
 * The one route in this feature that carries a param, validated before anything reads it.
 *
 * A route param is attacker-controlled and expo-router hands it over as
 * `string | string[] | undefined` whatever the route declared, so it is checked first — the same
 * rule `features/games/schemas/routeParams.ts` and `features/play/schemas/routeParams.ts` state,
 * and worth as much here: this string becomes the path of a read that serves another person's
 * photograph and level, and then the path of a `POST` that accepts a game on somebody's behalf.
 *
 * A link that does not survive this has no challenge behind it, which is the same answer as a
 * link to a challenge that is not yours. The two are deliberately not told apart, because the
 * server refuses to tell them apart for a reason: separating *it does not exist* from *you are
 * not on its court* would answer *is this id real* about a stranger's evening.
 */

import { z } from 'zod';

export const challengeRouteParams = z.object({
  /** The challenge this screen is about. Read from `GET /challenges/{id}`, which serves only yours. */
  challengeId: z.string().uuid(),
});

export type ChallengeRouteParams = z.infer<typeof challengeRouteParams>;

/** `undefined` when the link cannot be trusted. The screen decides what that looks like. */
export function parseChallengeRouteParams(
  params: Record<string, string | string[] | undefined>,
): ChallengeRouteParams | undefined {
  const result = challengeRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
