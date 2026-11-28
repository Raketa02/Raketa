/**
 * **You › Friends** — `friends`' page from You, composed with what it may not import
 * ([#754](https://github.com/Rakieta02/Rakieta/issues/754); the friends screens §4.1, §5).
 *
 * The page and its three tabs are `friends`'. **The shell hands in the three things that are other
 * features'**, as it does for Home's request cards: the record a row opens (`player_record`'s, which
 * draws `friends`' record button), and the Add friends sheet's group tiles and its door into Members
 * (`groups'`, which draws `friends`' pills on Members). Either feature importing the other back would
 * be a dependency both ways.
 *
 * **The record is a sibling of the page, never inside it** (`YouScreen`'s note): `behindOverlay`
 * hides everything inside the element carrying it. Every friends write re-reads the page's lists,
 * so an act on the record is on the tab under it when the sheet closes.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { FriendsPage, FriendsTabs } from '@/features/friends/types';
import { MyGroupMonogram, groupMembersRoute } from '@/features/groups/types';
import { PlayerRecordSheet } from '@/features/player_record/types';

export function YouFriendsScreen() {
  const router = useRouter();
  const [reading, setReading] = useState<string>();

  return (
    <>
      <FriendsPage
        onBack={router.back}
        behind={reading !== undefined}
        groups={{
          tile: (groupId) => <MyGroupMonogram groupId={groupId} size="card" />,
          open: (groupId) => router.push(groupMembersRoute(groupId)),
        }}
      >
        <FriendsTabs onPerson={setReading} />
      </FriendsPage>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading }}
        />
      )}
    </>
  );
}
