/**
 * **Creating an official group, and answering its Join requests** — and what each does to the
 * cache.
 *
 * ## A create seeds the page it lands on
 *
 * The answer to the create is the group as its page reads it, so it is written under the page's key
 * and the page draws at once, with *Group created* over it; the Groups tab is re-read, since it has a
 * new card. **Never retried** — two creates are two groups — and the button is busy while it is in
 * flight.
 *
 * ## An answer takes its row at once
 *
 * `groups`' `useAnswerRequest`, for an Administrator's routes: **✕** and **Approve** each end the
 * request whatever the server then does, so the row leaves *Want to join* on the tap and comes back —
 * that row alone, where it stood — only if the tap is refused, with a toast in the caller's words.
 * The group is re-read once the last answer in flight has landed, never after each, which would draw
 * a row answered a moment ago back in; that re-read is what puts an approved player at the top of
 * the players list. The Groups tab is re-read with it: *N waiting* and *N members* have moved.
 *
 * **A refusal that says the Administrator was removed is not this hook's to say.** The removal watch
 * (`useRemovalWatch`) answers `not_an_administrator` for the whole area, once; a toast here as well
 * would say it twice.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { JoinRequest } from '@/features/groups/types';
import type { AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';

import type { NewOfficialGroup, OfficialGroup } from '../domain/officialGroup';
import {
  answerRequest,
  createOfficialGroup,
  type RequestAnswer,
} from '../use-cases/officialGroups';

import { administratorKeys } from './administratorKeys';
import { isRemoval } from './useRemovalWatch';

export function useCreateOfficialGroup(clubId: string) {
  const client = useQueryClient();

  return useMutation<OfficialGroup, AppError, NewOfficialGroup>({
    mutationKey: administratorKeys.create(clubId),
    mutationFn: (group) => createOfficialGroup(clubId, group),
    onSuccess: (group) => {
      client.setQueryData(administratorKeys.group(clubId, group.id), group);
      void client.invalidateQueries({ queryKey: administratorKeys.groups(clubId) });
    },
  });
}

/** The row an answer took, and where it stood — what a refusal puts back. */
interface AnsweredRow {
  readonly row?: JoinRequest;
  readonly at?: number;
}

/** A tap on **✕** or **Approve**: whose request, and which answer. */
export interface RequestReply {
  readonly playerId: string;
  readonly answer: RequestAnswer;
}

/**
 * `refusal` words a refused answer for the toast — the caller's, because the words are copy, and
 * handed in because the row it was pressed on is gone by then.
 */
export function useAnswerAsAdministrator(
  clubId: string,
  groupId: string,
  refusal: (error: AppError) => string,
) {
  const client = useQueryClient();
  const key = administratorKeys.group(clubId, groupId);
  const mutationKey = administratorKeys.answers(clubId, groupId);

  return useMutation<void, AppError, RequestReply, AnsweredRow>({
    mutationKey,
    mutationFn: ({ playerId, answer }) => answerRequest(clubId, groupId, playerId, answer),
    onMutate: async ({ playerId }) => {
      await client.cancelQueries({ queryKey: key, exact: true });
      const requests = client.getQueryData<OfficialGroup>(key)?.requests ?? [];
      const at = requests.findIndex((request) => request.playerId === playerId);
      client.setQueryData<OfficialGroup>(key, (group) =>
        group === undefined
          ? group
          : {
              ...group,
              requests: group.requests.filter((request) => request.playerId !== playerId),
            },
      );
      return at < 0 ? {} : { row: requests[at], at };
    },
    onError: (error, _reply, context) => {
      // Only this row comes back, where it stood: another answer may be on its way.
      const { row, at } = context ?? {};
      if (row !== undefined && at !== undefined) {
        client.setQueryData<OfficialGroup>(key, (group) =>
          group === undefined || group.requests.some((held) => held.playerId === row.playerId)
            ? group
            : {
                ...group,
                requests: [...group.requests.slice(0, at), row, ...group.requests.slice(at)],
              },
        );
      }
      if (!isRemoval(error)) showToast({ message: refusal(error), tone: 'bad' });
    },
    onSettled: () => {
      // This answer is still counted while it settles: 1 is the last one in flight.
      if (client.isMutating({ mutationKey }) === 1) {
        void client.invalidateQueries({ queryKey: key, exact: true });
        void client.invalidateQueries({ queryKey: administratorKeys.groups(clubId) });
      }
    },
  });
}
