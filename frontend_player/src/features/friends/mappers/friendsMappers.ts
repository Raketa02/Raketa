/**
 * **A request, onto the wire** (#753) — where it was asked from, the group and the sport the screen
 * showed. The relation the routes answer needs no mapping: it is spelled as the wire spells it, and
 * `wireVocabulary.ts` holds the two equal.
 *
 * **And the Friends page's three reads, off it** (#754): your friends, the requests one way, and
 * the groups you could add from. A `null` on the wire is a field left off, as every mapper here does
 * it, and a sport this build cannot name is left off with its Level — the app would have no word or
 * colour to draw it with.
 */

import { toSport, toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Friend, FriendRequest, FriendSport, GroupToAddFrom } from '../domain/friendList';
import type { FriendLink } from '../domain/friendLink';
import type { AskedWhere } from '../domain/friendship';

type Schemas = components['schemas'];

/** `POST /friends/requests`'s body — the group and the sport only where the screen showed them. */
export function toAskRequest(
  playerId: string,
  where: AskedWhere,
): Schemas['AskToBeFriendsRequest'] {
  return {
    player_id: playerId,
    made_from: where.from,
    ...(where.groupId === undefined ? {} : { group_id: where.groupId }),
    ...(where.sport === undefined ? {} : { sport: toWireSport(where.sport) }),
  };
}

/** One friend: the face, the whole nickname, and every sport this build can name with its Level. */
export function toFriend(wire: Schemas['FriendSchema']): Friend {
  return {
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    sports: wire.sports.flatMap((served): FriendSport[] => {
      const sport = toSport(served.sport);
      return sport === undefined ? [] : [{ sport, level: served.level, band: served.band }];
    }),
    askedIn: wire.level_asked_in.flatMap((served) => {
      const sport = toSport(served);
      return sport === undefined ? [] : [sport];
    }),
  };
}

/**
 * `POST /friends/{id}/level-asks`'s body (#758) — the picker's sport, the Level they are asked to
 * get, and the group whose Friends tab the picker is on, whose picker their answer opens.
 */
export function toLevelAskRequest(sport: Sport, groupId: string): Schemas['AskForALevelRequest'] {
  return { sport: toWireSport(sport), group_id: groupId };
}

/** One open request — *Asked you*'s or *You asked*'s. */
export function toFriendRequest(wire: Schemas['FriendRequestSchema']): FriendRequest {
  return {
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    setAside: wire.set_aside,
  };
}

/** One of your groups in the Add friends sheet. */
export function toGroupToAddFrom(wire: Schemas['GroupToAddFromSchema']): GroupToAddFrom {
  return {
    groupId: wire.group_id,
    name: wire.name,
    memberCount: wire.member_count,
    toAdd: wire.to_add,
  };
}

/** **Your friend link** (#756) — its code and the whole address, as the server prints it. */
export function toFriendLink(wire: Schemas['FriendLinkResponse']): FriendLink {
  return { code: wire.code, link: wire.link };
}
