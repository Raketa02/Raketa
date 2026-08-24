/**
 * The wire adapter for taking a seat. One path, one method, no body.
 *
 * `POST /api/v1/matches/{matchId}/seat` opens `ADR-0081`'s five minutes in front
 * of a free seat and answers with the screen it changed. **Which seat is the
 * match's answer and not the caller's**, and a price is not something the caller
 * quotes — so there is nothing to send. The sport chip rides as a query parameter
 * exactly as it does on `GET /api/v1/now`, because it is a fact about the
 * **screen**: the two regions that come back are recomposed under it, and a region
 * composed under a different filter would replace her filtered screen with
 * somebody else's.
 *
 * **No idempotency key** (`ADR-0030` is for destructive commands). A second tap by
 * the player who already holds the claim is refused by her own claim, and *did my
 * first tap land* is answered by the card that comes back carrying it.
 *
 * **The path says `matches` and there is no `GET /matches/{id}` beside it.** The
 * backend refused a general match resource on purpose, so nothing here may grow
 * one.
 *
 * Nothing here decides anything: which card was tapped belongs to the screen, when
 * to write belongs to the hook, and what the answer means belongs above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type SeatWriteResponse = components['schemas']['SeatWriteResponse'];
type SportFilter = components['schemas']['SportFilter'];

export interface TakeSeatOptions {
  readonly matchId: string;
  /** The chip on the sport bar when she tapped, which the two regions come back under. */
  readonly sport: SportFilter;
  readonly signal?: AbortSignal;
}

/** Take the seat an offer named. Answers what the tap did, and her two regions. */
export function takeSeat({ matchId, sport, signal }: TakeSeatOptions): Promise<SeatWriteResponse> {
  return httpRequest<SeatWriteResponse>({
    method: 'POST',
    path: `/api/v1/matches/${encodeURIComponent(matchId)}/seat?sport=${encodeURIComponent(sport)}`,
    authenticated: true,
    signal,
  });
}
