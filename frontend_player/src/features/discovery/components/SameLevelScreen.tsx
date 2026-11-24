/**
 * **Same competitive level's See all** — pushed over Home, whose tab stays lit
 * ([#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows screens §4.4; the mechanics
 * §6.7; home rows 12–16).
 *
 * - **Header**: ‹, *Same competitive level players* bold — two lines where it wraps — and the sport
 *   pill, *● All ‹*, which slides open over the title onto the sports the reader shares with somebody,
 *   the chosen one last (`shared/ui`'s `SportPillFrame`, offering *All*).
 * - **Body**: one full-width dark card per player, best % first, friends where they fall, **20 to a
 *   page, the next read as the list nears its end**. On *All* each is in their evenest shared sport;
 *   **a sport re-compares everybody in it** — the server's read with the sport — and keeps only them.
 *   Every card keeps its *N sports ›*.
 * - **Every state**: reading (full-width skeleton cards filling the screen — #872), failed (the
 *   recovery sentence and *Try again*), offline
 *   (resumes), a later page refused (said under the list, with its own *Try again*), a sport that
 *   leaves nobody, and the pull, which reads every page again.
 *
 * A face opens the record, *N sports ›* the comparison sheet and the round button acts, as on Home's
 * row; **every friend write reaches every people list** (`LISTS_PEOPLE`): this list reads again, and
 * the row under the screen draws the answer, holding still until Home is back (`usePeopleRow`). The
 * frame, the paging and every state are every people row's
 * (`SeeAllScreen`).
 */

import { useState } from 'react';

import { foundAtSameLevel, type SameLevelPlayer } from '../domain/sameLevel';
import type { SeeAllSport } from '../domain/seeAll';
import { usePersonSheet } from '../hooks/usePersonSheet';
import { useReaderFace } from '../hooks/useReaderFace';
import { useSameLevelPage } from '../hooks/useSameLevel';

import { ComparingSheet } from './ComparingSheet';
import { DISCOVERY_COPY, SAME_LEVEL_PILL_WORDS, nobodyToCompareIn } from './discoveryCopy';
import { RowRecord, type RecordOpened } from './RowRecord';
import { SAME_LEVEL_CARD_SKELETON, SameLevelCard } from './SameLevelCard';
import { SeeAllScreen } from './SeeAllScreen';

export function SameLevelScreen() {
  const COPY = DISCOVERY_COPY.sameLevel;
  const [choice, setChoice] = useState<SeeAllSport>('all');
  const [reading, setReading] = useState<RecordOpened>();
  const list = useSameLevelPage(choice);
  const comparing = usePersonSheet(list.people ?? []);
  const you = useReaderFace();

  return (
    <SeeAllScreen<SameLevelPlayer>
      title={COPY.title}
      backLabel={COPY.back}
      pillWords={SAME_LEVEL_PILL_WORDS}
      choice={choice}
      onPick={setChoice}
      list={list}
      renderPerson={(player) => (
        <SameLevelCard
          player={player}
          you={you}
          onOpen={() =>
            setReading({ playerId: player.playerId, foundIn: foundAtSameLevel(player.shown.sport) })
          }
          onCompare={() => comparing.show(player)}
        />
      )}
      skeleton={SAME_LEVEL_CARD_SKELETON}
      emptyLine={choice === 'all' ? COPY.nobodyAtAll : nobodyToCompareIn(choice)}
      testID="same-level-list"
      overlayUp={reading !== undefined || comparing.open}
      overlays={
        <>
          <ComparingSheet comparing={comparing} />
          <RowRecord opened={reading} onClose={() => setReading(undefined)} />
        </>
      }
    />
  );
}
