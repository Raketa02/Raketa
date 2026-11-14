/**
 * **The record a people row opens** (#801, #802; the Home rows mechanics §12) — `player_record`'s
 * sheet, its requests sent from **the row it was opened from** (`foundIn`): *new players*, or *same
 * level* in the card's sport. A friend act or a block there re-reads the row under it on its own
 * (`rereadPeopleLists`). Nothing while no record is open.
 */

import type { FoundIn } from '@/features/friends/types';
import { PlayerRecordSheet } from '@/features/player_record/types';

/** Whose record is up, and the row it was opened from. */
export interface RecordOpened {
  readonly playerId: string;
  readonly foundIn: FoundIn;
}

export function RowRecord({
  opened,
  onClose,
}: {
  /** None while no record is open. */
  readonly opened: RecordOpened | undefined;
  readonly onClose: () => void;
}) {
  if (opened === undefined) return null;
  return (
    <PlayerRecordSheet
      visible
      onClose={onClose}
      subject={{ kind: 'player', playerId: opened.playerId }}
      foundIn={opened.foundIn}
    />
  );
}
