/**
 * **A friends game's seats, on its details** ([#759](https://github.com/Rakieta02/Rakieta/issues/759);
 * the friends screens §9, designed, no mock; the words §29.8) — one row per seat, the sender's
 * first, under the game's facts on its dark ground:
 *
 * ```
 * SEATS
 * tomek.k     In
 * You         In
 * magda.p     waiting · 21 h 00 left
 * ania.k      can't make it
 *    karol.t invited · 20 h 00 left            an invitation into the empty seat (#760)
 *    [ Invite a friend ]  [ Open to Ogrody ]   what the reader may do with it (#760)
 * ```
 *
 * Every state is a word (the design system's *every state carries a word*), and the waiting seat's
 * time counts down on the read's clock — the deck ribbon's countdown, cited — until it reads
 * *didn't answer*. One element per row, named by the person and their state.
 *
 * **An empty seat** ([#760](https://github.com/Rakieta02/Rakieta/issues/760); the mechanics §10,
 * §11.3) — *can't make it*, *didn't answer*, *empty*, *Seat open* — draws under its row the friends
 * invited into it and still to answer, and the two acts the read gives the reader, taken away at
 * the instants the read's clock passes (`seatActionsAt`): ***Invite a friend***, anyone In's,
 * which opens the picker with one seat; and ***Open to {group}***, the sender's before the cut-off,
 * behind its confirmation (`OpenTheSeat`). Both are the dark card's own button (`onDark`), and
 * each is named aloud with whose seat it is, since the details may hold two empty seats. They are
 * siblings of the row, never inside it: the row is one read-only element.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import { seatActionsAt, type SeatShown } from '../domain/friendsGame';

import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import {
  faceName,
  seatActionSpoken,
  seatInvitationWords,
  seatSpoken,
  seatStateWords,
} from './friendsGamePresentation';
import { OpenTheSeat } from './OpenTheSeat';

const COPY = FRIENDS_GAME_COPY.seats;

/** What an empty seat's two acts need — the game's, from the details. */
export interface SeatFilling {
  readonly bookingId: string;
  /** The club's cut-off still ahead on the read's clock, or none once it has come. */
  readonly cutOff: string | undefined;
  readonly startsAt: string;
  /** The group a seat opens to — absent for one the app cannot name (*the group*). */
  readonly group: string | undefined;
  /** What a stranger who takes the seat pays. */
  readonly shareGrosze: number;
  /** *Invite a friend* on the seat named `seatOf` — the picker with one seat. */
  readonly onInvite: (seatOf: string) => void;
}

export interface FriendsSeatsProps {
  readonly seats: readonly SeatShown[];
  /** The read's clock — a waiting seat's time left, an invitation's, and the acts' instants. */
  readonly now: number;
  /** An empty seat's acts. Without it — a reader outside the game — no seat offers any. */
  readonly filling?: SeatFilling;
}

export function FriendsSeats({ seats, now, filling }: FriendsSeatsProps) {
  if (seats.length === 0) return null;
  return (
    <View style={s.seats} testID="friends-seats">
      <Text style={s.heading} accessibilityRole="header">
        {COPY.heading}
      </Text>
      {seats.map((seat) => {
        const state = seatStateWords(seat, now);
        return (
          <View key={seat.person.playerId} style={s.seat}>
            <View
              style={s.row}
              accessible
              accessibilityLabel={seatSpoken(seat, now)}
              testID={`seat-state-${seat.person.playerId}`}
            >
              <Text style={s.name} numberOfLines={1}>
                {faceName(seat.person)}
              </Text>
              <Text style={[s.state, seat.state === 'IN' ? s.in : undefined]}>{state}</Text>
            </View>
            {seat.invitations.map((invitation) => (
              <Text key={invitation.playerId} style={s.invited}>
                {seatInvitationWords(invitation, now)}
              </Text>
            ))}
            {filling === undefined ? null : (
              <EmptySeatActs seat={seat} now={now} filling={filling} />
            )}
          </View>
        );
      })}
    </View>
  );
}

function EmptySeatActs({
  seat,
  now,
  filling,
}: {
  readonly seat: SeatShown;
  readonly now: number;
  readonly filling: SeatFilling;
}) {
  const acts = seatActionsAt(seat, { now, cutOff: filling.cutOff, startsAt: filling.startsAt });
  const { seatOf } = seat;
  if (seatOf === undefined || (!acts.invite && !acts.open)) return null;
  return (
    <View style={s.acts}>
      {acts.invite ? (
        <Button
          label={COPY.invite}
          accessibilityLabel={seatActionSpoken(COPY.invite, seat.person)}
          variant="onDark"
          size="sm"
          onPress={() => filling.onInvite(seatOf)}
        />
      ) : null}
      {acts.open ? (
        <OpenTheSeat
          bookingId={filling.bookingId}
          seatOf={seatOf}
          person={seat.person}
          group={filling.group}
          shareGrosze={filling.shareGrosze}
        />
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  seats: { gap: theme.space.xs },
  heading: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow, textTransform: 'uppercase' },
  seat: { gap: theme.space.xs },
  row: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.sm },
  name: { ...theme.type.rlLabel, color: theme.color.surface, flexShrink: 1 },
  state: { ...theme.type.tiny, color: theme.color.onDarkTiny, marginLeft: 'auto' },
  in: { color: theme.color.surface },
  // Under the seat's name: the invitation is the seat's, and its acts beneath it.
  invited: { ...theme.type.tiny, ...theme.tabular, color: theme.color.onDarkTiny },
  acts: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});
