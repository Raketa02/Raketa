/**
 * The root layout: the only place providers are composed, and the gate the bootstrap
 * sequence resolves behind.
 *
 * docs/architecture.md Part 3 fixes the eventual order — reporting wraps everything so
 * it can see failures, and auth sits above Query so a session change can reach the
 * cache. Each provider joins as its slice lands; a feature never adds a global one.
 */

import { Slot } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, initialWindowMetrics } from "react-native-safe-area-context";

import { BootstrapGate } from "@/shared/lib/bootstrap";

export default function RootLayout() {
  return (
    // `initialMetrics` lets the first frame use real insets instead of measuring one
    // frame later — the same reflow the fonts are awaited to avoid.
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      <StatusBar style="dark" />
      <BootstrapGate>
        <Slot />
      </BootstrapGate>
    </SafeAreaProvider>
  );
}
