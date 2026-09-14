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
 * ## The shell now holds one query, and that is the honest price of a badge
 *
 * #227's finding was that *"the shell remembers nothing"*, and it is **amended rather than
 * quietly contradicted** ([#326](https://github.com/Raketa02/Raketa/issues/326) §7): the bar
 * carries a count of unanswered challenges addressed to you, and a count on permanent chrome
 * has to come from somewhere. It is mounted **here** rather than read by the bar, because
 * `shared/ui` importing a feature hook would invert the dependency and give a drawn object a
 * network call — so the shell reads and the bar takes a number.
 *
 * It shares `challengeKeys.list()` with the Chats screen's own section, and TanStack dedupes
 * the two mounts to one request. Reading the cache only was rejected: it would leave the badge
 * blank on a cold start until the player visited Chats, making the count a reward for having
 * already looked, which inverts its job.
 * **The same path decides whether a press is a move at all.** `openTab` takes it and declines
 * the one case where the tab pressed is the screen already on — which used to lay the stack
 * down again and rebuild Find a game underneath the player. It is handed the value the lit
 * column is drawn from rather than a second read of its own, for the reason above.
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
 *
 * ## The bar stands down inside a conversation and on the yes screen, and standing down is not being drawn
 *
 * One screen replaces the bar with its composer, so the keyboard and the stream get the whole
 * screen ([#400](https://github.com/Raketa02/Raketa/issues/400)); a second — the yes screen —
 * replaces it with nothing, because the screen is the whole phone and its two doors are the only
 * ways out ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2). Which screens is `barStandsDown`'s answer, read off the same pathname the active column
 * is — the shell learns that *a route* stands the bar down and nothing about what either is. What it does with
 * the answer is **not render** the bar rather than hide it: the bar is a flex sibling of the
 * navigator, so a bar that was present and invisible would still take `TAB_BAR_HEIGHT` and the
 * bottom inset, and the composer would sit that far above the keyboard. Nothing animates it away
 * — the mock draws it absent, and 1.5 is *nothing animates that does not have to*; what happens
 * at the edges of the push is the stack growing by the bar's height as the room slides in and
 * shrinking as it slides out, **which has not been seen on a device either**.
 *
 * With the bar gone the bottom safe-area inset has no owner here, and the room takes it on its
 * own frame — the one place in the app where 10.1's *the bar owns the bottom inset* does not
 * hold, and the amendment beside it says so.
 */

import { Stack, usePathname } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { useChallengesWaiting } from '@/features/challenges/types';
import { TabBar, theme } from '@/shared/ui';

import { barStandsDown, tabForPathname } from '../domain/shellTabs';

import { openTab } from './shellNavigation';

export function TabShell() {
  const pathname = usePathname();
  const challengesWaiting = useChallengesWaiting();

  return (
    <View style={s.shell}>
      {/* `initialRouteName` is the shell's root stated outright — `SHELL_TAB_ROOT.now`, whose
          route is `index` — and it is not the default. expo-router orders a navigator's routes
          with the `Stack.Screen` children below **first**, so without it the first route this
          stack holds is `play/index`, named first for its transition, and a stack rebuilt from
          nothing opens there: a device showed every first press after a cold start landing on
          Find a game with ⚡Play lit, because the entry gate had torn the tree down for one round
          trip and this stack came back with no history to restore. `theShell.test.tsx` holds it. */}
      <Stack initialRouteName="index" screenOptions={{ headerShown: false, animation: 'none' }}>
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
        {/* And so is a game: it is pushed over the Now tab's list, the list stays underneath,
            and backing out returns to the row it was tapped from
            ([#314](https://github.com/Raketa02/Raketa/issues/314)). It is the first exception
            outside Play, which is why `shellTabs` had to say which tab it is inside. */}
        <Stack.Screen name="games/[gameId]" options={{ animation: 'default' }} />
        {/* And so is a challenge: it is pushed over the Chats inbox, the list stays underneath,
            and backing out returns to the row it was tapped from
            ([#360](https://github.com/Raketa02/Raketa/issues/360)). It needs no `INSIDE_A_TAB`
            entry, because everything under `/chats/…` already shares that tab's first segment
            — which is the whole reason both of this map's dynamic ids live under it. */}
        <Stack.Screen
          name="chats/challenge/[challengeId]/index"
          options={{ animation: 'default' }}
        />
        {/* And so is the builder reached from one: `features/play`'s own screen at a **second
            route** under the challenge it completes, pushed exactly as its first route is
            ([ADR-0150](../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
            §7). Nothing in that flow calls the reset — the send **pops back** to the challenge,
            which is the surface that draws the result. */}
        <Stack.Screen
          name="chats/challenge/[challengeId]/fill"
          options={{ animation: 'default' }}
        />
        {/* And the yes screen under a challenge — pushed over the challenge screen the instant
            *I'm in* is answered, and the one route whose **swipe-back is off**: a swipe that
            popped to the challenge screen underneath would land somewhere *Later* never does
            ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
            §1). It keeps the shell's own `none`, deliberately: the screen has one motion of its
            own, and a push that slid in under it would be a second. The bar stands down on it,
            below, as it does in the room. */}
        <Stack.Screen
          name="chats/challenge/[challengeId]/yes"
          options={{ gestureEnabled: false }}
        />
        {/* And so is a conversation: it is pushed over the Chats inbox, the list stays
            underneath, and backing out returns to the row it was tapped from — the challenge
            screen's argument, one row kind over ([#400](https://github.com/Raketa02/Raketa/issues/400)).
            It is one of the two screens the bar stands down on, below. */}
        <Stack.Screen
          name="chats/conversation/[conversationId]/index"
          options={{ animation: 'default' }}
        />
      </Stack>
      {barStandsDown(pathname) ? null : (
        <TabBar
          active={tabForPathname(pathname)}
          onPress={(tab) => openTab(tab, pathname)}
          challengesWaiting={challengesWaiting}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  shell: { flex: 1, backgroundColor: theme.color.paper },
});
