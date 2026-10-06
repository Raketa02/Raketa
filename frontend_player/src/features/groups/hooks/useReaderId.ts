/**
 * **Who is reading the page** — the signed-in player's id, read from the cache once, as
 * `usePlaySegment` reads it, and never observed: an observer would refetch
 * `/users/me` on every entry once it was stale. The entry gate has always read the player before
 * a tab can mount, and the account cannot change under a mounted page — a sign-out tears the tree
 * down.
 *
 * Two things on a group page need it: whose phone preference the fast filter reads, and which
 * seat on the Friends court is the reader's own.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { currentUserQuery } from '@/features/auth/types';

/** The reader's id, or `undefined` for a cache that has not heard of them. */
export function useReaderId(): string | undefined {
  const client = useQueryClient();
  const [readerId] = useState(() => client.getQueryData(currentUserQuery().queryKey)?.id);
  return readerId;
}
