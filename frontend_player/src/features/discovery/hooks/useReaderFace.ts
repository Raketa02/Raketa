/**
 * **The reader's own face** — the left of every Same competitive level card, *You* (#802; the Home
 * rows screens §4.2): who they are (`auth`'s `useReaderId`, the cached `/users/me` read once), and
 * their photograph off their own record (`player_record`'s `useOwnFace`, the edge the
 * read crosses by). Read once by the row and once by See all, never per card.
 *
 * `undefined` for a cache that has not heard of them: the card then draws no face on its left
 * rather than somebody else's poster.
 */

import { useReaderId } from '@/features/auth/types';
import { useOwnFace } from '@/features/player_record/types';

export interface ReaderFace {
  readonly playerId: string;
  /** Absent with no photograph, or before the record answers: the poster stands in. */
  readonly photoUrl?: string;
}

export function useReaderFace(): ReaderFace | undefined {
  const playerId = useReaderId();
  const { photoUrl } = useOwnFace(playerId);
  if (playerId === undefined) return undefined;
  return { playerId, ...(photoUrl === undefined ? {} : { photoUrl }) };
}
