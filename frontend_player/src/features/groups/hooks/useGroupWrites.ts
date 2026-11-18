/**
 * **Joining a group, creating one, and Info's four writes** — and what each does to the
 * cache.
 *
 * ## A join rewrites the row it came from, everywhere it is cached
 *
 * The answer to `POST /membership` **is** the row — the same group, with the reader's new
 * relation on it — so it is written into every cached search that holds that group (a club can be
 * in the home-club answer and the join answer at once), and the button turns into *you're in* or
 * *requested · waiting* without a second read. A join that made the reader a member also
 * invalidates the Groups list, which now has one more card. A search row is not optimistic:
 * whether a tap admits or asks is the group's policy **on the server**, and a client that guessed
 * would draw *you're in* over a group that has just switched to *People I approve*.
 *
 * **Home's Hottest groups card is** ([#800](https://github.com/Raketa02/Raketa/issues/800); the
 * Home rows screens §3.4: *Join turns the chip to You're in at once*). Its chip turns on the tap, to
 * what the card's own policy says — *You're in* or *Asked* — and **the answer's relation lands over
 * the guess**, so a group that switched policy meanwhile reads what the server did. A refusal puts
 * the one card's relation back, whatever else is in flight. Every read that could show the group is
 * then read again — the row, the Groups list, Home's own read (*Your games*) — and the searches are
 * written, as above, never re-read.
 *
 * A failed join is said in a toast, because the row it was pressed on has no line to say it in;
 * the row goes back to its button. Joining twice changes nothing on the server, so a second tap
 * after a failure is safe — but it is the player's tap, never a retry (mutations are never
 * retried globally).
 *
 * ## A withdraw takes the request back at once
 *
 * **Withdraw request** (#800, the mechanics §5.8) turns the card back to *Join* or *Ask to join* on
 * the tap: the route refuses nothing — an approval a moment earlier leaves the reader a member, and
 * the re-read says so — so the only failure is the network's, said in a toast with the card put back.
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
 * is re-read — the relation is *none* now, or the group is gone — and Home's Hottest groups with
 * them, whose card would otherwise still say *You're in*. What is read about the group
 * itself is **marked stale and not re-read**: the page that reads it is still on its way out, and a
 * re-read now would draw *not one of yours* over it as it leaves. A refusal that says the count
 * moved — `lone_owner_cannot_leave`, `group_has_other_members` — re-reads the group, so the door
 * becomes the one that works.
 */

import {
  useMutation,
  useMutationState,
  useQueryClient,
  type InfiniteData,
  type QueryClient,
} from '@tanstack/react-query';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';

import { proposalKeys } from '@/features/proposals/types';

import type {
  ClubSearch,
  EditedGroup,
  Group,
  GroupAtClub,
  GroupDetails,
  HottestGroup,
  HottestRow,
  JoinRequest,
  MyGroup,
  NewGroup,
} from '../domain/group';
import { countMoved, type GroupExit } from '../domain/groupInfo';
import { groupAction } from '../domain/groupRules';
import { withRelation } from '../domain/hottest';
import type { GroupRelation } from '../domain/vocabulary';
import {
  answerRequest,
  createGroup,
  editGroup,
  exitGroup,
  joinGroup,
  withdrawJoinRequest,
  type RequestAnswer,
} from '../use-cases/groupWrites';

import { groupKeys } from './groupKeys';

/** Every cached search's rows, each passed through `row` — the one place a search is rewritten. */
function rewriteSearches(client: QueryClient, row: (group: GroupAtClub) => GroupAtClub): void {
  client.setQueriesData<InfiniteData<ClubSearch, number>>(
    { queryKey: groupKeys.searches() },
    (data) =>
      data === undefined
        ? data
        : {
            ...data,
            pages: data.pages.map((page) => ({
              ...page,
              clubs: page.clubs.map((club) => ({ ...club, groups: club.groups.map(row) })),
            })),
          },
  );
}

/** The same group, wherever a cached search holds it, with the answer's relation on it. */
function writeRow(client: QueryClient, answer: GroupAtClub): void {
  rewriteSearches(client, (group) => (group.id === answer.id ? answer : group));
}

/** The relation a Hottest groups card stood at before a tap moved it — what a refusal puts back. */
interface HeldRelation {
  readonly relation?: GroupRelation;
}

/** One Hottest groups card's relation, moved — nothing when the row holds no such card. */
function moveCard(client: QueryClient, groupId: string, relation: GroupRelation): void {
  client.setQueryData<HottestRow>(groupKeys.hottest(), (row) =>
    row === undefined ? row : withRelation(row, groupId, relation),
  );
}

/**
 * **The card's relation drawn at once**, from what its own policy says the tap does — or nothing,
 * for a tap from a row the Hottest groups read does not hold.
 */
async function guessCard(
  client: QueryClient,
  groupId: string,
  guess: (card: HottestGroup) => GroupRelation,
): Promise<HeldRelation> {
  const card = client
    .getQueryData<HottestRow>(groupKeys.hottest())
    ?.groups.find((held) => held.id === groupId);
  if (card === undefined) return {};
  // A read in flight would land the old relation over the guess.
  await client.cancelQueries({ queryKey: groupKeys.hottest() });
  moveCard(client, groupId, guess(card));
  return { relation: card.relation };
}

/**
 * A refusal: the one card back where it stood, and the write's own error said. **The row is read
 * again** when the tap had moved a card: the guess cancelled any read in flight — a pull's, a
 * return's — and without a new one the row's cards and its count (#822) would stand as they were
 * before it.
 */
function refused(
  client: QueryClient,
  groupId: string,
  held: HeldRelation | undefined,
  error: AppError,
): void {
  if (held?.relation !== undefined) {
    moveCard(client, groupId, held.relation);
    void client.invalidateQueries({ queryKey: groupKeys.hottest() });
  }
  showToast({ message: recoveryMessage(error), tone: 'bad' });
}

/**
 * **Every read that could show a group the reader's relation to just moved** (the Home rows mechanics
 * §13): Home's Hottest groups, the Groups list, and Home's own read — *Your games* and the groupless
 * line. **The searches are written, never re-read**: the write's answer is the row, and a search
 * read again could land an older relation over it.
 */
function rereadWhereTheGroupShows(client: QueryClient): void {
  void client.invalidateQueries({ queryKey: groupKeys.hottest() });
  void client.invalidateQueries({ queryKey: groupKeys.mine() });
  void client.invalidateQueries({ queryKey: proposalKeys.home() });
}

export function useJoinGroup() {
  const client = useQueryClient();

  return useMutation<GroupAtClub, AppError, string, HeldRelation>({
    mutationKey: groupKeys.joins(),
    mutationFn: joinGroup,
    onMutate: (groupId) =>
      guessCard(client, groupId, (card) => (groupAction(card) === 'join' ? 'MEMBER' : 'REQUESTED')),
    onSuccess: (answer) => {
      writeRow(client, answer);
      moveCard(client, answer.id, answer.relation);
      rereadWhereTheGroupShows(client);
    },
    onError: (error, groupId, held) => refused(client, groupId, held, error),
  });
}

/** **Withdraw request** (#800) — the card reads *Join* or *Ask to join* again on the tap. */
export function useWithdrawJoinRequest() {
  const client = useQueryClient();

  return useMutation<void, AppError, string, HeldRelation>({
    mutationKey: groupKeys.withdrawals(),
    mutationFn: withdrawJoinRequest,
    onMutate: (groupId) => guessCard(client, groupId, () => 'NONE'),
    onSuccess: (_nothing, groupId) => {
      // A search row still saying *requested · waiting* reads as nothing asked; an approval a moment
      // earlier is the Groups list's re-read to say.
      rewriteSearches(client, (group) =>
        group.id === groupId && group.relation === 'REQUESTED'
          ? { ...group, relation: 'NONE' }
          : group,
      );
      rereadWhereTheGroupShows(client);
    },
    onError: (error, groupId, held) => refused(client, groupId, held, error),
  });
}

/**
 * **The groups whose join, ask or withdraw is still in flight** — any card's, from any screen, so
 * Home's row lets go of a second tap on that card while the first is unanswered (#800).
 */
export function useRelationWritesInFlight(): readonly string[] {
  return useMutationState({
    filters: { mutationKey: groupKeys.relationWrites(), status: 'pending' },
    select: (mutation) => mutation.state.variables,
  }).filter((groupId): groupId is string => typeof groupId === 'string');
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

/**
 * *Leave the group* or *Delete the group* — whichever door Info drew.
 *
 * **Offline, the act waits for the network, as every write here does — and closing the sheet takes
 * it back** (`takeBack`, #529). A paused mutation is not the sheet's: `reset` only lets go of it, and
 * it resumes on the next reconnect or return to the app whatever the player is looking at by then.
 * A player who closed the sheet said *stay*, so the waiting act is removed from the queue as well.
 */
export function useExitGroup(groupId: string) {
  const client = useQueryClient();
  const mutationKey = groupKeys.exit(groupId);

  const act = useMutation<void, AppError, GroupExit>({
    mutationKey,
    mutationFn: (exit) => exitGroup(groupId, exit),
    onSuccess: () => {
      client.setQueryData<readonly MyGroup[]>(groupKeys.mine(), (groups) =>
        groups?.filter((group) => group.id !== groupId),
      );
      void client.invalidateQueries({ queryKey: groupKeys.mine() });
      void client.invalidateQueries({ queryKey: groupKeys.searches() });
      // Home's row reads *You're in* on it until it is read again (#800).
      void client.invalidateQueries({ queryKey: groupKeys.hottest() });
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

  /** The sheet was closed: forget the act, and drop it from the queue if it is still waiting. */
  function takeBack() {
    const queue = client.getMutationCache();
    for (const waiting of queue.findAll({ mutationKey, predicate: (m) => m.state.isPaused })) {
      queue.remove(waiting);
    }
    act.reset();
  }

  return { act, takeBack };
}
