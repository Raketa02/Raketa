/**
 * **The Rankings routes this build reads** ([#775](https://github.com/Raketa02/Raketa/issues/775)),
 * through the one HTTP chokepoint.
 *
 * | Function | Route |
 * | --- | --- |
 * | `getRanking` | `GET /rankings/{sport}?view=GENERAL\|FRIENDS` — the reader's card, the podium, and General's first page of 50 or the whole of Friends |
 *
 * General's later pages (`GET /rankings/{sport}/general/rows`) are #776's.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

export interface Cancellable {
  readonly signal?: AbortSignal;
}

export function getRanking(
  sport: Schemas['Sport'],
  view: Schemas['RankingView'],
  { signal }: Cancellable = {},
): Promise<Schemas['RankingResponse']> {
  return httpRequest<Schemas['RankingResponse']>({
    method: 'GET',
    path: `/api/v1/rankings/${sport}?view=${view}`,
    authenticated: true,
    signal,
  });
}
