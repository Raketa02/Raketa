/**
 * **A booked game's chat** — the room, opened from the game's details and from nowhere else
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.4; the mechanics §14.3).
 *
 * `conversations`' own screen, the header's second line the booking's word. The room is found by the join keyed by the
 * game (`useGameRoom`) over the booking the details just read — both answered from the cache on the
 * way in — so the route carries only the booking's id, and *back* is the details by the stack.
 *
 * While the booking or the room is still being found the screen says so with the muted spinner,
 * offline that it resumes, and a refused read why, with the retry (`BookingAbsent`); a room the list
 * does not hold — the game's chat closed, or not open yet — is one sentence and the back chevron.
 */

import { ConversationScreen, useGameRoom } from '@/features/conversations/types';

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
  const room = useGameRoom(game?.gameId);

  if (game !== undefined && room.conversationId !== undefined) {
    return (
      <ConversationScreen
        conversationId={room.conversationId}
        gameState={COPY.statusInLine[game.status]}
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
