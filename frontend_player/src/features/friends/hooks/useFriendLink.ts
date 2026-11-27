/**
 * **Your friend link, and New link** ([#756](https://github.com/Raketa02/Raketa/issues/756); the
 * friends mechanics §4.1) — the Add friends sheet's *Not on Rakieta yet?* card.
 *
 * **The read is made when the sheet opens**, as the groups above it are, and **its first read
 * writes**: the server makes the code then. Two first reads can race, and the loser is refused with
 * `concurrent_modification` — reading again reads the winner's code, so that one refusal is retried
 * once, over the app's own rule for reads (`shouldRetryQuery`), which it keeps.
 *
 * **New link writes its answer into the read** (`setQueryData`): the server answers with the fresh
 * link, and that is the card's next drawing — no second round trip to learn what was just said. It
 * is **never retried**: each one mints a code, and a New link that raced a read or another New link
 * (`concurrent_modification`) is the state moving, so the link is read again and nothing is said —
 * the friends writes' rule (`stateMoved`).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { shouldRetryQuery } from '@/shared/lib/query-client';

import type { FriendLink } from '../domain/friendLink';
import { readFriendLink, replaceFriendLink } from '../use-cases/friends';

import { friendKeys } from './friendKeys';
import { RACED, stateMoved } from './useFriendWrites';

/** `enabled` false asks nothing — the sheet reads the link only once it is opened. */
export function useFriendLink({ enabled = true }: { readonly enabled?: boolean } = {}) {
  return useQuery<FriendLink, AppError>({
    queryKey: friendKeys.link(),
    queryFn: ({ signal }) => readFriendLink({ signal }),
    enabled,
    retry: (failures, error) =>
      (error.code === RACED && failures < 1) || shouldRetryQuery(failures, error),
  });
}

export function useNewFriendLink() {
  const client = useQueryClient();
  return useMutation<FriendLink, AppError, void>({
    mutationFn: () => replaceFriendLink(),
    onSuccess: (fresh) => client.setQueryData(friendKeys.link(), fresh),
    onError: (error) =>
      stateMoved(error) ? client.invalidateQueries({ queryKey: friendKeys.link() }) : undefined,
  });
}
