/**
 * The one route in this feature that carries a param, validated before anything reads it.
 *
 * A route param is attacker-controlled and expo-router hands it over as
 * `string | string[] | undefined` whatever the route declared, so it is checked first — the same
 * rule `features/play/schemas/routeParams.ts` states, and worth as much here: this string is
 * used to find a game in a list and then to build a path that appends a score to somebody's
 * stream.
 *
 * A link that does not survive this has no game behind it, which is the same answer as a link to
 * a game that is not yours: the screen says so and offers nothing. The two are deliberately not
 * told apart, because the server refuses to tell them apart for a reason — separating *it does
 * not exist* from *you did not play in it* would answer *is this id real* about four strangers'
 * evening.
 */

import { z } from 'zod';

export const gameRouteParams = z.object({
  /** The game this screen is about. Looked up in `GET /games`, which serves only yours. */
  gameId: z.string().uuid(),
});

export type GameRouteParams = z.infer<typeof gameRouteParams>;

/** `undefined` when the link cannot be trusted. The screen decides what that looks like. */
export function parseGameRouteParams(
  params: Record<string, string | string[] | undefined>,
): GameRouteParams | undefined {
  const result = gameRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}

/**
 * **Where a game screen is**, spelled once for the two surfaces that push it.
 *
 * It lived on `GamesSection` while that section was the only door. The rail that replaced it is
 * `features/plans`' ([#367](https://github.com/Raketa02/Raketa/issues/367)), so the path crosses a
 * feature boundary and a second spelling of it at the call site is how one of them goes stale — it
 * sits beside the schema that validates what comes back out of it.
 */
export const GAME_ROUTE = '/games/[gameId]';
