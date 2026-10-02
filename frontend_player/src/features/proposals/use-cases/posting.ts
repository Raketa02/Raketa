/**
 * **Posting a game** (#546, #558) — pass-throughs: who fits when, which courts are free and what is
 * already happening are the server's reads, and whether a post may be made is the server's to
 * refuse, each refusal with its own code. Nothing is decided on the way in or out.
 */

import { getPostingGrid, getPostingSlot, postPost, type Cancellable } from '../api/proposalsApi';
import type {
  Posted,
  PostingAsk,
  PostingGrid,
  PostingSlot,
  PostingWeek,
  PostPick,
} from '../domain/posting';
import type { DayRange } from '../domain/vocabulary';
import { toPosted, toPostingGrid, toPostingSlot, toWireAsk } from '../mappers/postingMappers';

export async function readPostingGrid(
  groupId: string,
  ask: PostingAsk,
  week: PostingWeek,
  options: Cancellable = {},
): Promise<PostingGrid> {
  return toPostingGrid(await getPostingGrid(groupId, toWireAsk(ask), week, options));
}

export async function readPostingSlot(
  groupId: string,
  ask: PostingAsk,
  day: string,
  range: DayRange,
  options: Cancellable = {},
): Promise<PostingSlot> {
  return toPostingSlot(await getPostingSlot(groupId, toWireAsk(ask), day, range, options));
}

/** *Post — you're In*: the controls and the court hour picked. */
export async function postAGame(
  groupId: string,
  ask: PostingAsk,
  pick: Pick<PostPick, 'clubId' | 'startsAt'>,
): Promise<Posted> {
  return toPosted(
    await postPost(groupId, { ...toWireAsk(ask), club_id: pick.clubId, starts_at: pick.startsAt }),
  );
}
