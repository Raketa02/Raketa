/**
 * **Same vibe's See all** — pushed over Home, whose tab stays lit
 * ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows screens §6.4; the mechanics
 * §8.6; home rows 24).
 *
 * - **Header**: ‹, *Same vibe players*, and the sport pill — *● All ‹* — which slides open over the
 *   title onto the sports at least one listed player holds a level in, the chosen one last
 *   (`shared/ui`'s `SportPillFrame`, offering *All*).
 * - **Body**: the same tiles in two columns, most in common first, friends where they fall, **20 to a
 *   page, the next read as the grid nears its end**. A sport keeps only who holds a level in it, and
 *   one that leaves nobody says so in place of the grid.
 * - **Every state** is the people rows' See all's (`SeeAllScreen`): reading, failed, offline, a later
 *   page refused, and the pull.
 *
 * Every tile opens the same vibe sheet and its round button acts, as on Home's row; **every friend
 * write re-reads every people list** (`LISTS_PEOPLE`), so this grid and the row under the screen both
 * move.
 */

import { useState } from 'react';

import type { SameVibePlayer } from '../domain/sameVibe';
import type { SeeAllSport } from '../domain/seeAll';
import { usePersonSheet } from '../hooks/usePersonSheet';
import { useSameVibePage } from '../hooks/useSameVibe';

import { DISCOVERY_COPY, SAME_VIBE_PILL_WORDS, nobodySharesYourTagsIn } from './discoveryCopy';
import { SameVibeTile } from './SameVibeTile';
import { SeeAllScreen } from './SeeAllScreen';
import { VibeSheet } from './VibeSheet';

/** See all's two columns (home rows 24). */
const COLUMNS = 2;

export function SameVibeScreen() {
  const COPY = DISCOVERY_COPY.sameVibe;
  const [choice, setChoice] = useState<SeeAllSport>('all');
  const grid = useSameVibePage(choice);
  const vibing = usePersonSheet(grid.people ?? []);

  return (
    <SeeAllScreen<SameVibePlayer>
      title={COPY.title}
      backLabel={COPY.back}
      pillWords={SAME_VIBE_PILL_WORDS}
      choice={choice}
      onPick={setChoice}
      list={grid}
      columns={COLUMNS}
      renderPerson={(player, width) => (
        <SameVibeTile
          player={player}
          layout="grid"
          width={width}
          onOpen={() => vibing.show(player)}
        />
      )}
      emptyLine={choice === 'all' ? COPY.nobodyAtAll : nobodySharesYourTagsIn(choice)}
      readingLabel={COPY.reading}
      testID="same-vibe-grid"
      overlayUp={vibing.open}
      overlays={<VibeSheet sheet={vibing} />}
    />
  );
}
