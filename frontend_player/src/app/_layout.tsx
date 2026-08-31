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

import { QueryClientProvider } from '@tanstack/react-query';
import { Slot } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback } from 'react';
import { SafeAreaProvider, initialWindowMetrics } from 'react-native-safe-area-context';

import { authKeys, refreshTokens, restoreSession } from '@/features/auth/types';
import { EnvironmentBadge } from '@/shared/config/EnvironmentBadge';
import { wireHttpCredentials } from '@/shared/lib/auth';
import { BootstrapGate, bootstrapApp, sharedBootstrapSteps } from '@/shared/lib/bootstrap';
import { queryClient } from '@/shared/lib/query-client';
import { ReducedMotionProvider, ToastHost } from '@/shared/ui';

/**
 * Hand the HTTP client its credential adapter, including the wire call its 401 rotation
 * needs. The rotation itself lives in `shared/`; only the endpoint comes from the feature,
 * because only a feature's `api/` layer may read the generated wire types.
 */
function wireCredentialsStep(): void {
  wireHttpCredentials(refreshTokens);
}

/**
 * The other step `shared/` cannot supply itself: restoring a session belongs to the auth
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
    () =>
      bootstrapApp({
        ...sharedBootstrapSteps,
        wireCredentials: wireCredentialsStep,
        restoreSession: restoreSessionStep,
      }),
    [],
  );

  return (
    // `initialMetrics` lets the first frame use real insets instead of measuring one
    // frame later — the same reflow the fonts are awaited to avoid.
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      <StatusBar style="dark" />
      <QueryClientProvider client={queryClient}>
        {/*
         * One subscription to the OS's reduced-motion switch, for every screen. It was a hook
         * per consumer while the consumers were two overlays; the Play tab's always-mounted
         * surfaces — a press transform, the fill's staggered seats — are what its own docstring
         * named as the moment it becomes the context Part 13 describes.
         */}
        <ReducedMotionProvider>
          <BootstrapGate run={run}>
            <Slot />
            {/*
             * A sibling of the route tree rather than part of it, so the badge is on every
             * screen without a screen having to know it exists — and inside the gate, so
             * it reads config only after bootstrap has validated it. Nothing at all in
             * production.
             */}
            <EnvironmentBadge />
            {/*
             * design-system 9.3's single root-level overlay host, and its first occupant.
             * `zIndex` is scoped to the parent in React Native, so a toast raised from inside
             * a card renders inside that card — mounting it once here is what makes the layer
             * order mean anything. One host, one queue: `shared/store/toast.store.ts`.
             */}
            <ToastHost />
          </BootstrapGate>
        </ReducedMotionProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
