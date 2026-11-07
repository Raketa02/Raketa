/**
 * **The friends card and *Find a court*, read** (#757) — pass-throughs, honestly: the sides, the
 * forecast, the court proposed and who is busy are the server's (`ReadFriendsLineUp`, #750), and
 * nothing about them is decided on the way in. The uniform-strict escape hatch.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { getFriendsCard, getFriendsCourts, type Cancellable } from '../api/proposalsApi';
import type { FriendsCard, FriendsCardAsk, FriendsCourts } from '../domain/friendsCard';
import {
  toFriendsCard,
  toFriendsCardQuery,
  toFriendsCourts,
  toFriendsCourtsQuery,
} from '../mappers/friendsCardMappers';

export async function readFriendsCard(
  groupId: string,
  sport: Sport,
  ask: FriendsCardAsk,
  options: Cancellable = {},
): Promise<FriendsCard> {
  return toFriendsCard(await getFriendsCard(groupId, toFriendsCardQuery(sport, ask), options));
}

export async function readFriendsCourts(
  groupId: string,
  sport: Sport,
  friendIds: readonly string[],
  options: Cancellable = {},
): Promise<FriendsCourts> {
  return toFriendsCourts(
    await getFriendsCourts(groupId, toFriendsCourtsQuery(sport, friendIds), options),
  );
}
