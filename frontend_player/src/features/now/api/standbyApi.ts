/**
 * The wire adapter for leaving standby. One path, one method, no body, no chip.
 *
 * `DELETE /api/v1/matches/{matchId}/standby` takes the viewer off a match's queue
 * and answers with the one card that changed — which for this act is *the card is
 * gone*, because a queue place is the whole of what put that match on her strip
 * (`ADR-0087`, `ADR-0091`).
 *
 * **No sport parameter, unlike the seat write beside it.** That one carries the
 * chip because its answer includes two whole regions, composed under whatever
 * filter she was holding. This one answers a **card** and nothing else, and a card
 * is a card whatever chip is held — so there is nothing here for a filter to
 * compose against, and sending one would invite a later reader to believe the
 * answer was scoped to it.
 *
 * **No idempotency key** (`ADR-0087`): a repeated delete of a place she no longer
 * holds is the state she asked for, and `ADR-0030`'s log is for destructive
 * commands. **Nothing here can refuse** — anybody may queue for any match, so
 * there is no membership to be a stranger to; the only 404 is a match id that
 * names nothing, which is about the address rather than about the act.
 *
 * Nothing here decides anything: which card was tapped belongs to the screen, when
 * to write belongs to the hook, and what the answer means belongs above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type StandbyWriteResponse = components['schemas']['StandbyWriteResponse'];

export interface LeaveStandbyOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

/** Leave this match's standby queue. Answers what Now should now hold. */
export function leaveStandby({
  matchId,
  signal,
}: LeaveStandbyOptions): Promise<StandbyWriteResponse> {
  return httpRequest<StandbyWriteResponse>({
    method: 'DELETE',
    path: `/api/v1/matches/${encodeURIComponent(matchId)}/standby`,
    authenticated: true,
    signal,
  });
}
