/**
 * **A friends game's seats, on its details** ([#759](https://github.com/Raketa02/Raketa/issues/759);
 * the friends screens §9, designed, no mock; the words §29.8) — one row per seat, the sender's
 * first, under the game's facts on its dark ground:
 *
 * ```
 * SEATS
 * tomek.k     In
 * You         In
 * magda.p     waiting · 21 h 00 left
 * ania.k      can't make it
 * ```
 *
 * Every state is a word (the design system's *every state carries a word*), and the waiting seat's
 * time counts down on the read's clock — the deck ribbon's countdown, cited — until it reads
 * *didn't answer*. One element per row, named by the person and their state.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { SeatShown } from '../domain/friendsGame';

import { tileName } from './deckPresentation';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { seatStateWords } from './friendsGamePresentation';

const COPY = FRIENDS_GAME_COPY.seats;

export interface FriendsSeatsProps {
  readonly seats: readonly SeatShown[];
  /** The read's clock — a waiting seat's time left. */
  readonly now: number;
}

export function FriendsSeats({ seats, now }: FriendsSeatsProps) {
  if (seats.length === 0) return null;
  return (
    <View style={s.seats} testID="friends-seats">
      <Text style={s.heading} accessibilityRole="header">
        {COPY.heading}
      </Text>
      {seats.map((seat) => {
        const name = seat.person.isYou ? COPY.you : tileName(seat.person);
        const state = seatStateWords(seat, now);
        return (
          <View
            key={seat.person.playerId}
            style={s.row}
            accessible
            accessibilityLabel={`${name}, ${state}`}
            testID={`seat-state-${seat.person.playerId}`}
          >
            <Text style={s.name} numberOfLines={1}>
              {name}
            </Text>
            <Text style={[s.state, seat.state === 'IN' ? s.in : undefined]}>{state}</Text>
          </View>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  seats: { gap: theme.space.xs },
  heading: { ...theme.type.eyebrow, color: theme.color.onDarkEyebrow, textTransform: 'uppercase' },
  row: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.sm },
  name: { ...theme.type.rlLabel, color: theme.color.surface, flexShrink: 1 },
  state: { ...theme.type.tiny, color: theme.color.onDarkTiny, marginLeft: 'auto' },
  in: { color: theme.color.surface },
});
