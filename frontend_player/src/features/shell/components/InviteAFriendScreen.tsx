/**
 * ***Invite a friend*** **into an empty seat** — `friends`' page as a picker with one seat, pushed
 * over a booked friends game's details, so *back* is the game
 * ([#760](https://github.com/Raketa02/Raketa/issues/760); the friends screens §9).
 *
 * **Composed here because it is three features'**: the game and the order are `proposals'`
 * (`SeatInvite`, `InviteOrder`), the page and the picker `friends'` (`FriendsPage`,
 * `FriendsPicker`), and the Add friends sheet's group tiles and door into Members `groups'`.
 * `friends` and `groups` each read `proposals`, so `proposals` cannot draw either — the shell does,
 * as it composes You › Friends.
 *
 * **One seat**: a pick replaces the last, and the rest grey out while one is picked, as a full
 * court greys them. **Everybody already on the game is left out** of the list (`onTheGame`), and the
 * order names the friend picked: *Invite piotr.s*. The pick is this screen's own and goes with it.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { FriendsPage, FriendsPicker, useFriendsIn } from '@/features/friends/types';
import { MyGroupMonogram, groupMembersRoute } from '@/features/groups/types';
import {
  InviteOrder,
  NobodyToInvite,
  SeatInvite,
  type SeatToInvite,
} from '@/features/proposals/types';

export function InviteAFriendScreen({
  bookingId,
  seatOf,
}: {
  readonly bookingId: string;
  readonly seatOf: string;
}) {
  return (
    <SeatInvite bookingId={bookingId} seatOf={seatOf}>
      {(seat) => <Picking seat={seat} />}
    </SeatInvite>
  );
}

function Picking({ seat }: { readonly seat: SeatToInvite }) {
  const router = useRouter();
  const friends = useFriendsIn(seat.sport).data;
  const [picked, setPicked] = useState<string>();
  const nickname = friends?.find((one) => one.playerId === picked)?.nickname;

  return (
    <FriendsPage
      onBack={router.back}
      groups={{
        tile: (groupId) => <MyGroupMonogram groupId={groupId} size="card" />,
        open: (groupId) => router.push(groupMembersRoute(groupId)),
      }}
      action={
        <InviteOrder
          seat={seat}
          friend={
            picked === undefined || nickname === undefined
              ? undefined
              : { playerId: picked, nickname }
          }
          onDone={router.back}
        />
      }
    >
      <FriendsPicker
        groupId={seat.groupId}
        sport={seat.sport}
        picked={picked === undefined ? [] : [picked]}
        onToggle={(playerId) => setPicked((now) => (now === playerId ? undefined : playerId))}
        seats={1}
        leaveOut={seat.onTheGame}
        empty={<NobodyToInvite />}
      />
    </FriendsPage>
  );
}
