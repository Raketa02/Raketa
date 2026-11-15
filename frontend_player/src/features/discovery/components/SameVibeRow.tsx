/**
 * **SAME VIBE PLAYERS** — the fourth of Home's five rows
 * ([#803](https://github.com/Raketa02/Raketa/issues/803); ADR-0204 §6; the Home rows screens §6.1;
 * the mechanics §8, §9; home rows 2, 20, 20.1).
 *
 * Up to ten pale tiles on Home's row frame (`HomeRow`, a peeking `HomeRowRail`), in the read's order —
 * fresh good matches first, then the gaps — with *See all ›* to the grid. **Hidden with its heading**
 * while the read holds nobody (the reader holds no tag, or nobody shares one), is in flight, or failed:
 * a row that fails is left out, and the rest of Home stands. Skill plays no part, so a reader with no
 * level sees it.
 *
 * **A tile opens the vibe sheet**; its round button acts, asking from *same vibe*. The row's reads
 * list people (`LISTS_PEOPLE`), so any friend write — from a tile, the sheet, the record its face
 * opens, or anywhere else — reaches it, the row holding still: the card draws the answer where it
 * stands, and the next read moves it (§9.1, §13; `usePeopleRow`). A block reads the row again.
 *
 * **Every tile that comes at least half on screen is reported**, once that Warsaw day
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); §9.2), its count this row's own. See all
 * reports nothing.
 */

import { router } from 'expo-router';

import { HomeRow, HomeRowRail } from '@/shared/ui';

import type { SameVibePlayer } from '../domain/sameVibe';
import { useOnScreenReports } from '../hooks/useOnScreenReports';
import { usePersonSheet } from '../hooks/usePersonSheet';
import { useSameVibe } from '../hooks/useSameVibe';

import { DISCOVERY_COPY } from './discoveryCopy';
import { SAME_VIBE_ROUTE } from './discoveryRoutes';
import { SameVibeTile } from './SameVibeTile';
import { VibeSheet } from './VibeSheet';

export function SameVibeRow() {
  const players = useSameVibe().data;
  const onScreen = useOnScreenReports('SAME_VIBE');
  if (players === undefined || players.length === 0) return null;
  return <SameVibe players={players} onScreen={onScreen} />;
}

function SameVibe({
  players,
  onScreen,
}: {
  readonly players: readonly SameVibePlayer[];
  readonly onScreen: (players: readonly SameVibePlayer[]) => void;
}) {
  const COPY = DISCOVERY_COPY.sameVibe;
  const vibing = usePersonSheet(players);

  return (
    <HomeRow
      heading={COPY.heading}
      link={{
        words: COPY.seeAll,
        label: COPY.seeAllLabel,
        onPress: () => router.push(SAME_VIBE_ROUTE),
      }}
      testID="same-vibe"
    >
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
    </HomeRow>
  );
}
