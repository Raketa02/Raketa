/**
 * **Players at your level** — the second of FOR YOU's five lines
 * ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5; was SAME COMPETITIVE LEVEL
 * PLAYERS, [#802](https://github.com/Raketa02/Raketa/issues/802), ADR-0204 §4; the Home rows screens
 * §4.1; the mechanics §6, §9; home rows 1, 7; home refactor 6, 7).
 *
 * Open, up to ten dark cards on the row frame's peeking rail, settling on their edges, in the read's
 * order — fresh good matches first, then the gaps — and *See all ›* to the full list at the foot.
 * **Hidden** while the read holds nobody (the reader holds no level anywhere, or nobody shares a
 * sport), is in flight, or failed: a line that fails is left out, and the rest of Home stands.
 *
 * **A face opens the record**, its requests sent from *same level* in the card's sport; *N sports ›*
 * opens the comparison sheet. The line's reads list people (`LISTS_PEOPLE`), so any friend write —
 * from a card, the sheet, the record, or anywhere else — reaches it, the line holding still: the card
 * draws the answer where it stands, and the next read moves it (§9.1, §13; `usePeopleRow`). A block
 * reads the line again.
 *
 * **Every card that comes at least half on screen is reported**, once that Warsaw day
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); §9.2) — **only while the line is open**: a
 * closed line draws no card, so it reports nobody. The reporter is the line's, so a report waiting to
 * be sent outlives a close. See all reports nothing.
 */

import { router } from 'expo-router';
import { memo, useState } from 'react';

import { FoldingLineFooter, HomeRowRail, type FoldingLineParts } from '@/shared/ui';

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

/**
 * **The Players at your level line, as the shell draws it** — `undefined` while it is hidden. Read
 * whether it is open or not, so the read runs when Home opens.
 */
export function useSameLevelLine(): FoldingLineParts | undefined {
  const COPY = DISCOVERY_COPY.sameLevel;
  const players = useSameLevel().data;
  const onScreen = useOnScreenReports('SAME_LEVEL');
  if (players === undefined || players.length === 0) return undefined;
  return {
    title: COPY.line,
    testID: 'same-level',
    content: <SameLevel players={players} onScreen={onScreen} />,
    footer: (
      <FoldingLineFooter
        link={{
          words: COPY.seeAll,
          label: COPY.seeAllLabel,
          onPress: () => router.push(SAME_LEVEL_ROUTE),
        }}
      />
    ),
  };
}

/** Memoised: the shell draws every line from one component, so a re-read of another line must not
 * draw this one's cards again. */
const SameLevel = memo(function SameLevel({
  players,
  onScreen,
}: {
  readonly players: readonly SameLevelPlayer[];
  readonly onScreen: (players: readonly SameLevelPlayer[]) => void;
}) {
  const you = useReaderFace();
  const comparing = usePersonSheet(players);
  const [reading, setReading] = useState<RecordOpened>();

  return (
    <>
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
    </>
  );
});
