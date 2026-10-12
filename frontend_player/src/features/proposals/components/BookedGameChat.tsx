/**
 * **A booked game's chat** — the room, opened from the game's details
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.4; the mechanics §14.3) or
 * straight over Home from the bubble on its card (Q100, [#619](https://github.com/Raketa02/Raketa/issues/619)).
 *
 * `conversations`' own screen, the header's second line the booking's word. The room is found by
 * the join keyed by the booking (`useBookingRoom`, #577) — the route's own id. From the details the
 * room and the booking they just read are both answered from the cache on the way in; from Home's
 * bubble the room is, and the booking is read behind the spinner. *Back* is whichever screen opened
 * it, by the stack.
 *
 * While the booking or the room is still being found the screen says so with the muted spinner,
 * offline that it resumes, and a refused read why, with the retry (`BookingAbsent`); a room the list
 * does not hold — the game's chat closed, or not open yet — is one sentence and the back chevron.
 */

import { ConversationScreen, useBookingRoom } from '@/features/conversations/types';

import { shownStatus } from '../domain/home';
import { bookingReadState, useBooking } from '../hooks/useHome';

import { BookingAbsent } from './BookingAbsent';
import { HOME_GAME_COPY } from './homeCopy';

const COPY = HOME_GAME_COPY;

export interface BookedGameChatProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
}

export function BookedGameChat({ bookingId }: BookedGameChatProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;
  const room = useBookingRoom(bookingId);

  if (game !== undefined && room.conversationId !== undefined) {
    return (
      <ConversationScreen
        conversationId={room.conversationId}
        gameState={COPY.statusInLine[shownStatus(game)]}
      />
    );
  }

  // The booking first, then the rooms: a read of either still on its way, held offline or refused
  // is said as such, and only a list that answered without the room says the chat is not open.
  const state =
    game === undefined
      ? bookingReadState(read)
      : {
          paused: room.paused,
          pending: !room.listed && room.error === null && !room.paused,
          error: room.error,
          retry: room.retry,
        };
  return (
    <BookingAbsent
      read={state}
      gone={game === undefined ? COPY.details.gone : COPY.details.noRoom}
      waiting={game === undefined ? COPY.details.reading : COPY.details.findingRoom}
      edges={['top', 'bottom']}
    />
  );
}
