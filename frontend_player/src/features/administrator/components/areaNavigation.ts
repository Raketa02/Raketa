/**
 * **The area's two tabs, as moves** — the player shell's rule, for the administrator's two
 * (`shell`'s `shellNavigation`, [#227](https://github.com/Raketa02/Raketa/issues/227)): **one
 * stack, and a tab press lays that tab's root down in place of whatever was on it.** Pressing
 * Groups from a group's page lands on the Groups list, never on the page; pressing the tab already
 * showing its root is not a move at all.
 *
 * Which tab is lit is read off the path rather than held in state, for the shell's reason: a copy
 * of it would be a second answer, free to disagree with the router after a redirect or the hardware
 * back button. The You tab is its root and every group's settings pushed over it; everything else
 * under the area is inside Groups — New official group and every group's page are pushed over the
 * list.
 */

import { router } from 'expo-router';

import type { AdministratorTabBarKey } from '@/shared/ui';

import { administratorYou, areaTabRoot } from './administratorRoutes';

/** Which of the two tabs a pathname is inside: the You tab and what is under it, or Groups. */
export function areaTabFor(clubId: string, pathname: string): AdministratorTabBarKey {
  const you = administratorYou(clubId);
  return pathname === you || pathname.startsWith(`${you}/`) ? 'you' : 'groups';
}

/** Open a tab at its root — unless that root is already where the person is. */
export function openAreaTab(clubId: string, tab: AdministratorTabBarKey, where: string): void {
  const root = areaTabRoot(clubId, tab);
  if (where === root) return;

  if (router.canDismiss()) router.dismissAll();
  router.replace(root);
}
