/**
 * This feature's query-key factory — **every key it uses, with every parameter that changes the
 * answer.**
 *
 * The two searches are keyed by **the text**, trimmed, because each keystroke is a new question
 * and a key per text is what lets the answer to `ogr` stay on screen while `ogro` is being asked
 * (`placeholderData`). The page is the infinite query's own cursor rather than part of the key:
 * the pages of one text are one answer, read twenty clubs at a time.
 *
 * Everything sits under one root, so a sign-out's `queryClient.clear()` takes it all and a join
 * can reach every cached search at once (`searches()`). **What is read about one group sits under
 * its page's key** — its Members per sport and the requests waiting on it — so a leave or a delete
 * reaches all of it through `detail(groupId)`.
 */

import type { Sport } from '@/shared/vocabulary/sport';

export const groupKeys = {
  all: ['groups'] as const,
  /** The reader's Groups list, newest joined first. */
  mine: () => [...groupKeys.all, 'mine'] as const,
  /** One group, as its page reads it — and, under it, everything else read about the group. */
  detail: (groupId: string) => [...groupKeys.all, 'detail', groupId] as const,
  /** Every sport's Members of one group — the root an answer to a request refreshes. */
  allMembers: (groupId: string) => [...groupKeys.detail(groupId), 'members'] as const,
  /** Members of one group, for one sport. */
  members: (groupId: string, sport: Sport) => [...groupKeys.allMembers(groupId), sport] as const,
  /** The Join requests waiting on one group — the Owner's read. */
  requests: (groupId: string) => [...groupKeys.detail(groupId), 'requests'] as const,
  /** **A mutation key**: the answers to one group's requests, counted to re-read the queue once. */
  answers: (groupId: string) => [...groupKeys.requests(groupId), 'answer'] as const,
  /** **A mutation key**: leaving or deleting one group — found to take a waiting one back (#529). */
  exit: (groupId: string) => [...groupKeys.detail(groupId), 'exit'] as const,
  /** Every cached search — the root a join rewrites. */
  searches: () => [...groupKeys.all, 'search'] as const,
  /** New group's home-club search, for one text. */
  homeClubs: (text: string) => [...groupKeys.searches(), 'home-clubs', text] as const,
  /** Join a group's search, for one text. */
  toJoin: (text: string) => [...groupKeys.searches(), 'join', text] as const,
};
