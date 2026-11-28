/**
 * **The cards each kind deals the player now in one sport, across their groups** — read when You ›
 * *What kind of game* opens a declared sport's row, so its answers can say what a change costs
 * (ADR-0201 §6, [#742](https://github.com/Rakieta02/Rakieta/issues/742)).
 *
 * `sport` is `domain/intentChangeCost`'s `sportToCount`: the open row's while it is declared, and
 * `undefined` otherwise, when nothing is read.
 *
 * **A count lives as long as the opening that read it** (`staleTime: 0`, `gcTime: 0`). It is of
 * cards dealt *now*, and between two openings the jobs deal, the deck is answered and the group
 * page's door changes the intent, none of which this screen sees. So closing the row drops the
 * count, and the next opening reads again and says no number until its own read lands — never the
 * last opening's, and never one from before a change of intent made on either surface. A failed
 * read leaves no older number behind it either.
 *
 * **No sport is `skipToken` under a key of its own**, not `enabled: false` under a real sport's: a
 * disabled observer on a borrowed key would keep that sport's count alive between its openings,
 * which is the one thing `gcTime: 0` is here to stop.
 */

import { skipToken, useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCounts } from '../domain/intentChangeCost';
import { readDeckCounts } from '../use-cases/readDeckCounts';

import { playerProfileKeys } from './playerProfileKeys';

export function useDeckCounts(sport: Sport | undefined) {
  return useQuery<DeckCounts, AppError>({
    queryKey:
      sport === undefined
        ? playerProfileKeys.deckCountsNone()
        : playerProfileKeys.deckCounts(sport),
    queryFn: sport === undefined ? skipToken : ({ signal }) => readDeckCounts(sport, { signal }),
    staleTime: 0,
    gcTime: 0,
  });
}
