/**
 * The wire adapter for Now. One request, one route, one query parameter.
 *
 * `ADR-0070`: *"the request carries the selected sport and nothing else."* In
 * particular it carries **no stamp of what the phone is holding**, and the server
 * never answers *nothing has changed* — Now is asked for only on the four
 * occasions `ADR-0054` names, every one of them a moment the player explicitly
 * asked, and pull-to-refresh carries a promise a saved payload would break.
 *
 * Nothing here decides anything: which sport is selected belongs to the store,
 * when to ask belongs to the hooks, and what the answer means belongs above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type NowResponse = components['schemas']['NowResponse'];
type SportFilter = components['schemas']['SportFilter'];

export interface ComposeNowOptions {
  readonly sport: SportFilter;
  readonly signal?: AbortSignal;
}

/** The whole screen, composed for this viewer and this sport. */
export function composeNow({ sport, signal }: ComposeNowOptions): Promise<NowResponse> {
  return httpRequest<NowResponse>({
    method: 'GET',
    path: `/api/v1/now?sport=${encodeURIComponent(sport)}`,
    authenticated: true,
    signal,
  });
}
