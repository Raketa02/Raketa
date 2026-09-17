/**
 * **How others see you, opened from the tab** — `PlayerRecordSheet` on `{ kind: 'me' }`,
 * section for section, retitled by the server's `is_self`, with nothing added and nothing
 * removed ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The shell holds whether it is up, because the header card and the *How others see you*
 * row both open it and the shell composes both. What this wraps is the one thing the shell
 * should not know: whose record, through which door — the signed-in player's id, read off
 * `GET /users/me` for the poster, on the ungated `/me` route. No sport, no distance, no
 * overlap, no pairing and no foot: it is your own record, opened from nowhere in particular.
 */

import { useCurrentUser } from '@/features/auth/types';

import { ownSubject } from '../hooks/useOwnRecord';

import { PlayerRecordSheet } from './PlayerRecordSheet';

export interface OwnRecordSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
}

export function OwnRecordSheet({ visible, onClose }: OwnRecordSheetProps) {
  const playerId = useCurrentUser().data?.id;

  // Nobody to open it on until the player is read — which bootstrap seeds before the tab can
  // be pressed, so this is the one render before that read rather than a state to draw.
  if (playerId === undefined) return null;

  return <PlayerRecordSheet visible={visible} onClose={onClose} subject={ownSubject(playerId)} />;
}
