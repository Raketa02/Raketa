/**
 * **Who is reading the screen** — the signed-in player's id, read from the cache once and never
 * observed: an observer would refetch `/users/me` on every entry once it was stale. The entry gate
 * has always read the player before a tab can mount, and the account cannot change under a mounted
 * screen — a sign-out tears the tree down.
 *
 * Every surface that needs to know whose it is reads it here: whose phone preference a choice is
 * (the Play segment, the Rankings view, Home's opened and dismissed games, a group's fast filter),
 * which seat on a group's Friends court is the reader's, and the reader's own face on a Same
 * competitive level card (#802). It was five copies of one line until #802 made a sixth caller.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { currentUserQuery } from './useCurrentUser';

/** The reader's id, or `undefined` for a cache that has not heard of them. */
export function useReaderId(): string | undefined {
  const client = useQueryClient();
  const [readerId] = useState(() => client.getQueryData(currentUserQuery().queryKey)?.id);
  return readerId;
}
