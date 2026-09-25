/**
 * **A group page's route param, checked before anything trusts it** — a route param is input
 * from outside the app (a link, a notification later), and an id that is not a UUID has no group
 * behind it.
 */

import { z } from 'zod';

const GroupRouteParams = z.object({ groupId: z.string().uuid() });

/** The group id, or `undefined` for a param this app cannot read. */
export function parseGroupRouteParams(params: unknown): { readonly groupId: string } | undefined {
  const parsed = GroupRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
