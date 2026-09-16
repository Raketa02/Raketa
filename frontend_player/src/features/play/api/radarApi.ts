/**
 * The radar's wire: one reading.
 *
 * One of the two layers allowed to read generated types, and the only place this path is
 * written down.
 *
 * ## `POST /radar` records, and is read like the deal
 *
 * A reading is a **recorded search** — the fifth surface, `RADAR`, with a `search_id` and its
 * rows kept for ever so the record sheet opens from every card it drew and an answer can name
 * it as its origin ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §1). So it carries no `Idempotency-Key`, for the deal's reason: posting again is a new
 * reading with a new id. It is **not a deal** — it enters no dealt memory and notes no exposure
 * (§4) — so a second reading costs the pool nothing, which is what lets the client hold one
 * under a stale time rather than for ever (`hooks/useReading`).
 *
 * **No `signal`**, as on the deal: the reading records server-side before it answers, and a
 * cancelled request leaves a search minted and nobody holding its id.
 *
 * The response is the deal's own shape, `ShortlistResponse`, with two fields on every row that
 * no other surface carries — `bearing_deg` and `ratings[]` — and `pool.want_to_play_you`
 * computed by the deck's rule on the envelope (§5).
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type ReadRadarRequest = components['schemas']['ReadRadarRequest'];
type ShortlistResponse = components['schemas']['ShortlistResponse'];

/**
 * One reading: every player the radar may draw for the viewer in this sport.
 *
 * **An empty reading is a `200`** — nobody rated in this sport inside the reach is an answer,
 * and the pool it came from is described either way, which is what the empty footer prints.
 */
export function readRadar(body: ReadRadarRequest): Promise<ShortlistResponse> {
  return httpRequest<ShortlistResponse>({
    method: 'POST',
    path: '/api/v1/radar',
    body,
    authenticated: true,
  });
}
