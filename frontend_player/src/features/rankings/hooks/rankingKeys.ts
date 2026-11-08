/**
 * **The Rankings query keys** ([#775](https://github.com/Raketa02/Raketa/issues/775)) — one root, so
 * whatever moves a ranking can mark every sport and view of it stale by prefix.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { RankingView } from '../domain/vocabulary';

export const rankingKeys = {
  all: () => ['rankings'] as const,
  ranking: (sport: Sport, view: RankingView) => ['rankings', sport, view] as const,
};
