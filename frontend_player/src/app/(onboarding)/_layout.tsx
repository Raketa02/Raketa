/**
 * Onboarding — a sibling of `(app)`, not a child of it.
 *
 * The nesting matters: the authenticated tree's layout is where the entry gate redirects
 * *into* this group, so onboarding sitting inside it would make the gate a loop.
 *
 * It carries its own session guard for the same reason `(auth)` does — the boundary is a
 * property of where a screen lives, not of how a player happened to arrive.
 */

import { Redirect, Stack } from "expo-router";

import { useSessionStatus } from "@/shared/lib/auth";

export default function OnboardingLayout() {
  const status = useSessionStatus();

  if (status === "bootstrapping") return null;

  if (status === "unauthenticated") return <Redirect href="/sign-in" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
