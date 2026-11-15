/**
 * **SAME COMPETITIVE LEVEL PLAYERS** — the second of Home's five rows
 * ([#802](https://github.com/Raketa02/Raketa/issues/802); ADR-0204 §4; the Home rows screens §4.1;
 * the mechanics §6, §9; home rows 1, 7).
 *
 * Up to ten dark cards on Home's row frame (`HomeRow`, a peeking `HomeRowRail`), in the read's order —
 * fresh good matches first, then the gaps — with *See all ›* to the full list. **Hidden with its
 * heading** while the read holds nobody (the reader holds no level anywhere, or nobody shares a
 * sport), is in flight, or failed: a row that fails is left out, and the rest of Home stands.
 *
 * **A face opens the record**, its requests sent from *same level* in the card's sport; *N sports ›*
 * opens the comparison sheet. The row's reads list people (`LISTS_PEOPLE`), so any friend write —
 * from a card, the sheet, the record, or anywhere else — reaches it, the row holding still: the card
 * draws the answer where it stands, and the next read moves it (§9.1, §13; `usePeopleRow`). A block
 * reads the row again.
 *
 * **Every card that comes at least half on screen is reported**, once that Warsaw day
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); §9.2), so a card seen on five days without
 * an add gives its place to a fresh match. See all reports nothing.
 */

import { router } from 'expo-router';
import { useState } from 'react';

import { HomeRow, HomeRowRail } from '@/shared/ui';

import { foundAtSameLevel, type SameLevelPlayer } from '../domain/sameLevel';
import { useOnScreenReports } from '../hooks/useOnScreenReports';
import { usePersonSheet } from '../hooks/usePersonSheet';
import { useReaderFace } from '../hooks/useReaderFace';
import { useSameLevel } from '../hooks/useSameLevel';

import { DISCOVERY_COPY } from './discoveryCopy';
import { SAME_LEVEL_ROUTE } from './discoveryRoutes';
import { ComparingSheet } from './ComparingSheet';
import { RowRecord, type RecordOpened } from './RowRecord';
import { SameLevelCard } from './SameLevelCard';

export function SameLevelRow() {
  const players = useSameLevel().data;
  const onScreen = useOnScreenReports('SAME_LEVEL');
  if (players === undefined || players.length === 0) return null;
  return <SameLevel players={players} onScreen={onScreen} />;
}

function SameLevel({
  players,
  onScreen,
}: {
  readonly players: readonly SameLevelPlayer[];
  readonly onScreen: (players: readonly SameLevelPlayer[]) => void;
}) {
  const COPY = DISCOVERY_COPY.sameLevel;
  const you = useReaderFace();
  const comparing = usePersonSheet(players);
  const [reading, setReading] = useState<RecordOpened>();

  return (
    <HomeRow
      heading={COPY.heading}
      link={{
        words: COPY.seeAll,
        label: COPY.seeAllLabel,
        onPress: () => router.push(SAME_LEVEL_ROUTE),
      }}
      testID="same-level"
    >
      <HomeRowRail cards={players} onScreen={onScreen}>
        {(player, width) => (
          <SameLevelCard
            key={player.playerId}
            player={player}
            you={you}
            width={width}
            onOpen={() =>
              setReading({
                playerId: player.playerId,
                foundIn: foundAtSameLevel(player.shown.sport),
              })
            }
            onCompare={() => comparing.show(player)}
          />
        )}
      </HomeRowRail>
      <ComparingSheet comparing={comparing} />
      <RowRecord opened={reading} onClose={() => setReading(undefined)} />
    </HomeRow>
  );
}
