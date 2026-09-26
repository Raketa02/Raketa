/**
 * **A profile's face** — the player's own photograph (or the poster standing in for it) for Player,
 * the club's tile for an administrator profile — at a group monogram's two sizes: `row` in the chip,
 * `card` in the sheet's rows (club 6–7).
 *
 * The photograph is the reader's own, off their record (`player_record`'s `useOwnFace`, the edge the
 * yes screen opened), and read only where Player is drawn: an account that does not play has no
 * record to read. Faces are boxes, not circles, and carry no initials (ADR-0167 §3, #513's call).
 */

import { useCurrentUser } from '@/features/auth/types';
import { useOwnFace } from '@/features/player_record/types';
import { PlayerPhoto, theme } from '@/shared/ui';

import type { ProfileOption } from '../domain/profiles';

import { ClubTile } from './ClubTile';

export function ProfileFace({
  option,
  size,
}: {
  readonly option: ProfileOption;
  readonly size: 'card' | 'row';
}) {
  return option.kind === 'player' ? (
    <OwnFace size={size} />
  ) : (
    <ClubTile clubName={option.clubName} size={size} />
  );
}

function OwnFace({ size }: { readonly size: 'card' | 'row' }) {
  const playerId = useCurrentUser().data?.id;
  const { photoUrl } = useOwnFace(playerId);

  if (playerId === undefined) return null;

  return (
    <PlayerPhoto
      playerId={playerId}
      {...(photoUrl === undefined ? {} : { photoUrl })}
      box={{ kind: 'face', size: theme.size.monogram[size] }}
    />
  );
}
