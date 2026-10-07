/**
 * **Blocked players, on the You tab** — the ACCOUNT group's last row: its title, how many in one
 * line — *Nobody*, *1 player*, *2 players* — and the door to the list
 * ([#587](https://github.com/Raketa02/Raketa/issues/587), PRD #571 story 19).
 *
 * The line is the screen's own read, so an unblock there is on the row the moment the player comes
 * back; a read that failed says so on the row, in the recovery register every row on the tab uses.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useBlockedPlayers } from '../hooks/useBlockedPlayers';

import { YOU_BLOCKED_PLAYERS_ROUTE } from './blockRoutes';
import { BLOCKS_COPY, blockedCountLine } from './blocksCopy';

export type BlockedPlayersRowProps = Pick<DoorRowProps, 'divided'>;

export function BlockedPlayersRow({ divided }: BlockedPlayersRowProps) {
  const router = useRouter();
  const read = useBlockedPlayers();

  return (
    <DoorRow
      glyph="slash"
      title={BLOCKS_COPY.blockedPlayers.title}
      line={liveLine(read, (blocked) => blockedCountLine(blocked.length))}
      divided={divided}
      onPress={() => router.push(YOU_BLOCKED_PLAYERS_ROUTE)}
    />
  );
}
