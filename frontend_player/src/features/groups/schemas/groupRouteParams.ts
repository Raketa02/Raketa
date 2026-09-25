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
