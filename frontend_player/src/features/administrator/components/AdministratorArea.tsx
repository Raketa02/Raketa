/**
 * **The administrator area** — one club's official groups, on its own two tabs, **Groups · You**
 * (club 17–19; [#516](https://github.com/Raketa02/Raketa/issues/516), PRD #500 stories 122–137).
 *
 * The administrator is a second profile inside this app (ADR-0185), so the area is **its own group
 * of screens beside the player's**, not a tab inside them: the player's five tabs are about playing,
 * and an account that only runs a club's groups has not asked to play. It is `shell`'s arrangement
 * a second time — **one stack and one bar under it**, the bar mounted once below the navigator so
 * it owns the bottom inset and never slides in with a screen — and its rule: a tab press lays that
 * tab's root down (`areaNavigation`), and the pushed screens take the push transition back.
 *
 * **The door is the account's profiles** (`useAreaAccess`): an area for a club this account does not
 * administer draws nothing and hands the person to `/`, where the entry gate decides.
 *
 * ## Removed while here
 *
 * The club can remove its Administrator at any moment, and the area hears it one of two ways: the
 * next administrator request is refused (`useRemovalWatch`), or the profile read, re-read on focus,
 * no longer lists the club. Either is answered once (`useLeaveOnRemoval`, `afterRemoval`): an
 * account that holds **nothing but** administrator profiles has nowhere left to be, so it is told
 * and signed out (PRD #500 story 136); one that also plays is told and switched to Player, and one
 * that runs another club's groups to that club's area — the switcher's own move
 * ([#518](https://github.com/Raketa02/Raketa/issues/518)), so the phone keeps it and the next launch
 * opens where the removal left it.
 */

import { useQueryClient } from '@tanstack/react-query';
import { Redirect, Stack, usePathname } from 'expo-router';
import { useCallback, useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';

import { authKeys, useCurrentUser, useSignOut, type AdministeredClub } from '@/features/auth/types';
import { showToast } from '@/shared/store/toast.store';
import { AdministratorTabBar, theme, useSaysTabBarReach } from '@/shared/ui';

import { afterRemoval } from '../domain/removal';
import { useAreaAccess } from '../hooks/useAreaAccess';
import { useRemovalWatch } from '../hooks/useRemovalWatch';

import { removedMessage } from './administratorPresentation';
import { areaTabFor, openAreaTab, useSwitchProfile } from './areaNavigation';
import { HandoverSheet } from './HandoverSheet';
import { InvitationSheet } from './InvitationSheet';

export function AdministratorArea({ clubId }: { readonly clubId: string }) {
  const access = useAreaAccess(clubId);
  // The club this area opened on — kept past a profile read that no longer lists it, because that
  // read is one of the two ways a removal is heard.
  const opened = useRef<AdministeredClub | undefined>(undefined);
  if (access.kind === 'open') opened.current = access.club;

  const leave = useLeaveOnRemoval(clubId, opened);
  useRemovalWatch(leave);

  // **The profile read can say it first.** A screen that asks no administrator route — the You
  // tab — hears a removal from `/users/me`, re-read on focus, which answers without the club. That
  // is the same removal as a refused request, and falling through to `/` instead would send an
  // account with nothing left through the gate into the player's setup, unannounced.
  const user = useCurrentUser();
  const dropped =
    opened.current !== undefined && access.kind === 'elsewhere' && user.data !== undefined;
  useEffect(() => {
    if (dropped) leave();
  }, [dropped, leave]);

  if (access.kind === 'pending' || dropped) return null;
  if (access.kind === 'elsewhere') return <Redirect href="/" />;

  return <AreaShell club={access.club} />;
}

/**
 * **What a removal does, once** — told, then moved where `afterRemoval` says: the player side, the
 * area of another club the account runs, or signed out when nothing is left. Whichever way the
 * removal was heard, and however many requests were refused, it is answered one time.
 */
function useLeaveOnRemoval(
  clubId: string,
  opened: { readonly current: AdministeredClub | undefined },
): () => void {
  const client = useQueryClient();
  const user = useCurrentUser();
  const { mutate: signOut } = useSignOut();
  const switchTo = useSwitchProfile();
  const profiles = user.data?.profiles;
  const left = useRef(false);

  return useCallback(() => {
    const club = opened.current;
    if (left.current || club === undefined || profiles === undefined) return;
    left.current = true;

    const next = afterRemoval(profiles, clubId);
    showToast({ message: removedMessage(club.clubName, { signedOut: next.kind === 'sign-out' }) });
    if (next.kind === 'sign-out') {
      signOut();
      return;
    }
    // What the account holds has changed: the next read of it is the one every profile goes by.
    void client.invalidateQueries({ queryKey: authKeys.currentUser() });
    // **A switch, and kept as one** (#518): the phone's last profile is the removed club's, and a
    // gate reading it — now, before the profile read catches up, or at the next launch — would
    // open that area again.
    switchTo(next);
  }, [client, clubId, opened, profiles, signOut, switchTo]);
}

function AreaShell({ club }: { readonly club: AdministeredClub }) {
  const pathname = usePathname();
  // The area's bar floats over its screens as the player's does, and this shell says its reach —
  // its own shorter bar's (ADR-0210 §3): the area's lists and forms end at it the same way.
  useSaysTabBarReach('administrator', true);

  return (
    <View style={s.area}>
      {/* `initialRouteName` is the Groups tab, stated outright, for the shell's reason: a stack
          rebuilt from nothing opens on its first route, and the pushed screens below are named
          first for their transition. */}
      <Stack initialRouteName="index" screenOptions={{ headerShown: false, animation: 'none' }}>
        {/* New official group and a group's page are pushed over the Groups list and come back
            out to it, a group's Members over its page, and a group's settings and Start playing
            over You; the two tabs' roots replace each other and take the shell's `none`. */}
        <Stack.Screen name="new-group" options={{ animation: 'default' }} />
        <Stack.Screen name="group/[groupId]/index" options={{ animation: 'default' }} />
        <Stack.Screen name="group/[groupId]/members" options={{ animation: 'default' }} />
        <Stack.Screen name="you/settings/[groupId]" options={{ animation: 'default' }} />
        <Stack.Screen name="you/start-playing" options={{ animation: 'default' }} />
      </Stack>
      <AdministratorTabBar
        active={areaTabFor(club.clubId, pathname)}
        onPress={(tab) => openAreaTab(club.clubId, tab, pathname)}
      />
      {/* Another club's invitation is offered here too, over the area it would sit beside (#518). */}
      <InvitationSheet worn={{ kind: 'administrator', clubId: club.clubId }} />
      {/* A club handing this account a group is told here, at whichever club it is (ADR-0192). */}
      <HandoverSheet worn={{ kind: 'administrator', clubId: club.clubId }} />
    </View>
  );
}

const s = StyleSheet.create({
  area: { flex: 1, backgroundColor: theme.color.paper },
});
