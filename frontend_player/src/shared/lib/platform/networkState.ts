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
