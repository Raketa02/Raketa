/**
 * **Where the administrator area lives** — its own group of screens, outside the player's tab shell
 * (PRD #500: *its own group of screens outside the player's tab shell*), one area per club it runs:
 * `/administrator/<club>` is the Groups tab, `…/you` the You tab, New official group and a group's
 * page are pushed over Groups, a group's Members over its page, and a group's settings over You.
 *
 * **The club is in the path**, because every screen here is one Administrator's at one club and a
 * person running two clubs' groups is two Administrators (ADR-0184 §1): the area is whole from its
 * URL, and the entry gate — and later the profile switcher — opens it by naming the club.
 *
 * Named here, beside the screens they reach, and read by the screens, the shell and the route files
 * alike: a path spelled twice is the one that goes stale.
 */

import type { AdministratorTabBarKey } from '@/shared/ui';

/** **The Groups tab** — the area's root, where the entry gate lands an administrator-only account. */
export function administratorHome(clubId: string): string {
  return `/administrator/${clubId}`;
}

/** **The You tab.** */
export function administratorYou(clubId: string): string {
  return `${administratorHome(clubId)}/you`;
}

/** Each tab's root, by tab. */
export function areaTabRoot(clubId: string, tab: AdministratorTabBarKey): string {
  return tab === 'groups' ? administratorHome(clubId) : administratorYou(clubId);
}

/** **New official group**, pushed over the Groups tab. */
export function newOfficialGroupRoute(clubId: string) {
  return { pathname: '/administrator/[clubId]/new-group', params: { clubId } } as const;
}

/** **An official group's page**, pushed over the Groups tab — or replacing New official group. */
export function officialGroupRoute(clubId: string, groupId: string) {
  return {
    pathname: '/administrator/[clubId]/group/[groupId]',
    params: { clubId, groupId },
  } as const;
}

/** **An official group's Members**, pushed over its page from the players card (#529). */
export function officialGroupMembersRoute(clubId: string, groupId: string) {
  return {
    pathname: '/administrator/[clubId]/group/[groupId]/members',
    params: { clubId, groupId },
  } as const;
}

/**
 * **An official group's settings**, pushed over the You tab from the group's row — under the tab's
 * own segment, so the You column stays lit and *back* is the tab.
 */
export function groupSettingsRoute(clubId: string, groupId: string) {
  return {
    pathname: '/administrator/[clubId]/you/settings/[groupId]',
    params: { clubId, groupId },
  } as const;
}

/**
 * ***Start playing*'s first step, the Adult attestation**, pushed over the You tab — `auth`'s
 * screen at an address inside the area, so *back* is the tab (the entry gate's own address for it
 * is `auth`'s `START_PLAYING_STEP`). The steps after it are the gate's.
 */
export function startPlayingRoute(clubId: string) {
  return { pathname: '/administrator/[clubId]/you/start-playing', params: { clubId } } as const;
}
