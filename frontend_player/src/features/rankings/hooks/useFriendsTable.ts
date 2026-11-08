/**
 * **Friends, as the page reads it** ([#777](https://github.com/Raketa02/Raketa/issues/777); the
 * rankings screens §4.6, §5.3) — the reader and their friends, **one read, the whole table**:
 * `GET /rankings/{sport}?view=FRIENDS`. The server works it out on every read and keeps it nowhere
 * (the mechanics §4.2), and never pages it.
 *
 * It hands the page the shape General's pages do (`RankingRead`), so the card, the podium, the list
 * and the *You · 4th* button are drawn once for both. **Its ends ask for nothing**, it has no page to
 * refuse, and its button only ever scrolls — the reader's row is always on hand.
 *
 * **The app's defaults, chosen** (architecture Part 7), as General's: a friend's result settling
 * moves a place, so the moderate class's 30 seconds is fresh enough while the view is up, and
 * foregrounding reads it again. **Opening the view always reads it** (the screens §3: *switching view
 * re-reads the page*), so a friend added or removed anywhere is in the table the next time it opens.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { jumpPlace, type Ranking } from '../domain/ranking';
import { readRanking } from '../use-cases/readRanking';

import { rankingKeys } from './rankingKeys';
import type { RankingRead } from './rankingRead';

/** An end of a table read whole — there is nothing past it to ask for. */
const NOTHING_TO_ASK = () => {};

export function useFriendsTable(sport: Sport): RankingRead {
  const read = useQuery<Ranking, AppError>({
    queryKey: rankingKeys.friends(sport),
    queryFn: ({ signal }) => readRanking(sport, 'FRIENDS', { signal }),
    refetchOnMount: 'always',
  });

  const ranking = read.data;
  const place = jumpPlace(ranking?.card);

  return {
    ranking,
    error: ranking === undefined ? read.error : null,
    paused: read.fetchStatus === 'paused',
    window: 'fromTheTop',
    rows: ranking?.rows ?? [],
    atTheTop: true,
    loadEarlier: NOTHING_TO_ASK,
    loadLater: NOTHING_TO_ASK,
    earlierFailure: undefined,
    laterFailure: undefined,
    jump: place === undefined ? undefined : { place, failure: undefined },
    reread: () => read.refetch(),
    retry: () => void read.refetch(),
  };
}
