/**
 * **The record a New in Raketa tile opens** (#801; the Home rows mechanics §12) — `player_record`'s
 * sheet, its requests sent from *new players*. A friend act or a block there re-reads the row under
 * it on its own (`rereadPeopleLists`). Nothing while no tile is open.
 */

import { PlayerRecordSheet } from '@/features/player_record/types';

import { FOUND_AMONG_NEW_PLAYERS } from '../domain/joiner';

export function JoinerRecord({
  playerId,
  onClose,
}: {
  /** Whose record is up — none while no tile is open. */
  readonly playerId: string | undefined;
  readonly onClose: () => void;
}) {
  if (playerId === undefined) return null;
  return (
    <PlayerRecordSheet
      visible
      onClose={onClose}
      subject={{ kind: 'player', playerId }}
      foundIn={FOUND_AMONG_NEW_PLAYERS}
    />
  );
}
