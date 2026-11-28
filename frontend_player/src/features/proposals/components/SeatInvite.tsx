/**
 * ***Invite a friend*** **into an empty seat** — this feature's half of the picker with one seat
 * ([#760](https://github.com/Rakieta02/Rakieta/issues/760), over #752's route; the friends screens §9;
 * the mechanics §10.1, §10.3, §11.3). The page and the picker are `friends`', which reads this
 * feature, so the shell composes them around these three:
 *
 * - **`SeatInvite`** — the game read, as the details read it (one cache): while it is absent the
 *   booking's own four states (`BookingAbsent`), and once it is there, what the picker needs
 *   (`SeatToInvite`) handed to the composer — the group and sport whose friends it lists, and
 *   everybody already on the game, whom it leaves out.
 * - **`InviteOrder`** — the order pinned at the page's foot: ***Invite piotr.s*** once a friend is
 *   picked, greyed *Invite a friend* before. Done, back to the game with the toast. **A refusal
 *   about the friend** — on the game already, no friend any more, no Level, a block with somebody on
 *   it (named nobody), a game at that hour, a full week — is said above the order, the pick still
 *   there to change; **a refusal that leaves no seat** — taken first, the game off or under way — is
 *   the toast, and back to the game, which is read again.
 * - **`NobodyToInvite`** — the picker's empty state: every friend is on the game already, or there
 *   is none.
 *
 * **Not retried**, as no write is; the busy order is what keeps a second press from asking twice,
 * and the server refuses a second invitation of the same friend `already_on_the_game`.
 */

import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { sportInLine } from '@/features/onboarding/types';
import { showToast } from '@/shared/store/toast.store';
import { Button, Note, theme } from '@/shared/ui';

import { seatToInviteOf, seatWriteRefusalOf, type SeatToInvite } from '../domain/friendsGame';
import { useInviteIntoASeat } from '../hooks/useFriendsGameWrites';
import { bookingReadState, useBooking } from '../hooks/useHome';

import { BookingAbsent } from './BookingAbsent';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { inviteLabel, inviteRefusal, invitedToast } from './friendsGamePresentation';
import { HOME_GAME_COPY } from './homeCopy';

export interface SeatInviteProps {
  readonly bookingId: string;
  /** The empty seat *Invite a friend* was pressed on. */
  readonly seatOf: string;
  /** The page, once the game is read. */
  readonly children: (seat: SeatToInvite) => ReactNode;
}

export function SeatInvite({ bookingId, seatOf, children }: SeatInviteProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;
  if (game === undefined) {
    return (
      <BookingAbsent
        read={bookingReadState(read)}
        gone={HOME_GAME_COPY.details.gone}
        waiting={HOME_GAME_COPY.details.reading}
        edges={['top']}
      />
    );
  }
  return <>{children(seatToInviteOf(game, seatOf))}</>;
}

/** The friend picked — the order names them, and a refusal does. */
export interface FriendPicked {
  readonly playerId: string;
  readonly nickname: string;
}

export interface InviteOrderProps {
  readonly seat: SeatToInvite;
  /** Nobody picked yet: the order is greyed. */
  readonly friend: FriendPicked | undefined;
  /** Invited, or no seat left to invite into — back to the game. */
  readonly onDone: () => void;
}

export function InviteOrder({ seat, friend, onDone }: InviteOrderProps) {
  const invite = useInviteIntoASeat(seat.bookingId, seat.seatOf);
  // A refusal is about the friend it was said of: picking another takes it away.
  const [refused, setRefused] = useState<{ readonly of: string; readonly words: string }>();
  const refusal = refused !== undefined && refused.of === friend?.playerId ? refused : undefined;

  return (
    <View style={s.order}>
      {refusal === undefined ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {refusal.words}
        </Note>
      )}
      <Button
        label={inviteLabel(friend?.nickname)}
        size="lg"
        disabled={friend === undefined}
        busy={invite.isPending}
        busyLabel={FRIENDS_GAME_COPY.invite.inviting}
        onPress={() => {
          if (friend === undefined || invite.isPending) return;
          setRefused(undefined);
          invite.mutate(friend.playerId, {
            onSuccess: () => {
              showToast({ message: invitedToast(friend.nickname), tone: 'ok' });
              onDone();
            },
            onError: (error) => {
              const words = inviteRefusal(error, {
                nickname: friend.nickname,
                sport: sportInLine(seat.sport),
                startsAt: seat.startsAt,
              });
              if (seatWriteRefusalOf(error.code) === 'gone') {
                showToast({ message: words, tone: 'bad' });
                onDone();
              } else {
                setRefused({ of: friend.playerId, words });
              }
            },
          });
        }}
      />
    </View>
  );
}

/** The picker with nobody left to invite — everyone is on the game already, or there is none. */
export function NobodyToInvite() {
  return <Note variant="info">{FRIENDS_GAME_COPY.invite.nobody}</Note>;
}

const s = StyleSheet.create({
  order: { gap: theme.space.sm },
});
