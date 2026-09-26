/**
 * **Where the administrator area lives** — its own group of screens, outside the player's tab shell
 * (PRD #500: *its own group of screens outside the player's tab shell*), one area per club it runs:
 * `/administrator/<club>` is the Groups tab, `…/you` the You tab, and New official group and a
 * group's page are pushed over Groups.
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
