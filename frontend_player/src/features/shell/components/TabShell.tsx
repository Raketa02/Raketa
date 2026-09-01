/**
 * The five-tab shell: one stack, and the bar under it.
 *
 * **A `Stack`, not `<Tabs>`, and that is the ticket's one new decision.** `<Tabs>` keeps a
 * separate history per tab and restores it when you come back — which is what it is for, and
 * which breaks *back goes where I came from* without a symptom: a player who leaves the deck
 * and returns to Play lands back on the deck, nothing throws, and the rule is only observable
 * to somebody doing it on purpose ([#227](https://github.com/Raketa02/Raketa/issues/227)).
 * Four of the five tabs are single-screen roots and only Play has depth, so five histories
 * were never the shape; `shellNavigation` replaces rather than pushes, and this file draws
 * the result.
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
 * ## The transition says which of the two moves happened
 *
 * A `Stack`'s default is the push transition, and the shell's ordinary move is a **replace** —
 * so out of the box, going from Now to Around slides in from the right and reads as going
 * *deeper* on the one gesture whose whole meaning is that nothing was kept. The shell's
 * default is therefore `none`, and the two Play screens take the push back, because entering
 * Find a game and pushing the deck over it genuinely are ones: what they arrive on stays
 * underneath, and leaving should read as coming back out. **This is the one thing in the shell
 * that has not been seen on a device.**
 */

import { Stack, usePathname } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { TabBar, theme } from '@/shared/ui';

import { tabForPathname } from '../domain/shellTabs';

import { openTab } from './shellNavigation';

export function TabShell() {
  const pathname = usePathname();

  return (
    <View style={s.shell}>
      <Stack screenOptions={{ headerShown: false, animation: 'none' }}>
        <Stack.Screen name="play/index" options={{ animation: 'default' }} />
        {/* The deck is genuinely pushed: Find a game stays underneath it, so the transition
            that reads as *going deeper* is the true one — the same exception, for the same
            reason ([#270](https://github.com/Raketa02/Raketa/issues/270)). */}
        <Stack.Screen name="play/deck" options={{ animation: 'default' }} />
        {/* And so are the builder and the pool: a finished search is pushed onto the court and
            a seat is pushed onto the pool, and both come back out
            ([#271](https://github.com/Raketa02/Raketa/issues/271)). The exception is named per
            screen rather than per prefix because a Play route that is genuinely a **replace**
            — there is not one yet — must take the shell's own `none` back. */}
        <Stack.Screen name="play/builder" options={{ animation: 'default' }} />
        <Stack.Screen name="play/pool" options={{ animation: 'default' }} />
      </Stack>
      <TabBar active={tabForPathname(pathname)} onPress={openTab} />
    </View>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1, backgroundColor: theme.color.paper },
});
