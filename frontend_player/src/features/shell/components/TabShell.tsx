/**
 * The shell: one stack, and the bar floating over its foot — **Home · ⚡Play · You**.
 *
 * **A `Stack`, not `<Tabs>`.** `<Tabs>` keeps a separate history per tab and restores it when you
 * come back — which is what it is for, and which breaks *back goes where I came from* without a
 * symptom: a player who leaves a group's page and returns to Play lands back on the page, nothing
 * throws, and the rule is only observable to somebody doing it on purpose
 * ([#227](https://github.com/Raketa02/Raketa/issues/227)). `shellNavigation` replaces rather than
 * pushes, and this file draws the result.
 *
 * **The bar is mounted here, once, over the navigator** — a sibling of the *navigator*, not of
 * each screen: a bar rendered per screen re-mounts on every push and slides in with the screen it
 * belongs behind. One mount is also what lets the bar own the bottom safe-area inset while every
 * screen takes only the top edge.
 *
 * **It floats, and owns no layout** (10.1, [ADR-0210](../../../../../docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md)
 * §3, [#881](https://github.com/Raketa02/Raketa/issues/881)). It was a flex sibling under the
 * stack, which ended every screen above it for free; now every screen inside the tabs draws to the
 * bottom of the phone and the bar is drawn over its foot. What it takes there is its **reach** —
 * its height and the bottom inset while it is drawn, nothing while it stands down — and this shell
 * says it (`useSaysTabBarReach`). Every scroller ends at reach + its gap, the deck's buttons and
 * Post a game stand above it, a pinned button's screen ends at it, and the Undo toast follows it.
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
 * answer is **not render** the bar rather than hide it, and say its reach is nothing: a bar that
 * was present and invisible would still be a reach the screens kept clear of, and the composer
 * would sit that far above the keyboard. Nothing animates it away — the mock draws it absent, and
 * 1.5 is *nothing animates that does not have to*.
 *
 * With the bar gone the bottom safe-area inset has no owner here, and the room takes it on its
 * own frame — the one place in the app where 10.1's *the bar owns the bottom inset* does not
 * hold, and the amendment beside it says so.
 *
 * **On Android it stands down while the keyboard is up, too** (10.1, ADR-0210 §9,
 * [#882](https://github.com/Raketa02/Raketa/issues/882)). Android shrinks the window for the
 * keyboard, and the bar floats at the window's foot, so it would ride up above the keyboard — over
 * the field being typed into, on a form whose page no longer ends above the bar. The same answer
 * as the chat's: not rendered, its reach nothing, so a form ends at its own gap above the keyboard,
 * and nothing animates; it is back when the keyboard goes. An iPhone draws its keyboard over the
 * window, covering the bar already, so there the keyboard changes nothing
 * (`useKeyboardShrinksTheWindow`, the platform module's).
 */

import { router, Stack, usePathname } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { NoticesHost } from '@/features/notifications/types';
import { bookedGameRoute, FillProvider, useHomeBadge } from '@/features/proposals/types';
import { useKeyboardShrinksTheWindow } from '@/shared/lib/platform';
import { TabBar, theme, useSaysTabBarReach } from '@/shared/ui';

import { barStandsDown, tabForPathname } from '../domain/shellTabs';

import { PUSHED_SCREENS } from './pushedScreens';
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

export function TabShell() {
  const pathname = usePathname();
  const gamesNeedingYou = useHomeBadge();
  const keyboardShrinksTheWindow = useKeyboardShrinksTheWindow();
  const barShown = !barStandsDown(pathname) && !keyboardShrinksTheWindow;
  useSaysTabBarReach('player', barShown);

  return (
    <View style={s.shell}>
      {/* The moment a yes fills a game (#555): its ten seconds, its toast above the bar and its
          overlays outlive the screen the yes was said on, so they are held here, around the tabs. */}
      <FillProvider openGame={openGame}>
        {/* `initialRouteName` is the shell's root stated outright — `SHELL_TAB_ROOT.home`, whose
          route is `index` — and it is not the default. expo-router orders a navigator's routes
          with the `Stack.Screen` children below **first**, so without it the first route this
          stack holds is `play/index`, named first for its transition, and a stack rebuilt from
          nothing opens there: a device showed every first press after a cold start landing on
          Play with ⚡Play lit, because the entry gate had torn the tree down for one round trip
          and this stack came back with no history to restore. `theShell.test.tsx` holds it. */}
        <Stack initialRouteName="index" screenOptions={{ headerShown: false, animation: 'none' }}>
          {/* Every screen pushed over a tab takes the push back — named one by one in
            `pushedScreens`, which says what each is pushed over and holds the list to the tree. */}
          {PUSHED_SCREENS.map((name) => (
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
