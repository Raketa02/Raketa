/**
 * **Where the groups screens live** — under Play, so the Play column stays lit on every one of
 * them (`shellTabs`' first-segment rule) and *back* returns to the Groups list.
 *
 * Named here, beside the screens they reach, and read by the screens and the route files alike: a
 * path spelled twice is the one that goes stale.
 */

import type { Sport } from '@/shared/vocabulary/sport';

export const NEW_GROUP_ROUTE = '/play/new-group';
export const JOIN_GROUP_ROUTE = '/play/join';

/** A group's page. The id is validated where the route reads it (`schemas/groupRouteParams`). */
export function groupRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]', params: { groupId } } as const;
}

/**
 * **The Friends screen**, pushed over a group's page from an empty seat or *+ Friends* — for the
 * sport the court was drawn for, so the screen counts that court's seats. Validated where the
 * route reads it, as the page's own id is.
 */
export function groupFriendsRoute(groupId: string, sport: Sport) {
  return { pathname: '/play/group/[groupId]/friends', params: { groupId, sport } } as const;
}
