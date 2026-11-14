/**
 * **New in Raketa's See all** — pushed over Home, whose tab stays lit
 * ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows screens §5.3; the mechanics
 * §7.4; home rows 19, 19.2).
 *
 * - **Header**: ‹, *New in Raketa*, and the sport pill — *● All ‹* — which slides open over the title
 *   onto the sports at least one Joiner holds a level in, the chosen one last (`shared/ui`'s
 *   `SportPillFrame`, offering *All*).
 * - **Body**: the tiles in two columns, newest first, friends where they fall, **20 to a page, the next
 *   read as the grid nears its end**. A sport keeps only who holds a level in it, and one that leaves
 *   nobody says *Nobody new plays squash yet* in place of the grid.
 * - **Every state**: reading (a spinner where the grid will be), failed (the recovery sentence and *Try
 *   again*), offline (resumes), a later page refused (said under the grid, with its own *Try again*),
 *   and the pull, which reads every page again.
 *
 * A tile opens the record and its round button acts, as on Home's row; **every friend write re-reads
 * every people list** (`LISTS_PEOPLE`), so this grid and the row under the screen both move. The
 * frame, the paging and every state are every people row's (`SeeAllScreen`).
 */

import { useState } from 'react';
import { useWindowDimensions } from 'react-native';

import { theme } from '@/shared/ui';

import { FOUND_AMONG_NEW_PLAYERS, type Joiner } from '../domain/joiner';
import type { SeeAllSport } from '../domain/seeAll';
import { useNewInRaketaPage } from '../hooks/useNewInRaketa';

import { DISCOVERY_COPY, NEW_IN_RAKETA_PILL_WORDS, nobodyNewPlays } from './discoveryCopy';
import { JoinerTile } from './JoinerTile';
import { RowRecord, type RecordOpened } from './RowRecord';
import { SeeAllScreen } from './SeeAllScreen';

/** See all's two columns (home rows 19). */
const COLUMNS = 2;

export function NewInRaketaScreen() {
  const COPY = DISCOVERY_COPY.newInRaketa;
  const [choice, setChoice] = useState<SeeAllSport>('all');
  const [reading, setReading] = useState<RecordOpened>();
  const grid = useNewInRaketaPage(choice);
  const { width: screen } = useWindowDimensions();
  const tile = (screen - 2 * theme.size.gutter - theme.space.sm * (COLUMNS - 1)) / COLUMNS;

  return (
    <SeeAllScreen<Joiner>
      title={COPY.title}
      backLabel={COPY.back}
      pillWords={NEW_IN_RAKETA_PILL_WORDS}
      choice={choice}
      onPick={setChoice}
      list={grid}
      columns={COLUMNS}
      renderPerson={(joiner) => (
        <JoinerTile
          joiner={joiner}
          width={tile}
          layout="grid"
          onOpen={() => setReading({ playerId: joiner.playerId, foundIn: FOUND_AMONG_NEW_PLAYERS })}
        />
      )}
      emptyLine={choice === 'all' ? COPY.nobodyAtAll : nobodyNewPlays(choice)}
      readingLabel={COPY.reading}
      testID="new-in-raketa-grid"
      overlayUp={reading !== undefined}
      overlays={<RowRecord opened={reading} onClose={() => setReading(undefined)} />}
    />
  );
}
