/**
 * **The Friends page as a picker**, for one sport of one group — pushed over the group's page from
 * an empty seat on its court or from *+ Friends*, so *back* is the court
 * ([#757](https://github.com/Raketa02/Raketa/issues/757); the friends screens §4.2; friends 3, 6).
 *
 * **`friends`' page, composed here** with what it may not import: the frame (`FriendsPage` — back,
 * *Friends*, **+ Add friends** and its sheet, with this feature's group tiles and Members as its
 * doors) holding the picker (`FriendsPicker`) and, pinned at its foot, **Done**. No tabs, and no
 * eyebrow: friends 3's header, as from You.
 *
 * **The picks start as the court's seats** and are this screen's own until **Done**, which seats
 * them (`seatPicks`) — those still picked keep their seats, the rest fill the empty ones, the card
 * is asked for the evenest sides — and goes back to the court. *Back* without Done leaves the court
 * as it was. **Somebody seated who is no longer a friend** is neither counted nor kept: the list
 * (the picker's own read) is what a pick is held to, so their seat is free to fill.
 *
 * **No friends yet**: the group's empty card (play 55) — *Nobody you know here yet*, who would show
 * up here, and the link's two doors — the picker's own empty state, handed in. The group is the
 * page's read, already in the cache; a failure to read it is the page's own block, with the page's
 * words.
 */

import { router } from 'expo-router';
import { useMemo, useState } from 'react';

import { FriendsPage, FriendsPicker, FRIENDS_COPY, useFriendsIn } from '@/features/friends/types';
import { codeMessage } from '@/shared/errors';
import { Button, courtSeatCount } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  emptyLineUp,
  seatedOf,
  seatPicks,
  togglePick,
  withoutStrangers,
} from '../domain/friendsLineUp';
import { useGroup } from '../hooks/useGroups';
import { lineUpKey, useFriendsGame } from '../store/friendsGame.store';

import { groupMembersRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { friendsLine } from './groupsPresentation';
import { LinkCard } from './LinkCard';
import { MyGroupMonogram } from './MyGroupMonogram';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.friends;

export function FriendsScreen({
  groupId,
  sport,
}: {
  readonly groupId: string;
  readonly sport: Sport;
}) {
  const read = useGroup(groupId);
  const group = read.data;
  const stored = useFriendsGame((state) => state.lineUps[lineUpKey(groupId, sport)]);
  const put = useFriendsGame((state) => state.put);

  const seats = courtSeatCount(sport) - 1;
  // Somebody seated who is no longer a friend holds no seat here — not counted, not kept on Done.
  const friends = useFriendsIn(sport).data;
  const stillFriends = useMemo(
    () => (friends === undefined ? undefined : new Set(friends.map((one) => one.playerId))),
    [friends],
  );
  const lineUp = withoutStrangers(stored ?? emptyLineUp(seats), stillFriends);
  const [chosen, setChosen] = useState<readonly string[]>(() => seatedOf(lineUp.seats));
  const picked = chosen.filter((one) => stillFriends === undefined || stillFriends.has(one));

  const toggle = (playerId: string) => setChosen(togglePick(picked, playerId, seats));

  const done = () => {
    put(groupId, sport, seatPicks(lineUp, picked));
    router.back();
  };

  return (
    <FriendsPage
      onBack={() => router.back()}
      groups={{
        tile: (id) => <MyGroupMonogram groupId={id} size="card" />,
        open: (id) => router.push(groupMembersRoute(id)),
      }}
      action={<Button label={FRIENDS_COPY.picker.done} size="lg" onPress={done} />}
    >
      <FriendsPicker
        groupId={groupId}
        sport={sport}
        picked={picked}
        onToggle={toggle}
        seats={seats}
        empty={
          group !== undefined ? (
            <LinkCard group={group} headline={COPY.nobody} line={friendsLine(group.name)} />
          ) : read.error !== null ? (
            <ReadFailure
              error={read.error}
              message={codeMessage(GROUPS_COPY.group.refused, read.error)}
              onRetry={() => void read.refetch()}
            />
          ) : null
        }
      />
    </FriendsPage>
  );
}
