/**
 * **Where the groups screens live** — under Play, so the Play column stays lit on every one of
 * them (`shellTabs`' first-segment rule) and *back* returns to the Groups list.
 *
 * Named here, beside the screens they reach, and read by the screens and the route files alike: a
 * path spelled twice is the one that goes stale.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckArrival } from '../schemas/groupRouteParams';

/** **The Groups list** — Play's root, on its *Groups* segment; where leaving a group lands. */
export const GROUPS_LIST_ROUTE = '/play';

export const NEW_GROUP_ROUTE = '/play/new-group';
export const JOIN_GROUP_ROUTE = '/play/join';

/**
 * **Join a group, with a group's code** — what a group link opens (#520): the field filled with the
 * link and the group found under it. The code is validated where the route reads it
 * (`schemas/groupRouteParams`).
 */
export function joinGroupRouteFor(code: string) {
  return { pathname: JOIN_GROUP_ROUTE, params: { code } } as const;
}

/** A group's page. The id is validated where the route reads it (`schemas/groupRouteParams`). */
export function groupRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]', params: { groupId } } as const;
}

/**
 * **A group's deck, opened at a card** — where a notice about a card waiting for the player opens
 * (#559; the screens A9: *the deck opens with the card on top*): the page on Games, in the card's
 * sport and kind, the card first. Validated where the route reads it (`schemas/groupRouteParams`).
 */
export function groupDeckRoute(groupId: string, arrival: DeckArrival) {
  return {
    pathname: '/play/group/[groupId]',
    params: { groupId, sport: arrival.sport, kind: arrival.kind, card: arrival.card },
  } as const;
}

/**
 * **The Friends screen**, pushed over a group's page from an empty seat or *+ Friends* — for the
 * sport the court was drawn for, so the screen counts that court's seats. Validated where the
 * route reads it, as the page's own id is.
 */
export function groupFriendsRoute(groupId: string, sport: Sport) {
  return { pathname: '/play/group/[groupId]/friends', params: { groupId, sport } } as const;
}

/**
 * **Members** (play 61), pushed over a group's page from Info's members row. No sport in the
 * route: the page shares the fast filter's one state, so it opens on the sport the group page is
 * on and a pick there is the page's too.
 */
export function groupMembersRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]/members', params: { groupId } } as const;
}

/** **Edit group**, pushed over a group's page from Info's Edit group row — the Owner's. */
export function groupEditRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]/edit', params: { groupId } } as const;
}
