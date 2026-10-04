/**
 * **The administrator area's route params, checked** — a route param is untrusted input, and the
 * club and the group are both ids the server answers for. A param that does not survive has no
 * club or group behind it, and the route sends the person to `/`, where the entry gate decides.
 */

import { z } from 'zod';

const ClubRouteParams = z.object({ clubId: z.string().uuid() });

export function parseClubRouteParams(params: unknown): { readonly clubId: string } | undefined {
  const parsed = ClubRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

const OfficialGroupRouteParams = ClubRouteParams.extend({ groupId: z.string().uuid() });

export function parseOfficialGroupRouteParams(
  params: unknown,
): { readonly clubId: string; readonly groupId: string } | undefined {
  const parsed = OfficialGroupRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
