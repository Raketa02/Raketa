/**
 * **Where Rankings is** ([#775](https://github.com/Raketa02/Raketa/issues/775)) — `/rankings`, pushed
 * over Home (the shell lists it inside Home's tab, so the Home column stays lit), on the sport it is
 * asked for: the trophy's, or the one a pass returns to. No sport opens it on the deck's last, or
 * padel (the rankings mechanics §9).
 */

import type { Sport } from '@/shared/vocabulary/sport';

export const RANKINGS_PATH = '/rankings';

export function rankingsRoute(sport?: Sport) {
  return sport === undefined
    ? ({ pathname: RANKINGS_PATH } as const)
    : ({ pathname: RANKINGS_PATH, params: { sport } } as const);
}
