/**
 * **The datafile, from the flags host** — the one read this feature makes over the network.
 *
 * One file per environment, built by the flags repo and served at
 * `<EXPO_PUBLIC_FEATURES_URL>/<environment>/featurevisor-player.json`
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §3, §4): the Mac's LAN address today, a bucket later, and the same path on both.
 *
 * It comes back `unknown` on purpose. It is not the API's and has no generated type; what it is
 * gets decided by `schemas/`, which is the only thing allowed to say so.
 */

import type { AppEnvironment } from '@/shared/config/env';
import { httpGetFromFeaturesHost } from '@/shared/lib/http';

/** A read Query can cancel — the signal it hands the `queryFn`, forwarded to the socket. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/** Where one environment's datafile is served, under the features host. */
function datafilePath(environment: AppEnvironment): string {
  return `/${environment}/featurevisor-player.json`;
}

export function fetchDatafile(
  environment: AppEnvironment,
  options: Cancellable = {},
): Promise<unknown> {
  return httpGetFromFeaturesHost<unknown>({
    path: datafilePath(environment),
    signal: options.signal,
  });
}
