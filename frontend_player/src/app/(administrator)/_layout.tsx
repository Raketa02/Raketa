/**
 * **The administrator area** — a sibling of `(app)`, not a child of it
 * ([#516](https://github.com/Raketa02/Raketa/issues/516), ADR-0185).
 *
 * The nesting matters for onboarding's reason: `(app)`'s entry gate redirects *into* this group
 * an account that only runs a club's groups, so the area sitting inside `(app)` would put it behind
 * the gate it is the gate's answer to. And the administrator is a second profile with its own tabs,
 * not a tab inside the player's shell.
 *
 * It carries its own session guard for the same reason `(auth)` and `(onboarding)` do — the
 * boundary is a property of where a screen lives, not of how somebody happened to arrive. Which
 * club's area a person may be in is the next layout's, which knows the club.
 */

import { Redirect, Stack } from 'expo-router';

import { useSessionStatus } from '@/shared/lib/auth';

export default function AdministratorLayout() {
  const status = useSessionStatus();

  if (status === 'bootstrapping') return null;

  if (status === 'unauthenticated') return <Redirect href="/sign-in" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
