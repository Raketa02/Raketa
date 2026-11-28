/**
 * **How far a group tab's first read has come** ([#875](https://github.com/Rakieta02/Rakieta/issues/875);
 * PRD #867; the loading shimmer log §10) — for the three tabs this feature draws on a group's page:
 * what the page's reveal waits on for the body on screen.
 *
 * | Tab | Waits for |
 * | --- | --- |
 * | **Games** | the deck the tab draws — the kind chosen, or the one the intent corrects it to (`useGroupDeck`) |
 * | **Fill in** | its rescues, for the page's sport |
 * | **You’re in** | the reader's live yeses — and, with none here, Fill in's too (`youreInRead`) |
 *
 * Each answer is `shared/lib/query-client`'s `readStage` — `reading`, `landed`, or `ended` with
 * nothing to show — read off the cache under the hooks' own keys, so asking costs no request and the
 * page draws again only as the answer turns. No sport yet, or no tab of this feature's: nothing to say
 * but that it is still to come, or nothing to wait for.
 */

import type { QueryClient } from '@tanstack/react-query';

import { readStage, useQueryCacheAnswer, type ReadStage } from '@/shared/lib/query-client';
import type { Sport } from '@/shared/vocabulary/sport';

import { resolveKind, type GroupDeck } from '../domain/deck';
import { yesesIn, youreInRead } from '../domain/fillIn';
import type { LiveYeses } from '../domain/liveYes';
import type { GameKind } from '../domain/vocabulary';

import { proposalKeys } from './proposalKeys';

/** The group tabs this feature draws. */
export type GroupGamesTab = 'games' | 'fillIn' | 'youreIn';

/**
 * `tab` is the one on screen, `undefined` for a tab that is not this feature's (Friends), which waits
 * on nothing here. `chosen` is the kind the Games tab's menu stands on.
 */
export function useGroupTabRead(
  groupId: string,
  sport: Sport | undefined,
  tab: GroupGamesTab | undefined,
  chosen: GameKind,
): ReadStage {
  return useQueryCacheAnswer((client) => {
    if (tab === undefined) return 'landed';
    if (sport === undefined) return 'reading';
    const rescues = () => readStage(client.getQueryState(proposalKeys.fillIn(groupId, sport)));
    switch (tab) {
      case 'games':
        return deckRead(client, groupId, sport, chosen);
      case 'fillIn':
        return rescues();
      case 'youreIn': {
        const yeses = client.getQueryState<LiveYeses>(proposalKeys.liveYeses());
        const here =
          yeses?.data === undefined ? undefined : yesesIn(yeses.data.yeses, groupId, sport).length;
        return youreInRead(readStage(yeses), here, rescues());
      }
    }
  });
}

/** The deck the Games tab draws — the kind chosen, or the one the intent shows instead. */
function deckRead(client: QueryClient, groupId: string, sport: Sport, chosen: GameKind): ReadStage {
  const asked = client.getQueryState<GroupDeck>(proposalKeys.deck(groupId, sport, chosen));
  const kind = resolveKind(chosen, asked?.data?.segments);
  return readStage(
    kind === chosen ? asked : client.getQueryState(proposalKeys.deck(groupId, sport, kind)),
  );
}
