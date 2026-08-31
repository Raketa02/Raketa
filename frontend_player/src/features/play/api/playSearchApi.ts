/**
 * The wire adapter for a search. One of the two layers allowed to read generated types, and
 * the only place these paths are written down.
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
