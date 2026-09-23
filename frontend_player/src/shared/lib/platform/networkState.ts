/**
 * `onlineManager`, wired to native connectivity.
 *
 * Query's default online check is `navigator.onLine`, which React Native either does not
 * provide or reports as a constant. Left unwired, `networkMode: 'online'` believes the
 * app is permanently online: queries fail instead of pausing, paused mutations never
 * resume, and nothing refetches when signal comes back.
 *
 * `expo-network` is the SDK-supported source. It joined package.json with this file —
 * the architecture lists it as required and not yet present, and a dependency is added
 * because code needs it, never preemptively.
 */

import { useSyncExternalStore } from 'react';

import * as Network from 'expo-network';
import { onlineManager } from '@tanstack/react-query';

/**
 * Reachability, not merely "an interface is up".
 *
 * A phone attached to a captive-portal wifi has `isConnected === true` and reaches
 * nothing. `isInternetReachable` is the honest signal; it is `null` while the platform
 * is still deciding, and an undecided answer is treated as online — pausing every query
 * on a maybe would strand the app at launch on connections that are perfectly fine.
 */
function isOnline(state: Network.NetworkState): boolean {
  if (state.isConnected !== true) return false;
  return state.isInternetReachable !== false;
}

/** Called once, by the bootstrap sequence. Returns the unsubscribe for tests. */
export function wireOnlineManager(): () => void {
  const subscription = Network.addNetworkStateListener((state) => {
    onlineManager.setOnline(isOnline(state));
  });

  // The listener only fires on *change*, so the first value has to be asked for. A
  // failure here is not fatal: assume online and let the first request find out.
  void Network.getNetworkStateAsync().then(
    (state) => onlineManager.setOnline(isOnline(state)),
    () => onlineManager.setOnline(true),
  );

  return () => subscription.remove();
}

/**
 * Whether the app believes it can reach the network **right now**, as a subscription.
 *
 * `onlineManager` is already the app's one answer to that question — it is what
 * `networkMode: 'online'` pauses on, wired above to `expo-network` rather than to
 * `navigator.onLine` — so a second source here would be a second opinion, and the two would
 * first disagree during the moment a screen is deciding what to say about the first one.
 *
 * **It has exactly one caller, and that caller is not a correctness mechanism.** The send is
 * the one act in this app that fails now rather than pausing
 * (`features/challenges/hooks/challengeMutationOptions.ts`), and `docs/architecture.md` Part 11
 * is explicit that *"button disabling is UX, not correctness"* — so this closes the control and
 * states the reason beside it, while the
 * `networkMode` override is what actually keeps a deadline the player did not choose out of the
 * queue. Everything else in the app pauses and says so from `isPaused`, which needs no hook at
 * all: a paused request reports its own state.
 *
 * `useSyncExternalStore` rather than an effect and a `useState`, because the manager is an
 * external store and the first paint has to be right: an effect would render one frame of *you
 * are online* to a player who is not.
 */
export function useIsOnline(): boolean {
  return useSyncExternalStore(
    (notify) => onlineManager.subscribe(notify),
    () => onlineManager.isOnline(),
    // The server snapshot. React Native never renders on a server, and a `getServerSnapshot`
    // that disagreed with the client one would be a hydration mismatch nothing here can have —
    // it is passed so the signature is total rather than because a second environment exists.
    () => true,
  );
}
