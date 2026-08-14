/**
 * The authorization boundary, as a redirect.
 *
 * Expo Router's declarative protected routes landed **after** SDK 52, so until this app
 * moves past it the guard is a redirect keyed on `SessionStatus` — never on
 * `user === undefined`, which conflates "still loading" with "logged out" and produces
 * the login-screen flash. See docs/architecture.md Part 2.
 *
 * The route group is the point: the boundary is visible in the file tree, so a screen
 * added under `(app)/` is guarded by where it was put rather than by remembering to
 * guard it.
 */

import { Redirect, Stack } from "expo-router";

import { useSessionStatus } from "@/shared/lib/auth";

export default function AppLayout() {
  const status = useSessionStatus();

  // Can't happen in practice — `BootstrapGate` renders nothing until the sequence
  // resolves, so no route tree exists while the status is still `bootstrapping`. It is
  // handled anyway because the alternative is falling through to the redirect, which
  // would turn any future change to the gate into a login-screen flash.
  if (status === "bootstrapping") return null;

  if (status === "unauthenticated") return <Redirect href="/sign-in" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
