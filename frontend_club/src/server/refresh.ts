import 'server-only';

import { clubApi } from './backend';
import { settle, type ApiError } from './outcome';
import { sessionFromPair, type ClubSession } from './session';

/**
 * **The refresh, single-flight per session.**
 *
 * The backend rotates a refresh token every time it is presented, so two refreshes of the same
 * token race, and the second is refused as spent. A browser makes that race easily: a page and
 * its prefetches arrive together carrying the same cookie. So one refresh token is exchanged
 * **once**, and every caller holding it shares that exchange.
 *
 * A renewed pair is also kept for {@link GRACE_MS} afterwards. A request that left the browser
 * before the new cookie landed still carries the old token; it is handed the same new pair
 * instead of a refusal.
 *
 * The flights are per process, and per bundle: the proxy and the server actions each keep their
 * own, because Next builds them separately. That is enough, since the proxy renews a token before
 * a render or an action reads it, and a second instance behind a load balancer is a deploy-time
 * question that does not exist yet.
 */

export type Refreshed =
  | { readonly kind: 'renewed'; readonly session: ClubSession }
  /** The backend will not rotate this token. The session is over. */
  | { readonly kind: 'refused' }
  /** No answer. The session may be fine; nothing is concluded from silence. */
  | { readonly kind: 'unreachable'; readonly error: ApiError };

const GRACE_MS = 20_000;

interface Flight {
  readonly promise: Promise<Refreshed>;
  renewedAt?: number;
}

const flights = new Map<string, Flight>();

async function exchange(refreshToken: string): Promise<Refreshed> {
  const outcome = await settle(() =>
    clubApi().POST('/api/v1/club/auth/refresh', { body: { refresh_token: refreshToken } }),
  );
  if (outcome.ok) return { kind: 'renewed', session: sessionFromPair(outcome.data) };
  const { status } = outcome.error;
  return status === 0 || status >= 500
    ? { kind: 'unreachable', error: outcome.error }
    : { kind: 'refused' };
}

export function refreshOnce(refreshToken: string, now: number = Date.now()): Promise<Refreshed> {
  for (const [token, flight] of flights) {
    if (flight.renewedAt !== undefined && now - flight.renewedAt > GRACE_MS) flights.delete(token);
  }

  const current = flights.get(refreshToken);
  if (current !== undefined) return current.promise;

  const flight: Flight = {
    promise: exchange(refreshToken).then((refreshed) => {
      if (refreshed.kind === 'renewed') flight.renewedAt = Date.now();
      else flights.delete(refreshToken);
      return refreshed;
    }),
  };
  flights.set(refreshToken, flight);
  return flight.promise;
}
