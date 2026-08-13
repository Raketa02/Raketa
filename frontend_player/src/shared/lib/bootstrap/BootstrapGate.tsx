/**
 * Holds the splash screen up until the startup sequence resolves, then reveals the tree.
 *
 * Bootstrap is a **state**, never `user === undefined`. That ambiguity is what produces
 * the two bugs every mobile app ships once — the login screen flashing while valid
 * credentials are still being read out of the keychain, and the authenticated tree
 * flashing before a redirect. See docs/architecture.md Part 3.
 *
 * A failed launch is shown rather than swallowed. Config that is missing or malformed
 * has no in-app recovery, and leaving the splash up forever turns a one-line fix into a
 * hang with no symptom.
 */

import { useEffect, useRef, useState, type ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { theme } from "@/shared/ui/theme";

import { bootstrapApp } from "./bootstrapApp";
import { hideSplash, preventSplashAutoHide } from "./splash";

// Module scope, so the native splash is pinned before React renders anything at all.
preventSplashAutoHide();

type GateState =
  | { readonly status: "bootstrapping" }
  | { readonly status: "ready" }
  | { readonly status: "failed"; readonly reason: string };

function reasonOf(error: unknown): string {
  return error instanceof Error ? error.message : "The app could not start.";
}

export interface BootstrapGateProps {
  readonly children: ReactNode;
  /** The sequence to run. Overridden only by tests, which drive its timing. */
  readonly run?: () => Promise<void>;
}

export function BootstrapGate({ children, run = bootstrapApp }: BootstrapGateProps) {
  const [state, setState] = useState<GateState>({ status: "bootstrapping" });
  const splashHidden = useRef(false);

  useEffect(() => {
    let live = true;

    run().then(
      () => {
        if (live) setState({ status: "ready" });
      },
      (error: unknown) => {
        if (live) setState({ status: "failed", reason: reasonOf(error) });
      },
    );

    return () => {
      live = false;
    };
  }, [run]);

  if (state.status === "bootstrapping") {
    // Nothing renders behind the splash — not a spinner, not an empty tree.
    return null;
  }

  // Hiding on layout rather than on resolution means the first frame the player sees is
  // already painted, instead of one blank frame between the splash and the tree.
  const onLayout = () => {
    if (splashHidden.current) return;
    splashHidden.current = true;
    hideSplash();
  };

  return (
    <View style={s.root} onLayout={onLayout} testID="app-root">
      {state.status === "failed" ? <StartupFailure reason={state.reason} /> : children}
    </View>
  );
}

function StartupFailure({ reason }: { readonly reason: string }) {
  return (
    <View style={s.failure} accessibilityRole="alert">
      <Text style={s.eyebrow}>Startup failed</Text>
      <Text style={s.title}>Rakieta could not start</Text>
      <View style={s.note}>
        <Text style={s.noteText}>{reason}</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: theme.color.paper,
  },
  failure: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
  },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: "uppercase",
  },
  title: {
    ...theme.type.h1,
    color: theme.color.ink,
  },
  note: {
    backgroundColor: theme.color.redSoft,
    borderRadius: theme.radius.note,
    padding: theme.space.md,
  },
  noteText: {
    ...theme.type.tiny,
    color: theme.color.red,
  },
});
