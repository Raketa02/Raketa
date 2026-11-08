/**
 * **Read one sport's ranking in one view** ([#775](https://github.com/Raketa02/Raketa/issues/775)) —
 * the route, folded into the page's shapes. No rule of its own: every place, chip and gap is the
 * server's (the rankings mechanics §7.2), so this is the uniform-strict pass-through.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { getRanking, type Cancellable } from '../api/rankingsApi';
import type { Ranking } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';
import { toRanking } from '../mappers/rankingMappers';

export function readRanking(
  sport: Sport,
  view: RankingView,
  { signal }: Cancellable = {},
): Promise<Ranking> {
  return getRanking(toWireSport(sport), view, signal === undefined ? {} : { signal }).then(
    toRanking,
  );
}
