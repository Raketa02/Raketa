/**
 * **Friends, on the You tab** — its title, how many friends and who waits on an answer in one line —
 * *3 friends · 1 asked you*, *1 friend*, *No friends yet* — and the door to You › Friends
 * ([#754](https://github.com/Rakieta02/Rakieta/issues/754), PRD #743 story 34; the friends screens
 * §4.1).
 *
 * **The line is the page's own two reads** — your friends and *Asked you* — so an accept there is on
 * the row the moment the player comes back, and **it waits for both**: a line that read *3 friends*
 * and then grew *· 1 asked you* would say two things in a second. A read that failed says so on the
 * row, in the recovery register every row on the tab uses.
 */

import { useRouter } from 'expo-router';

import { liveLine } from '@/shared/errors';
import { DoorRow, type DoorRowProps } from '@/shared/ui';

import { useFriendRequests, useFriends } from '../hooks/useFriendLists';

import { FRIENDS_COPY, friendsRowLine } from './friendsCopy';
import { YOU_FRIENDS_ROUTE } from './friendRoutes';

export type FriendsRowProps = Pick<DoorRowProps, 'divided'>;

export function FriendsRow({ divided }: FriendsRowProps) {
  const router = useRouter();
  const friends = useFriends();
  const askedYou = useFriendRequests('ASKED_YOU');

  const both =
    friends.data === undefined || askedYou.data === undefined
      ? undefined
      : { friends: friends.data.length, askedYou: askedYou.data.length };

  return (
    <DoorRow
      glyph="users"
      title={FRIENDS_COPY.row.title}
      line={liveLine({ data: both, error: friends.error ?? askedYou.error }, (counts) =>
        friendsRowLine(counts.friends, counts.askedYou),
      )}
      divided={divided}
      onPress={() => router.push(YOU_FRIENDS_ROUTE)}
    />
  );
}
