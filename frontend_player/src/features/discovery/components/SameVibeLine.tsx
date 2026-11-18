/**
 * **Players with your vibe** — the fourth of FOR YOU's five lines
 * ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5; was SAME VIBE PLAYERS,
 * [#803](https://github.com/Raketa02/Raketa/issues/803), ADR-0204 §6; the Home rows screens §6.1; the
 * mechanics §8, §9; home rows 2, 20, 20.1; home refactor 10, 11).
 *
 * Open, up to ten pale tiles on the row frame's peeking rail, settling on their edges, in the read's
 * order — fresh good matches first, then the gaps — and *See all N ›* to the grid at the foot.
 * **Its count**, on the line and in *See all N ›*, is everybody sharing at least one tag with the
 * reader ([#822](https://github.com/Raketa02/Raketa/issues/822); ADR-0205 §6; the mechanics §8.8) —
 * the read's `total`, *99+* past 99, never the good matches — and moves with the read.
 * **Hidden** while the read holds nobody (the reader holds no tag, or nobody shares one), is in
 * flight, or failed: a line that fails is left out, and the rest of Home stands. Skill plays no part,
 * so a reader with no level sees it.
 *
 * **A tile opens the vibe sheet**; its round button acts, asking from *same vibe*. The line's reads
 * list people (`LISTS_PEOPLE`), so any friend write — from a tile, the sheet, the record its face
 * opens, or anywhere else — reaches it, the line holding still: the card draws the answer where it
 * stands, and the next read moves it (§9.1, §13; `usePeopleRow`). A block reads the line again.
 *
 * **Every tile that comes at least half on screen is reported**, once that Warsaw day
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); §9.2), its count this line's own — **only
 * while the line is open**: a closed line draws no tile. See all reports nothing.
 */

import { router } from 'expo-router';
import { memo } from 'react';

import { FoldingLineFooter, HomeRowRail, type FoldingLineParts } from '@/shared/ui';

import type { SameVibePlayer } from '../domain/sameVibe';
import { useOnScreenReports } from '../hooks/useOnScreenReports';
import { usePersonSheet } from '../hooks/usePersonSheet';
import { useSameVibe } from '../hooks/useSameVibe';

import { DISCOVERY_COPY, seeAllWords } from './discoveryCopy';
import { SAME_VIBE_ROUTE } from './discoveryRoutes';
import { SameVibeTile } from './SameVibeTile';
import { VibeSheet } from './VibeSheet';

/**
 * **The Players with your vibe line, as the shell draws it** — `undefined` while it is hidden. Read
 * whether it is open or not, so the read runs when Home opens.
 */
export function useSameVibeLine(): FoldingLineParts | undefined {
  const COPY = DISCOVERY_COPY.sameVibe;
  const row = useSameVibe().data;
  const onScreen = useOnScreenReports('SAME_VIBE');
  if (row === undefined || row.people.length === 0) return undefined;
  return {
    title: COPY.line,
    count: row.total,
    testID: 'same-vibe',
    content: <SameVibe players={row.people} onScreen={onScreen} />,
    footer: (
      <FoldingLineFooter
        link={{
          words: seeAllWords(row.total),
          label: COPY.seeAllLabel,
          onPress: () => router.push(SAME_VIBE_ROUTE),
        }}
      />
    ),
  };
}

/** Memoised: the shell draws every line from one component, so a re-read of another line must not
 * draw this one's cards again. */
const SameVibe = memo(function SameVibe({
  players,
  onScreen,
}: {
  readonly players: readonly SameVibePlayer[];
  readonly onScreen: (players: readonly SameVibePlayer[]) => void;
}) {
  const vibing = usePersonSheet(players);

  return (
    <>
      <HomeRowRail cards={players} onScreen={onScreen}>
        {(player, width) => (
          <SameVibeTile
            key={player.playerId}
            player={player}
            layout="row"
            width={width}
            onOpen={() => vibing.show(player)}
          />
        )}
      </HomeRowRail>
      <VibeSheet sheet={vibing} />
    </>
  );
});
