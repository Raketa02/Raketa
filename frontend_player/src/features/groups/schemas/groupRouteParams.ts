/**
 * **A group page's route params, checked before anything trusts them** — a route param is input
 * from outside the app (a link, a notification later), and an id that is not a UUID has no group
 * behind it.
 */

import { z } from 'zod';

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

const GroupRouteParams = z.object({ groupId: z.string().uuid() });

/** The group id, or `undefined` for a param this app cannot read. */
export function parseGroupRouteParams(params: unknown): { readonly groupId: string } | undefined {
  const parsed = GroupRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/**
 * The Friends screen's: the group, and **the sport the court was drawn for** — the screen's
 * eyebrow counts that court's seats (play 54), so a sport this build cannot name is a screen with
 * nothing to count, and is refused like a group id that is not one.
 */
const FriendsRouteParams = GroupRouteParams.extend({ sport: z.enum(SPORTS) });

export function parseFriendsRouteParams(
  params: unknown,
): { readonly groupId: string; readonly sport: Sport } | undefined {
  const parsed = FriendsRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/**
 * **A group's code** — the eight letters and digits after `/join/` in its link. Read in lower case,
 * the case every code is minted in, so a link a keyboard capitalised names the same group; whether
 * the eight are any group's is the server's to say (ADR-0183 §4).
 */
export const GroupCodeSchema = z
  .string()
  .regex(/^[0-9A-Za-z]{8}$/)
  .transform((code) => code.toLowerCase());

const JoinRouteParams = z.object({ code: GroupCodeSchema });

/**
 * **Join a group opened by a group link** (#520): the code the link carried, or `undefined` —
 * Join a group opened from Play, or a code that cannot be one, either way an empty field.
 */
export function parseJoinRouteParams(params: unknown): { readonly code: string } | undefined {
  const parsed = JoinRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
