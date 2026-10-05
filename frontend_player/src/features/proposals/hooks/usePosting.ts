/**
 * ***Post a game*'s reads and its write** ([#558](https://github.com/Raketa02/Raketa/issues/558);
 * the backend's #546).
 *
 * | | |
 * | --- | --- |
 * | `usePostingGrid` | `GET /pools/{id}/posting-grid` — one week of WHEN, for what the controls ask |
 * | `usePostingSlot` | `GET /pools/{id}/posting-grid/slot` — a cell's sheet, while it is open |
 * | `usePostAGame` | `POST /pools/{id}/posts` — *Post — you're In* |
 *
 * ## The grid keeps its last answer while a control changes it — within a sport, a kind and a week
 *
 * Every tap on a control is a new question, and the grid would otherwise blank to a spinner between
 * a stepper's taps. So the answer for the last ask stays drawn while the next is read — **but only
 * while the sport, the kind and the week are the same**: a padel grid drawn while tennis is read, or
 * this week's while next week's is, would put a cell under a finger that is not the one it reads as;
 * and the engine's level window the steppers step against is the kind's, so a grid kept across a
 * kind would hand them the other kind's.
 *
 * ## A post re-reads what it changed, and is never retried
 *
 * Posting is the poster's yes: it adds a live yes, a game to *You're In* and a dealt challenge to
 * every deck of the group — so on success the group's root (its decks, its Fill in and every grid),
 * every game's details and the live yeses are read again. Not retried, the route's own rule: a
 * second post is a second game.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type Query,
  type QueryKey,
} from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type {
  CellAt,
  Posted,
  PostingAsk,
  PostingGrid,
  PostingSlot,
  PostingWeek,
  PostPick,
} from '../domain/posting';
import { postAGame, readPostingGrid, readPostingSlot } from '../use-cases/posting';

import { proposalKeys } from './proposalKeys';
import { useLatest } from './useLatest';

/** Whether a previous grid read asked for the same sport, kind and week — worth keeping drawn. */
function sameGrid(
  previous: Query<PostingGrid, AppError, PostingGrid, QueryKey> | undefined,
  ask: PostingAsk,
  week: PostingWeek,
): boolean {
  const meta = previous?.meta;
  return meta?.sport === ask.sport && meta.kind === ask.kind && meta.week === week;
}

export function usePostingGrid(groupId: string, ask: PostingAsk, week: PostingWeek) {
  return useQuery<PostingGrid, AppError>({
    queryKey: proposalKeys.postingGrid(groupId, ask, week),
    queryFn: ({ signal }) => readPostingGrid(groupId, ask, week, { signal }),
    // What the placeholder compares against — read off the query, never off its key's positions.
    meta: { sport: ask.sport, kind: ask.kind, week },
    placeholderData: (previous, query) => (sameGrid(query, ask, week) ? previous : undefined),
  });
}

/** A cell's sheet — read while it is open, for the ask the grid was read with. */
export function usePostingSlot(groupId: string, ask: PostingAsk, cell: CellAt | undefined) {
  return useQuery<PostingSlot, AppError>({
    queryKey: proposalKeys.postingSlot(groupId, ask, cell?.day ?? '', cell?.range ?? 'MORNING'),
    queryFn: ({ signal }) =>
      readPostingSlot(groupId, ask, cell?.day ?? '', cell?.range ?? 'MORNING', { signal }),
    enabled: cell !== undefined,
  });
}

export interface PostAsked {
  readonly ask: PostingAsk;
  readonly pick: PostPick;
}

/**
 * ***Post — you're In*** — `onPosted` and `onRefused` are handled on the mutation rather than on the
 * call, the deck's reason: a call's own callbacks are dropped once another call is made, and they
 * never run once the screen that made it has gone.
 */
export function usePostAGame(
  groupId: string,
  handlers: {
    readonly onPosted: (posted: Posted, asked: PostAsked) => void;
    readonly onRefused: (error: AppError, asked: PostAsked) => void;
  },
) {
  const client = useQueryClient();
  const latest = useLatest(handlers);

  return useMutation<Posted, AppError, PostAsked>({
    mutationFn: ({ ask, pick }) => postAGame(groupId, ask, pick),
    onSuccess: async (posted, asked) => {
      await Promise.all([
        client.invalidateQueries({ queryKey: proposalKeys.group(groupId) }),
        client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
        client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
      ]);
      latest.current.onPosted(posted, asked);
    },
    onError: (error, asked) => latest.current.onRefused(error, asked),
  });
}
