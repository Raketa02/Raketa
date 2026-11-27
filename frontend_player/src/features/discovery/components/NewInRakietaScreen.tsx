/**
 * **New in Rakieta's See all** — pushed over Home, whose tab stays lit
 * ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows screens §5.3; the mechanics
 * §7.4; home rows 19, 19.2).
 *
 * - **Header**: ‹, *New in Rakieta*, and the sport pill — *● All ‹* — which slides open over the title
 *   onto the sports at least one Joiner holds a level in, the chosen one last (`shared/ui`'s
 *   `SportPillFrame`, offering *All*).
 * - **Body**: the tiles in two columns, newest first, friends where they fall, **20 to a page, the next
 *   read as the grid nears its end**. A sport keeps only who holds a level in it, and one that leaves
 *   nobody says *Nobody new plays squash yet* in place of the grid.
 * - **Every state**: reading (the grid's tiles as skeleton blocks, filling the screen — #872), failed
 *   (the recovery sentence and *Try again*), offline (resumes), a later page refused (said under the
 *   grid, with its own *Try again*), and the pull, which reads every page again.
 *
 * A tile opens the record and its round button acts, as on Home's row; **every friend write reaches
 * every people list** (`LISTS_PEOPLE`): this grid reads again, and the row under the screen draws the
 * answer, holding still until Home is back (`usePeopleRow`). The frame, the paging and every state are
 * every people row's (`SeeAllScreen`).
 */

import { useState } from 'react';

import { FOUND_AMONG_NEW_PLAYERS, type Joiner } from '../domain/joiner';
import type { SeeAllSport } from '../domain/seeAll';
import { useNewInRakietaPage } from '../hooks/useNewInRakieta';

import { DISCOVERY_COPY, NEW_IN_RAKIETA_PILL_WORDS, nobodyNewPlays } from './discoveryCopy';
import { JOINER_TILE_SKELETON, JoinerTile } from './JoinerTile';
import { RowRecord, type RecordOpened } from './RowRecord';
import { SeeAllScreen } from './SeeAllScreen';

/** See all's two columns (home rows 19). */
const COLUMNS = 2;

export function NewInRakietaScreen() {
  const COPY = DISCOVERY_COPY.newInRakieta;
  const [choice, setChoice] = useState<SeeAllSport>('all');
  const [reading, setReading] = useState<RecordOpened>();
  const grid = useNewInRakietaPage(choice);

  return (
    <SeeAllScreen<Joiner>
      title={COPY.title}
      backLabel={COPY.back}
      pillWords={NEW_IN_RAKIETA_PILL_WORDS}
      choice={choice}
      onPick={setChoice}
      list={grid}
      columns={COLUMNS}
      renderPerson={(joiner, width) => (
        <JoinerTile
          joiner={joiner}
          width={width}
          layout="grid"
          onOpen={() => setReading({ playerId: joiner.playerId, foundIn: FOUND_AMONG_NEW_PLAYERS })}
        />
      )}
      skeleton={JOINER_TILE_SKELETON}
      emptyLine={choice === 'all' ? COPY.nobodyAtAll : nobodyNewPlays(choice)}
      testID="new-in-rakieta-grid"
      overlayUp={reading !== undefined}
      overlays={<RowRecord opened={reading} onClose={() => setReading(undefined)} />}
    />
  );
}
