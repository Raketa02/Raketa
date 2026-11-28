/**
 * **The Rankings query keys** ([#775](https://github.com/Rakieta02/Rakieta/issues/775),
 * [#776](https://github.com/Rakieta02/Rakieta/issues/776), [#777](https://github.com/Rakieta02/Rakieta/issues/777)) — one root, so whatever moves a ranking can
 * mark every sport and view of it stale by prefix.
 *
 * General is two infinite queries under one prefix, the cursors in their pages: the list from the
 * top — the main read, then each page below it — and the list around the reader, after a jump.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { TopTenAsk } from '../domain/topTen';

export const rankingKeys = {
  all: () => ['rankings'] as const,
  general: (sport: Sport) => ['rankings', sport, 'GENERAL'] as const,
  generalFromTheTop: (sport: Sport) => [...rankingKeys.general(sport), 'fromTheTop'] as const,
  generalAroundMe: (sport: Sport) => [...rankingKeys.general(sport), 'aroundMe'] as const,
  /** Friends (#777): one read, the whole table — no pages. */
  friends: (sport: Sport) => ['rankings', sport, 'FRIENDS'] as const,
  /** Home's Top 10 (#805): every read of the row — Home's pull re-reads them all. */
  topTen: () => ['rankings', 'top-10'] as const,
  /** One read of the row: a sport picked exactly, or the opening one preferred. */
  topTenAsked: (ask: TopTenAsk) => [...rankingKeys.topTen(), ask.kind, ask.sport] as const,
  /** No read yet — the opening sport is still being worked out (`skipToken`, never a sport's key). */
  topTenUnasked: () => [...rankingKeys.topTen(), 'unasked'] as const,
};
