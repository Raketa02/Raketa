/**
 * **Joining a group, and creating one** — the two writes, and what each does to the cache.
 *
 * ## A join rewrites the row it came from, everywhere it is cached
 *
 * The answer to `POST /membership` **is** the row — the same group, with the reader's new
 * relation on it — so it is written into every cached search that holds that group (a club can be
 * in the home-club answer and the join answer at once), and the button turns into *you're in* or
 * *requested · waiting* without a second read. A join that made the reader a member also
 * invalidates the Groups list, which now has one more card. Neither is optimistic: whether a tap
 * admits or asks is the group's policy **on the server**, and a client that guessed would draw
 * *you're in* over a group that has just switched to *People I approve*.
 *
 * A failed join is said in a toast, because the row it was pressed on has no line to say it in;
 * the row goes back to its button. Joining twice changes nothing on the server, so a second tap
 * after a failure is safe — but it is the player's tap, never a retry (mutations are never
 * retried globally).
 *
 * ## A create seeds the page it lands on
 *
 * The answer to `POST /groups` is the group as its page reads it, so it is written under the
 * page's key and the page draws at once, with the toast over it. The Groups list and every cached
 * search are invalidated: the list has a new card, and the club now has a group here. **Never
 * retried**, because two creates are two groups; the button is busy while it is in flight.
 */

import {
  useMutation,
  useQueryClient,
  type InfiniteData,
  type QueryClient,
} from '@tanstack/react-query';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';

import type { ClubSearch, Group, GroupAtClub, NewGroup } from '../domain/group';
import { createGroup, joinGroup } from '../use-cases/groupWrites';

import { groupKeys } from './groupKeys';

/** The same group, wherever a cached search holds it, with the answer's relation on it. */
function writeRow(client: QueryClient, answer: GroupAtClub): void {
  client.setQueriesData<InfiniteData<ClubSearch, number>>(
    { queryKey: groupKeys.searches() },
    (data) =>
      data === undefined
        ? data
        : {
            ...data,
            pages: data.pages.map((page) => ({
              ...page,
              clubs: page.clubs.map((club) => ({
                ...club,
                groups: club.groups.map((group) => (group.id === answer.id ? answer : group)),
              })),
            })),
          },
  );
}

export function useJoinGroup() {
  const client = useQueryClient();

  return useMutation<GroupAtClub, AppError, string>({
    mutationFn: joinGroup,
    onSuccess: (answer) => {
      writeRow(client, answer);
      if (answer.relation === 'MEMBER') {
        void client.invalidateQueries({ queryKey: groupKeys.mine() });
      }
    },
    onError: (error) => showToast({ message: recoveryMessage(error), tone: 'bad' }),
  });
}

export function useCreateGroup() {
  const client = useQueryClient();

  return useMutation<Group, AppError, NewGroup>({
    mutationFn: createGroup,
    onSuccess: (group) => {
      client.setQueryData(groupKeys.detail(group.id), group);
      void client.invalidateQueries({ queryKey: groupKeys.mine() });
      void client.invalidateQueries({ queryKey: groupKeys.searches() });
    },
  });
}
