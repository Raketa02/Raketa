/**
 * The tab tree — five destinations, and the bar that reaches them.
 *
 * It was a `Stack` while Now was the only screen, on the ground that *an empty tab bar
 * over a single route would be chrome pretending to be navigation*. There are five routes
 * now, so it is navigation ([ADR-0082](../../../../../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)).
 *
 * **This file is the only thing that knows a tab key is a route.** `TabBar` is a design
 * primitive: it takes the active key and hands back the pressed one, and the mapping lives
 * here — so the bar stays renderable without a router and `shared/ui` never imports
 * `expo-router`. `TAB_ROUTES` is that mapping and it is exhaustive over `TabKey`, so a
 * sixth tab is a type error here rather than a press that goes nowhere.
 *
 * **A press navigates rather than pushing.** `navigation.navigate` on the tab navigator
 * keeps each tab's own stack where the player left it, which is the whole reason the tabs
 * are a navigator and not five links.
 */

import { Tabs } from 'expo-router';
import type { ComponentProps } from 'react';

import { TabBar, type TabKey } from '@/shared/ui';

/** Which route file each tab reaches, exhaustive over `TabKey`. */
const TAB_ROUTES: Record<TabKey, string> = {
  now: 'index',
  find: 'find',
  create: 'create',
  msg: 'inbox',
  // `account`, not `you`: the screen is the auth feature's own surface and was addressable
  // there before the bar existed. The key and the label are §B13's; the address is ours.
  you: 'account',
};

const TAB_OF_ROUTE: Record<string, TabKey> = Object.fromEntries(
  Object.entries(TAB_ROUTES).map(([tab, route]) => [route, tab as TabKey]),
);

/**
 * The renderer's own props, taken off `Tabs` rather than imported.
 *
 * `@react-navigation/bottom-tabs` is `expo-router`'s dependency and not one of ours;
 * naming it in an import would make this file depend on a package `package.json` does not
 * declare, which is how a transitive bump breaks a build nobody changed.
 */
type TabBarRenderProps = Parameters<NonNullable<ComponentProps<typeof Tabs>['tabBar']>>[0];

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props: TabBarRenderProps) => <AppTabBar {...props} />}
    >
      {/* Declared in the bar's own order, so the navigator's back behaviour and the
          drawn order are one list rather than two that can disagree. */}
      <Tabs.Screen name="index" />
      <Tabs.Screen name="find" />
      <Tabs.Screen name="create" />
      <Tabs.Screen name="inbox" />
      <Tabs.Screen name="account" />
    </Tabs>
  );
}

function AppTabBar({ state, navigation }: TabBarRenderProps) {
  const current = state.routes[state.index];
  const active = TAB_OF_ROUTE[current?.name ?? ''] ?? 'now';

  return (
    <TabBar
      active={active}
      // Nothing counts anything yet. The Inbox count is the badge's only planned source
      // and Inbox is unbuilt, so the prop is left off rather than passed a zero — an
      // absent count and a count of nothing are the same screen, and only one of them is
      // a claim.
      onSelect={(tab) => navigation.navigate(TAB_ROUTES[tab])}
    />
  );
}
