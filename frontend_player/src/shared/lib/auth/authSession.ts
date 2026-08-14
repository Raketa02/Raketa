/**
 * The session state machine — the one place the app's answer to "is anyone signed in?"
 * lives.
 *
 * It holds a **status and nothing else**. In particular it does not hold the current
 * user: that is backend data, TanStack Query owns it, and a second copy here would be a
 * mirror the one-owner rule exists to forbid (docs/architecture.md Part 1). A screen
 * that needs a nickname asks the profile query; a screen that needs to know whether to
 * render at all asks this.
 *
 * It is an external store rather than React state because the answer is needed outside
 * React — by the sign-out path and, later, by #22's rotation — and because the routing
 * guard must read it synchronously during render.
 */

import { useSyncExternalStore } from "react";

import type { SessionStatus } from "./auth.types";

type Listener = () => void;

let status: SessionStatus = "bootstrapping";
const listeners = new Set<Listener>();

function emit(): void {
  for (const listener of listeners) listener();
}

export function getSessionStatus(): SessionStatus {
  return status;
}

/**
 * Move the machine. Idempotent: setting the status it already holds notifies nobody.
 *
 * That matters for sign-out, which several failing requests can reach at once. A
 * transition that re-emitted would re-run every subscriber's effect per caller, and the
 * redirect would fire repeatedly.
 */
export function setSessionStatus(next: SessionStatus): void {
  if (status === next) return;
  status = next;
  emit();
}

export function subscribeToSession(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Test seam. Returns the machine to its pre-bootstrap state. */
export function resetSessionStatus(): void {
  status = "bootstrapping";
  listeners.clear();
}

/**
 * The status, for React. The guard in `(app)/_layout.tsx` and the auth screens read it
 * through here.
 *
 * `getSessionStatus` doubles as the server snapshot: this app has no SSR, and expo-router
 * still asks for one on web.
 */
export function useSessionStatus(): SessionStatus {
  return useSyncExternalStore(subscribeToSession, getSessionStatus, getSessionStatus);
}
