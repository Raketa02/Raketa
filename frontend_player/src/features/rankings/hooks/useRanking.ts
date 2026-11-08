/**
 * **One sport's ranking, as the page reads it** ([#775](https://github.com/Raketa02/Raketa/issues/775)).
 *
 * The app's defaults: a place moves when a result settles anywhere in Raketa, and the server keeps a
 * sport's General order for at most a minute (the rankings mechanics §15), so the read is made
 * current by opening the page and by foregrounding, like every list of the server's. Switching sport
 * is a new key, and so a new read.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Ranking } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';
import { readRanking } from '../use-cases/readRanking';

import { rankingKeys } from './rankingKeys';

export function useRanking(sport: Sport, view: RankingView) {
  return useQuery<Ranking, AppError>({
    queryKey: rankingKeys.ranking(sport, view),
    queryFn: ({ signal }) => readRanking(sport, view, { signal }),
  });
}
