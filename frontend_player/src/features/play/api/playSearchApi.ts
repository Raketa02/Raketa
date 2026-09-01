/**
 * The wire adapter for a search, a line-up and a forecast — **and the line between the two
 * that record and the one that does not.**
 *
 * One of the two layers allowed to read generated types, and the only place these paths are
 * written down.
 *
 * `POST /searches` and `POST /lineups` each **mint a search** and record it; `POST /forecasts`
 * deliberately does neither. That is the whole reason it exists as a route
 * ([ADR-0108](../../../../../docs/adr/0108-a-forecast-is-a-route-not-a-search.md)):
 * *"re-posting `/lineups` per swap would enter a six-edit builder session into* searches run
 * *as six searches, which is a lie in the one table the product uses to judge itself."* So the
 * three sit together, and the two rules below apply to the first two and not to the third.
 *
 * **`POST /searches` is deliberately not idempotent** — *"two taps are two searches"* — and it
 * carries **no `Idempotency-Key`** for that reason: a key would be a claim the route makes the
 * opposite of. What protects a player from a double tap is the control being busy, and what
 * protects them from a retry storm is that nothing in Play retries without them asking.
 *
 * **No `signal`.** A search *records* server-side before it answers, so a cancelled request
 * leaves a search minted and nobody holding its id — which is the exact state
 * `search_not_found` describes and the one this screen must not manufacture. It is the same
 * reason the profile commit takes none, and the same reason `TIMEOUT_MS.request` stays at 15 s
 * against a specification that asked for eight: giving up early on a recording write does not
 * bound a wait, it manufactures telemetry (`domain/retryTarget`).
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type RunSearchRequest = components['schemas']['RunSearchRequest'];
type ShortlistResponse = components['schemas']['ShortlistResponse'];
type RunLineupRequest = components['schemas']['RunLineupRequest'];
type LineupResponse = components['schemas']['LineupResponse'];
type ForecastRequest = components['schemas']['ForecastRequest'];
type ForecastResponse = components['schemas']['ForecastResponse'];

/**
 * Find me a game: at most twenty ranked people, unpaginated, and the envelope over them.
 *
 * The breakdown ships with the search rather than behind a tap, so nothing here asks for one.
 */
export function runSearch(body: RunSearchRequest): Promise<ShortlistResponse> {
  return httpRequest<ShortlistResponse>({
    method: 'POST',
    path: '/api/v1/searches',
    body,
    authenticated: true,
  });
}

/**
 * ⚡ *Fill the seats* — **the line-up and fill-seats are one request**, and one recorded search.
 *
 * It mints a `search_id` of its own, so the answer is written into `searchKeys.detail(id)`
 * exactly as a shortlist's is and the line-up it seats is bound to **that** id. Not idempotent
 * and carrying no key, for `POST /searches`' reason: two taps are two line-ups, and what
 * protects a player from a double tap is the control being busy.
 *
 * **A seat may come back unfilled and this is still a `200`** — the empty seat says why, and
 * *three of four* is an honest answer.
 */
export function runLineup(body: RunLineupRequest): Promise<LineupResponse> {
  return httpRequest<LineupResponse>({
    method: 'POST',
    path: '/api/v1/lineups',
    body,
    authenticated: true,
  });
}

/**
 * What a four you composed would leave on court — **the one `POST` in Play that records
 * nothing.**
 *
 * Which is why this one takes a `signal` where the three recording writes take none: a
 * cancelled forecast leaves no trace and costs nobody a row, so Part 7's *"pass Query's
 * `signal` through to `fetch`"* applies to it unreservedly — the same asymmetry `deckApi`
 * draws between its read and its writes, arriving here on a `POST` because what decides it is
 * whether the route records, not which verb it wears.
 *
 * It is read as a **query** rather than run as a mutation for the same reason: nothing is
 * mutated, the answer is a pure function of `(search_id, the set of players)`, and holding it
 * under that key is what makes a swap a selection out of a response already held rather than
 * a round trip (`hooks/searchKeys.ts`).
 */
export function requestForecast(
  body: ForecastRequest,
  { signal }: ForecastOptions = {},
): Promise<ForecastResponse> {
  return httpRequest<ForecastResponse>({
    method: 'POST',
    path: '/api/v1/forecasts',
    body,
    authenticated: true,
    signal,
  });
}

export interface ForecastOptions {
  readonly signal?: AbortSignal;
}
