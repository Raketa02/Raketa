/**
 * **The Rankings routes this build reads** ([#775](https://github.com/Raketa02/Raketa/issues/775),
 * [#776](https://github.com/Raketa02/Raketa/issues/776)), through the one HTTP chokepoint.
 *
 * | Function | Route |
 * | --- | --- |
 * | `getRanking` | `GET /rankings/{sport}?view=GENERAL\|FRIENDS` — the reader's card, the podium, and General's first page of 50 or the whole of Friends |
 * | `getGeneralPage` | `GET /rankings/{sport}/general/rows?after=\|before=\|around_me=true` — a page of General: below a cursor, above one, or with the reader in the middle |
 * | `getTopTen` | `GET /top-10?sport=\|prefer=` — Home's Top 10 ([#805](https://github.com/Raketa02/Raketa/issues/805)): General's first ten in a sport named exactly, or in a preferred one the server falls through from |
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

/** **Which page of General** — one of the three, as the route takes them: never two at once. */
export type GeneralPageQuery =
  { readonly after: string } | { readonly before: string } | { readonly aroundMe: true };

export function getGeneralPage(
  sport: Schemas['Sport'],
  page: GeneralPageQuery,
  { signal }: Cancellable = {},
): Promise<Schemas['GeneralPageResponse']> {
  const query =
    'after' in page
      ? `after=${encodeURIComponent(page.after)}`
      : 'before' in page
        ? `before=${encodeURIComponent(page.before)}`
        : 'around_me=true';
  return httpRequest<Schemas['GeneralPageResponse']>({
    method: 'GET',
    path: `/api/v1/rankings/${sport}/general/rows?${query}`,
    authenticated: true,
    signal,
  });
}

/**
 * **Which sport Top 10 is read in** — named exactly (the pill's pick), or preferred (the opening
 * sport), never both: the route refuses either with `not_one_sport`.
 */
export type TopTenQuery =
  { readonly sport: Schemas['Sport'] } | { readonly prefer: Schemas['Sport'] };

export function getTopTen(
  query: TopTenQuery,
  { signal }: Cancellable = {},
): Promise<Schemas['TopTenResponse']> {
  const asked = 'sport' in query ? `sport=${query.sport}` : `prefer=${query.prefer}`;
  return httpRequest<Schemas['TopTenResponse']>({
    method: 'GET',
    path: `/api/v1/top-10?${asked}`,
    authenticated: true,
    signal,
  });
}
