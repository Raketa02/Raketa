/**
 * **Read one page of General** ([#776](https://github.com/Raketa02/Raketa/issues/776); the screens
 * §5.3) — the list's own first page, which is the main read's, the page around the reader, or the
 * page below or above a cursor, folded into one shape. No rule of its own: the order, every place
 * and every cursor are the server's.
 *
 * **The first page is the main read** (`readRanking`), so the card and the podium come with it and
 * agree with its rows — one kept order's, read once.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getGeneralPage, type Cancellable, type GeneralPageQuery } from '../api/rankingsApi';
import type { GeneralPage, PageAt, Ranking } from '../domain/ranking';
import { toGeneralPage } from '../mappers/rankingMappers';

import { readRanking } from './readRanking';

/** A page of General, and — on the list's own first page — the main read it came with. */
export interface GeneralRead extends GeneralPage {
  readonly ranking?: Ranking;
}

export function readGeneralPage(
  sport: Sport,
  page: PageAt,
  { signal }: Cancellable = {},
): Promise<GeneralRead> {
  const cancellable = signal === undefined ? {} : { signal };
  if (page.at === 'top') {
    return readRanking(sport, 'GENERAL', cancellable).then((ranking) => ({
      rows: ranking.rows,
      ...(ranking.next === undefined ? {} : { next: ranking.next }),
      ranking,
    }));
  }
  return getGeneralPage(toWireSport(sport), queryOf(page), cancellable).then(toGeneralPage);
}

function queryOf(page: Exclude<PageAt, { at: 'top' }>): GeneralPageQuery {
  switch (page.at) {
    case 'aroundMe':
      return { aroundMe: true };
    case 'after':
      return { after: page.cursor };
    case 'before':
      return { before: page.cursor };
  }
}
