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
import { PrototypeScreen } from '@/prototype-tabbar/PrototypeScreen';
import { queryClient } from '@/shared/lib/query-client';

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

/* ------------------------------------------------------------------------- *
 * PROTOTYPE — branch `prototype/tabbar-glyphs`, Raketa02/Raketa#49.
 * Delete this block and restore `<Slot />` when the branch is thrown away.
 *
 * The tab bar is a design-system primitive, so it needs the real fonts and the real
 * theme — but nothing behind the auth gate, and no backend. So the bootstrap sequence
 * still runs (config, then Archivo and IBM Plex Mono) with the session step stubbed
 * out, and the route tree is replaced by the prototype screen.
 * ------------------------------------------------------------------------- */
const PROTOTYPE_TAB_BAR = true;

async function noRestoreStep(): Promise<void> {}

export default function RootLayout() {
  const run = useCallback(
    () =>
      bootstrapApp({
        ...sharedBootstrapSteps,
        wireCredentials: wireCredentialsStep,
        restoreSession: PROTOTYPE_TAB_BAR ? noRestoreStep : restoreSessionStep,
      }),
    [],
  );

  return (
    // `initialMetrics` lets the first frame use real insets instead of measuring one
    // frame later — the same reflow the fonts are awaited to avoid.
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      <StatusBar style="dark" />
      <QueryClientProvider client={queryClient}>
        <BootstrapGate run={run}>
          {PROTOTYPE_TAB_BAR ? <PrototypeScreen /> : <Slot />}
          {/*
           * A sibling of the route tree rather than part of it, so the badge is on every
           * screen without a screen having to know it exists — and inside the gate, so
           * it reads config only after bootstrap has validated it. Nothing at all in
           * production.
           */}
          <EnvironmentBadge />
        </BootstrapGate>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
