/**
 * **The friends card and *Find a court*** ([#757](https://github.com/Raketa02/Raketa/issues/757))
 * — one read each, keyed by everything asked, so the group's Friends court and the card under it
 * share one answer: the court draws the card's sides from the same read the card is drawn from.
 *
 * | | |
 * | --- | --- |
 * | `useFriendsCard` | `GET /pools/{id}/friends-card` — the line-up's card; nothing asked until every seat is filled |
 * | `useFriendsCourts` | `GET /pools/{id}/friends-card/courts` — *Find a court*, asked only once the sheet opens |
 *
 * **A changed line-up is a new key, and the card reads again from nothing** — *what is sent is
 * what was seen* (the mechanics §7.4): the card a swap or a court asks for is never drawn from the
 * one before it. A refusal is not retried — the app's default, which retries only what the error
 * model calls safe to — since each names the line-up, and asking again asks the same question.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { FriendsCard, FriendsCardAsk, FriendsCourts } from '../domain/friendsCard';
import { readFriendsCard, readFriendsCourts } from '../use-cases/friendsCard';

import { proposalKeys } from './proposalKeys';

/** Nothing asked: the key a line-up with an empty seat holds, which is never read. */
const NO_ASK: FriendsCardAsk = { kind: 'competitive', friendIds: [] };

/** The card for a full line-up — `ask` absent while a seat is empty, and nothing is asked. */
export function useFriendsCard(groupId: string, sport: Sport, ask: FriendsCardAsk | undefined) {
  return useQuery<FriendsCard, AppError>({
    queryKey: proposalKeys.friendsCard(groupId, sport, ask ?? NO_ASK),
    queryFn: ({ signal }) => readFriendsCard(groupId, sport, ask ?? NO_ASK, { signal }),
    enabled: ask !== undefined,
  });
}

/** *Find a court* — `enabled` once the sheet is open. */
export function useFriendsCourts(
  groupId: string,
  sport: Sport,
  friendIds: readonly string[],
  { enabled }: { readonly enabled: boolean },
) {
  return useQuery<FriendsCourts, AppError>({
    queryKey: proposalKeys.friendsCourts(groupId, sport, friendIds),
    queryFn: ({ signal }) => readFriendsCourts(groupId, sport, friendIds, { signal }),
    enabled,
  });
}
