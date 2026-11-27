/**
 * **The hold** — the one interface between the tree and the launch gate
 * ([ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §3).
 *
 * The splash fades into the first screen, already drawn underneath. But a screen can be mounted and
 * laid out and still draw nothing — the entry gate's *pending*, the one blank state after startup —
 * and fading into it would be the blank frame the brief forbids. So **a screen under the splash can
 * declare itself blank**, and while any declaration stands, the fade does not start. A screen that
 * answers withdraws it. The hold delays only the fade: it never replays motion, and once the fade
 * has begun nothing stops it.
 *
 * This is what lets the shared gate know when the first screen has answered **without importing a
 * feature**: the feature says so, through this.
 *
 * **A hold that is never withdrawn keeps the splash up for good.** Today only the entry gate holds,
 * and only while *pending*. A second user is a review question (ADR-0209, *Harder*).
 */

import { createContext, useContext, useLayoutEffect, type ReactNode } from 'react';

/** Where a screen declares itself blank. */
export interface SplashHolds {
  /** Declares the screen blank; the function it returns withdraws the declaration. */
  readonly place: () => () => void;
}

/**
 * Outside a launch gate — the router suites' own test root, which never draws a splash — a hold
 * goes nowhere, because there is nothing to hold.
 */
const NOWHERE: SplashHolds = { place: () => () => {} };

const SplashHoldsContext = createContext<SplashHolds>(NOWHERE);

export interface SplashHoldsProviderProps {
  readonly holds: SplashHolds;
  readonly children: ReactNode;
}

/** The launch gate's, around the tree it mounts; a test's, around a tree it wants to read. */
export function SplashHoldsProvider({ holds, children }: SplashHoldsProviderProps) {
  return <SplashHoldsContext.Provider value={holds}>{children}</SplashHoldsContext.Provider>;
}

/**
 * Declares this screen blank for as long as `blank` is true and the screen is mounted.
 *
 * In a **layout** effect, so the declaration stands before the tree's layout reaches the gate: a
 * passive effect can land after it, and the gate would see a laid-out tree with no hold for a frame.
 */
export function useSplashHold(blank: boolean): void {
  const holds = useContext(SplashHoldsContext);

  useLayoutEffect(() => {
    if (!blank) return;
    return holds.place();
  }, [blank, holds]);
}
