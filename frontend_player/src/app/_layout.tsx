/**
 * The root layout: the only place providers are composed, and the gate the bootstrap
 * sequence resolves behind.
 *
 * docs/architecture.md Part 3 fixes the order — reporting wraps everything so it can see
 * failures, and auth sits above Query so a session change can reach the cache. Each
 * provider joins as its slice lands; a feature never adds a global one.
 *
 * The session has no provider of its own: `shared/lib/auth` is an external store, read
 * through `useSessionStatus`. A context would make the status unreadable from the
 * sign-out path and from #22's rotation, both of which live outside React.
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { Slot } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useCallback } from "react";
import { SafeAreaProvider, initialWindowMetrics } from "react-native-safe-area-context";

import { authKeys, restoreSession } from "@/features/auth/types";
import { BootstrapGate, bootstrapApp, sharedBootstrapSteps } from "@/shared/lib/bootstrap";
import { queryClient } from "@/shared/lib/query-client";

/**
 * The one step `shared/` cannot supply itself: restoring a session belongs to the auth
 * feature, and `shared/lib/bootstrap` may never import a feature. Composing them is a
 * route file's job, which is why this adapter is here and is this small.
 *
 * Seeding the cache with the validated player is the "prefer response-driven updates"
 * rule at launch: bootstrap already asked the server who this is, so the first screen
 * should not ask again.
 */
async function restoreSessionStep(): Promise<void> {
  const restored = await restoreSession();
  if (restored.user !== undefined) {
    queryClient.setQueryData(authKeys.currentUser(), restored.user);
  }
}

export default function RootLayout() {
  const run = useCallback(
    () => bootstrapApp({ ...sharedBootstrapSteps, restoreSession: restoreSessionStep }),
    [],
  );

  return (
    // `initialMetrics` lets the first frame use real insets instead of measuring one
    // frame later — the same reflow the fonts are awaited to avoid.
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      <StatusBar style="dark" />
      <QueryClientProvider client={queryClient}>
        <BootstrapGate run={run}>
          <Slot />
        </BootstrapGate>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
