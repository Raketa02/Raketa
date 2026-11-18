/**
 * **New in Raketa** — the third of FOR YOU's five lines
 * ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5; was the NEW IN RAKETA row,
 * [#801](https://github.com/Raketa02/Raketa/issues/801), ADR-0204 §5; the Home rows screens §5.1; the
 * mechanics §7; home rows 1, 17, 17.2; home refactor 8, 9).
 *
 * Open, up to ten portrait tiles on the row frame's `tiles` rail, settling on their edges, in the
 * read's order — who the reader isn't connected with first, then who they asked, then friends — and
 * *See all N ›* to the grid at the foot. **Hidden** while the read holds nothing, is in flight, or
 * failed: a line that fails is left out, and the rest of Home stands (the screens §1).
 *
 * **Its count, on the line and in *See all N ›*, is how many joined in the last 30 days**
 * ([#822](https://github.com/Raketa02/Raketa/issues/822); ADR-0205 §6; the mechanics §7.5) — the
 * read's `total`, *99+* past 99 — and moves with the read.
 *
 * **A tile opens the record**, its requests sent from *new players* (`foundIn`). The line's reads list
 * people (`LISTS_PEOPLE`), so any friend write — from a tile, the record, or anywhere else in the app
 * — reaches it, the line holding still: the tile draws the answer where it stands, and the next read
 * moves it (the mechanics §13; `usePeopleRow`). A block reads the line again.
 */

import { router } from 'expo-router';
import { memo, useState } from 'react';

import { FoldingLineFooter, HomeRowRail, type FoldingLineParts } from '@/shared/ui';

import { FOUND_AMONG_NEW_PLAYERS, type Joiner } from '../domain/joiner';
import { useNewInRaketa } from '../hooks/useNewInRaketa';

import { DISCOVERY_COPY, seeAllWords } from './discoveryCopy';
import { NEW_IN_RAKETA_ROUTE } from './discoveryRoutes';
import { RowRecord, type RecordOpened } from './RowRecord';
import { JoinerTile } from './JoinerTile';

/**
 * **The New in Raketa line, as the shell draws it** — `undefined` while it is hidden. Read whether it
 * is open or not, so the read runs when Home opens.
 */
export function useNewInRaketaLine(): FoldingLineParts | undefined {
  const COPY = DISCOVERY_COPY.newInRaketa;
  const row = useNewInRaketa().data;
  if (row === undefined || row.people.length === 0) return undefined;
  return {
    title: COPY.line,
    count: row.total,
    testID: 'new-in-raketa',
    content: <NewInRaketa joiners={row.people} />,
    footer: (
      <FoldingLineFooter
        link={{
          words: seeAllWords(row.total),
          label: COPY.seeAllLabel,
          onPress: () => router.push(NEW_IN_RAKETA_ROUTE),
        }}
      />
    ),
  };
}

/** Memoised: the shell draws every line from one component, so a re-read of another line must not
 * draw this one's cards again. */
const NewInRaketa = memo(function NewInRaketa({
  joiners,
}: {
  readonly joiners: readonly Joiner[];
}) {
  const [reading, setReading] = useState<RecordOpened>();

  return (
    <>
      <HomeRowRail cards={joiners} geometry="tiles">
        {(joiner, width) => (
          <JoinerTile
            key={joiner.playerId}
            joiner={joiner}
            width={width}
            layout="row"
            onOpen={() =>
              setReading({ playerId: joiner.playerId, foundIn: FOUND_AMONG_NEW_PLAYERS })
            }
          />
        )}
      </HomeRowRail>
      <RowRecord opened={reading} onClose={() => setReading(undefined)} />
    </>
  );
});
