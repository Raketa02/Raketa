/**
 * **NEW IN RAKETA** — the third of Home's five rows ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * ADR-0204 §5; the Home rows screens §5.1; the mechanics §7; home rows 1, 17, 17.2).
 *
 * Up to ten portrait tiles on Home's row frame (`HomeRow`, `HomeRowRail`'s `tiles`), in the read's
 * order — who the reader isn't connected with first, then who they asked, then friends — with
 * *See all ›* to the grid. **Hidden with its heading** while the read holds nothing, is in flight, or
 * failed: a row that fails is left out, and the rest of Home stands (the screens §1).
 *
 * **A tile opens the record**, its requests sent from *new players* (`foundIn`). The row's reads list
 * people (`LISTS_PEOPLE`), so any friend write or block — from a tile, the record, or anywhere else in
 * the app — reads the row again (the mechanics §13).
 */

import { router } from 'expo-router';
import { useState } from 'react';

import { HomeRow, HomeRowRail } from '@/shared/ui';

import { FOUND_AMONG_NEW_PLAYERS, type Joiner } from '../domain/joiner';
import { useNewInRaketa } from '../hooks/useNewInRaketa';

import { DISCOVERY_COPY } from './discoveryCopy';
import { NEW_IN_RAKETA_ROUTE } from './discoveryRoutes';
import { RowRecord, type RecordOpened } from './RowRecord';
import { JoinerTile } from './JoinerTile';

export function NewInRaketaRow() {
  const joiners = useNewInRaketa().data;
  if (joiners === undefined || joiners.length === 0) return null;
  return <NewInRaketa joiners={joiners} />;
}

function NewInRaketa({ joiners }: { readonly joiners: readonly Joiner[] }) {
  const [reading, setReading] = useState<RecordOpened>();

  return (
    <HomeRow
      heading={DISCOVERY_COPY.newInRaketa.heading}
      link={{
        words: DISCOVERY_COPY.newInRaketa.seeAll,
        label: DISCOVERY_COPY.newInRaketa.seeAllLabel,
        onPress: () => router.push(NEW_IN_RAKETA_ROUTE),
      }}
      testID="new-in-raketa"
    >
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
    </HomeRow>
  );
}
