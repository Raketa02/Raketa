/**
 * The shell: one stack, and the bar under it — **Home · ⚡Play · You**.
 *
 * **A `Stack`, not `<Tabs>`.** `<Tabs>` keeps a separate history per tab and restores it when you
 * come back — which is what it is for, and which breaks *back goes where I came from* without a
 * symptom: a player who leaves a group's page and returns to Play lands back on the page, nothing
 * throws, and the rule is only observable to somebody doing it on purpose
 * ([#227](https://github.com/Raketa02/Raketa/issues/227)). `shellNavigation` replaces rather than
 * pushes, and this file draws the result.
 *
 * **The bar is mounted here, once, below the navigator.** Design-system 10.1 lists it inside
 * the screen structure, and it is a flex sibling exactly as that says — but a sibling of the
 * *navigator*, not of each screen: a bar rendered per screen re-mounts on every push and
 * slides in with the screen it belongs behind. One mount is also what lets the bar own the
 * bottom safe-area inset while every screen takes only the top edge.
 *
 * The active column is read from the current path rather than held in state. The bar is a
 * drawn object that takes an answer, and the answer is a fact about where the player is —
 * a copy of it in a store would be a second answer, free to disagree with the router after
 * a deep link, a redirect, or the hardware back button.
 *
 * ## The shell holds one query, and that is the honest price of a badge
 *
 * #227's finding was that *"the shell remembers nothing"*, and it is **amended rather than
 * quietly contradicted** ([#326](https://github.com/Raketa02/Raketa/issues/326) §7): the bar
 * carries a count of the booked games that need you, and a count on permanent chrome has to come
 * from somewhere. It is read **here** rather than by the bar, because `shared/ui` importing a
 * feature hook would invert the dependency and give a drawn object a network call — so the shell
 * reads and the bar takes a number. It is Home's own read (`GET /home`), so TanStack dedupes the
 * two mounts to one request, and whatever invalidates it — a fill, a foreground — re-reads it at
 * once. Since the old loop left ([#576](https://github.com/Raketa02/Raketa/issues/576)) it is the
 * only list the shell holds: the old games, plans and challenges reads went with it.
 *
 * **The same path decides whether a press is a move at all.** `openTab` takes it and declines
 * the one case where the tab pressed is the screen already on — which used to lay the stack
 * down again and rebuild the tab underneath the player. It is handed the value the lit column is
 * drawn from rather than a second read of its own, for the reason above.
 *
 * ## The transition says which of the two moves happened
 *
 * A `Stack`'s default is the push transition, and the shell's ordinary move is a **replace** —
 * so out of the box, going from Home to You slides in from the right and reads as going
 * *deeper* on the one gesture whose whole meaning is that nothing was kept. The shell's
 * default is therefore `none`, and the screens pushed over a tab take the push back, because
 * what they arrive on stays underneath, and leaving should read as coming back out. **This is
 * the one thing in the shell that has not been seen on a device.**
 *
 * ## The bar stands down inside a booked game's chat, and standing down is not being drawn
 *
 * The room replaces the bar with its composer, so the keyboard and the stream get the whole
 * screen ([#400](https://github.com/Raketa02/Raketa/issues/400)). Which screen is
 * `barStandsDown`'s answer, read off the same pathname the active column is — the shell learns
 * that *a route* stands the bar down and nothing about what a room is. What it does with the
 * answer is **not render** the bar rather than hide it: the bar is a flex sibling of the
 * navigator, so a bar that was present and invisible would still take `TAB_BAR_HEIGHT` and the
 * bottom inset, and the composer would sit that far above the keyboard. Nothing animates it away
 * — the mock draws it absent, and 1.5 is *nothing animates that does not have to*.
 *
 * With the bar gone the bottom safe-area inset has no owner here, and the room takes it on its
 * own frame — the one place in the app where 10.1's *the bar owns the bottom inset* does not
 * hold, and the amendment beside it says so.
 */

import { router, Stack, usePathname } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { NoticesHost } from '@/features/notifications/types';
import { bookedGameRoute, FillProvider, useHomeBadge } from '@/features/proposals/types';
import { TAB_BAR_HEIGHT, TabBar, theme } from '@/shared/ui';

import { barStandsDown, tabForPathname } from '../domain/shellTabs';

import { landOnHome, openTab } from './shellNavigation';

/**
 * *It's a game!*'s *Open game* (#555): Home laid down and the booked game's details pushed over it,
 * so back from the game is Home, where a booked game lives (the screens A2.4). The shell's move,
 * handed to the fill rather than imported by it — `proposals` never imports the shell that mounts
 * it. The details are a booking's (#556, A4.1), at the route `proposals` spells.
 */
function openGame(bookingId: string) {
  landOnHome();
  router.push(bookedGameRoute(bookingId));
}

/**
 * The screens behind the You tab's rows — every route under `you/` except the tab's own root.
 * The list rather than a prefix, because `Stack.Screen` matches on the name and a wildcard
 * would put the push on the root too.
 */
const YOU_SCREENS = [
  'you/passport',
  'you/reliability',
  'you/kind-of-game',
  'you/week',
  'you/radius',
  'you/area',
  'you/who-you-play-with',
  'you/game-suggestions',
  'you/photos',
  'you/tags',
  'you/intro',
  'you/name',
  'you/games-and-money',
  'you/payments',
  'you/notifications',
] as const;

export function TabShell() {
  const pathname = usePathname();
  const gamesNeedingYou = useHomeBadge();
  const barShown = !barStandsDown(pathname);

  return (
    <View style={s.shell}>
      {/* The moment a yes fills a game (#555): its ten seconds, its toast above the bar and its
          overlays outlive the screen the yes was said on, so they are held here, around the tabs. */}
      <FillProvider toastAbove={barShown ? TAB_BAR_HEIGHT : 0} openGame={openGame}>
        {/* `initialRouteName` is the shell's root stated outright — `SHELL_TAB_ROOT.home`, whose
          route is `index` — and it is not the default. expo-router orders a navigator's routes
          with the `Stack.Screen` children below **first**, so without it the first route this
          stack holds is `play/index`, named first for its transition, and a stack rebuilt from
          nothing opens there: a device showed every first press after a cold start landing on
          Play with ⚡Play lit, because the entry gate had torn the tree down for one round trip
          and this stack came back with no history to restore. `theShell.test.tsx` holds it. */}
        <Stack initialRouteName="index" screenOptions={{ headerShown: false, animation: 'none' }}>
          <Stack.Screen name="play/index" options={{ animation: 'default' }} />
          {/* And the groups screens (#512, #513, #514): New group and Join a group are pushed over
            the Groups list and come back out to it, and a group's page is pushed over the list —
            or replaces New group once the group exists, so *back* is the list either way.
            Friends, Members and Edit group are pushed over the page and come back out to it. */}
          <Stack.Screen name="play/new-group" options={{ animation: 'default' }} />
          <Stack.Screen name="play/join" options={{ animation: 'default' }} />
          <Stack.Screen name="play/group/[groupId]/index" options={{ animation: 'default' }} />
          <Stack.Screen name="play/group/[groupId]/friends" options={{ animation: 'default' }} />
          <Stack.Screen name="play/group/[groupId]/members" options={{ animation: 'default' }} />
          <Stack.Screen name="play/group/[groupId]/edit" options={{ animation: 'default' }} />
          {/* And so is a booked game (#556): its details pushed over Home, its chat and its
            result pushed over the details — each comes back out to the screen it was opened from.
            The chat is the one screen the bar stands down on (`shellTabs`). */}
          <Stack.Screen name="booking/[bookingId]/index" options={{ animation: 'default' }} />
          <Stack.Screen name="booking/[bookingId]/chat" options={{ animation: 'default' }} />
          <Stack.Screen name="booking/[bookingId]/result" options={{ animation: 'default' }} />
          {/* And so are the recent notices behind Home's bell (#559): pushed over Home, and back
            is Home — a row opens its game over the list, so back from the game is the list. */}
          <Stack.Screen name="notices" options={{ animation: 'default' }} />
          {/* And so is every screen behind a row on You: each is pushed over the tab, the tab
            stays underneath, and backing out returns to the row it was tapped from
            ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
            §1). Named one by one, as every exception is: `you/index` is the tab's root, arrived
            at by a tab press, and takes the shell's own `none` like every root. */}
          {YOU_SCREENS.map((name) => (
            <Stack.Screen key={name} name={name} options={{ animation: 'default' }} />
          ))}
        </Stack>
        {barShown ? (
          <TabBar
            active={tabForPathname(pathname)}
            onPress={(tab) => openTab(tab, pathname)}
            gamesNeedingYou={gamesNeedingYou}
          />
        ) : null}
        {/* The notices (#559), for the session: the phone registered, a push while the app is
            open drawn as the banner over every screen and the bar, and a push tapped opening its
            game. Held here for the fill's reason — all three outlive the screen the player is on. */}
        <NoticesHost />
      </FillProvider>
    </View>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1, backgroundColor: theme.color.paper },
});
