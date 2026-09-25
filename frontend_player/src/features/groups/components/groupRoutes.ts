/**
 * **Where the groups screens live** — under Play, so the Play column stays lit on every one of
 * them (`shellTabs`' first-segment rule) and *back* returns to the Groups list.
 *
 * Named here, beside the screens they reach, and read by the screens and the route files alike: a
 * path spelled twice is the one that goes stale.
 */

export const NEW_GROUP_ROUTE = '/play/new-group';
export const JOIN_GROUP_ROUTE = '/play/join';

/** A group's page. The id is validated where the route reads it (`schemas/groupRouteParams`). */
export function groupRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]', params: { groupId } } as const;
}
