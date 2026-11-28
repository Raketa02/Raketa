/**
 * **The area's two tabs, as moves** — the player shell's rule, for the administrator's two
 * (`shell`'s `shellNavigation`, [#227](https://github.com/Rakieta02/Rakieta/issues/227)): **one
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
import { useCallback } from 'react';

import { useKeepProfile, type ProfileChoice } from '@/features/auth/types';
import type { AdministratorTabBarKey } from '@/shared/ui';

import { choiceOf, isWorn, type ProfileOption } from '../domain/profiles';

import { administratorHome, administratorYou, areaTabRoot } from './administratorRoutes';

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

/**
 * **Wearing another profile** — instantly, with no password and no new token
 * ([#518](https://github.com/Rakieta02/Rakieta/issues/518), PRD #500 story 134; ADR-0185 §6).
 *
 * Switching is client state: the administrator's authority is not in the token at all, and every
 * administrator route asks the server again. So a switch is two moves and nothing on the wire —
 * **the phone keeps the choice** (`auth`'s `useKeepProfile`, into the cache first, so the entry gate
 * reading it in the next instant already agrees), and **the app goes to that profile's home**:
 * Player's is `/`, where the gate lays the player's app down; an administrator profile's is its
 * club's Groups tab. A removal moves the same way, so the next launch agrees with it too.
 */
export function useSwitchProfile(): (to: ProfileChoice) => void {
  const keep = useKeepProfile();

  return useCallback(
    (to: ProfileChoice) => {
      keep(to);
      router.replace(to.kind === 'player' ? '/' : administratorHome(to.clubId));
    },
    [keep],
  );
}

/**
 * **A row of the profile list pressed** — both sheets that draw one, the switcher and the invitation
 * sheet after Accept: another profile is switched to, and the one worn is no move at all.
 */
export function useChooseProfile(worn: ProfileChoice): (option: ProfileOption) => void {
  const switchTo = useSwitchProfile();

  return useCallback(
    (option: ProfileOption) => {
      if (!isWorn(option, worn)) switchTo(choiceOf(option));
    },
    [switchTo, worn],
  );
}
