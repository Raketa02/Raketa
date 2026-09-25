/**
 * **Joining a group, creating one, and the Info tab's four writes** — and what each does to the
 * cache.
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
 *
 * ## An answer to a request takes its row at once
 *
 * **✕** and **Approve** (#514) each end the request, whatever the server then does — declined, or
 * a member — so the row leaves *Want to join* the moment it is tapped, and comes back only if the
 * tap is refused, with a toast saying why. This one **is** optimistic where a join is not: there
 * is nothing for the server to decide about where the row goes, only whether the tap reached it.
 * The queue is re-read once the last answer in flight has landed — not after each, which would
 * draw a row answered a moment ago back in until its own answer lands. An approval also re-reads
 * the group, its Members and the Groups list: somebody is in, and every count says so.
 *
 * ## An edit seeds the page, and says who it let in
 *
 * The answer to `PUT /details` is the group as the save left it, so it is written under the
 * page's key and the page is right when the Owner goes back. Everything that reads the name or
 * the waiting queue is re-read — the Groups list, every search, the requests, and Members,
 * because a switch to Anyone admitted everybody waiting. Who it admitted is the answer's, and the
 * Edit screen draws it.
 *
 * ## Leaving and deleting take the group off the list
 *
 * The card is dropped from the Groups list on the answer and the list re-read, and every search
 * is re-read — the relation is *none* now, or the group is gone. What is read about the group
 * itself is **marked stale and not re-read**: the page that reads it is still on its way out, and a
 * re-read now would draw *not one of yours* over it as it leaves. A refusal that says the count
 * moved — `lone_owner_cannot_leave`, `group_has_other_members` — re-reads the group, so the door
 * becomes the one that works.
 */

import {
  useMutation,
  useQueryClient,
  type InfiniteData,
  type QueryClient,
} from '@tanstack/react-query';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';

import type {
  ClubSearch,
  EditedGroup,
  Group,
  GroupAtClub,
  GroupDetails,
  JoinRequest,
  MyGroup,
  NewGroup,
} from '../domain/group';
import { countMoved, type GroupExit } from '../domain/groupInfo';
import {
  answerRequest,
  createGroup,
  editGroup,
  exitGroup,
  joinGroup,
  type RequestAnswer,
} from '../use-cases/groupWrites';

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
 * `refusal` words a refused answer for the toast. It is the caller's because the words are
 * copy, and it is handed in rather than said by the caller because the row it was pressed on is
 * gone by then — only the mutation's own callbacks outlive it.
 */
export function useAnswerRequest(groupId: string, refusal: (error: AppError) => string) {
  const client = useQueryClient();
  const key = groupKeys.requests(groupId);
  const mutationKey = groupKeys.answers(groupId);

  return useMutation<void, AppError, RequestReply, AnsweredRow>({
    mutationKey,
    mutationFn: ({ playerId, answer }) => answerRequest(groupId, playerId, answer),
    onMutate: async ({ playerId }) => {
      await client.cancelQueries({ queryKey: key });
      const requests = client.getQueryData<readonly JoinRequest[]>(key) ?? [];
      const at = requests.findIndex((request) => request.playerId === playerId);
      client.setQueryData<readonly JoinRequest[]>(key, (held) =>
        held?.filter((request) => request.playerId !== playerId),
      );
      return at < 0 ? {} : { row: requests[at], at };
    },
    onError: (error, _reply, context) => {
      // Only this row comes back, where it stood: another answer may be on its way, and its row
      // stays gone until that one is refused too.
      const { row, at } = context ?? {};
      if (row !== undefined && at !== undefined) {
        client.setQueryData<readonly JoinRequest[]>(key, (held) =>
          held === undefined || held.some((request) => request.playerId === row.playerId)
            ? held
            : [...held.slice(0, at), row, ...held.slice(at)],
        );
      }
      showToast({ message: refusal(error), tone: 'bad' });
    },
    onSuccess: (_nothing, { answer }) => {
      if (answer !== 'approve') return;
      void client.invalidateQueries({ queryKey: groupKeys.detail(groupId), exact: true });
      void client.invalidateQueries({ queryKey: groupKeys.allMembers(groupId) });
      void client.invalidateQueries({ queryKey: groupKeys.mine() });
    },
    onSettled: () => {
      // This answer is still counted while it settles: 1 is the last one in flight.
      if (client.isMutating({ mutationKey }) === 1) {
        void client.invalidateQueries({ queryKey: key });
      }
    },
  });
}

export function useEditGroup(groupId: string) {
  const client = useQueryClient();

  return useMutation<EditedGroup, AppError, GroupDetails>({
    mutationFn: (details) => editGroup(groupId, details),
    onSuccess: ({ group }) => {
      client.setQueryData(groupKeys.detail(groupId), group);
      void client.invalidateQueries({ queryKey: groupKeys.allMembers(groupId) });
      void client.invalidateQueries({ queryKey: groupKeys.requests(groupId) });
      void client.invalidateQueries({ queryKey: groupKeys.mine() });
      void client.invalidateQueries({ queryKey: groupKeys.searches() });
    },
  });
}

/** *Leave the group* or *Delete the group* — whichever door the Info tab drew. */
export function useExitGroup(groupId: string) {
  const client = useQueryClient();

  return useMutation<void, AppError, GroupExit>({
    mutationFn: (exit) => exitGroup(groupId, exit),
    onSuccess: () => {
      client.setQueryData<readonly MyGroup[]>(groupKeys.mine(), (groups) =>
        groups?.filter((group) => group.id !== groupId),
      );
      void client.invalidateQueries({ queryKey: groupKeys.mine() });
      void client.invalidateQueries({ queryKey: groupKeys.searches() });
      void client.invalidateQueries({
        queryKey: groupKeys.detail(groupId),
        refetchType: 'none',
      });
    },
    onError: (error) => {
      if (countMoved(error.code)) {
        void client.invalidateQueries({ queryKey: groupKeys.detail(groupId), exact: true });
      }
    },
  });
}
