/**
 * **A booked game's result** — today's game screen, over the game's details
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the mechanics §14.1: the result states are
 * *unchanged from today*).
 *
 * A booking opens an ordinary Game (#541), and its result is told and agreed exactly as any game's
 * is: `games`' `GameScreen`, at the Game the booking names. It is composed here with the score
 * leading and nothing in its three Classic slots — **no plan** (the booking is the plan), **no
 * card** (the details below it are the card) and **no fill** (a seat open on a booking is a rescue,
 * #557's) — and no court, because the details drew the forecast already. The Game is found off the
 * booking's own read, which the details have just made.
 */

import { GameScreen } from '@/features/games/types';

import { bookingReadState, useBooking } from '../hooks/useHome';

import { BookingAbsent } from './BookingAbsent';
import { HOME_GAME_COPY } from './homeCopy';

const COPY = HOME_GAME_COPY.details;

export interface BookedGameResultProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
}

export function BookedGameResult({ bookingId }: BookedGameResultProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;

  if (game === undefined) {
    return (
      <BookingAbsent
        read={bookingReadState(read)}
        gone={COPY.gone}
        waiting={COPY.reading}
        edges={['top']}
      />
    );
  }

  return (
    <GameScreen
      gameId={game.gameId}
      entryLead="the-score"
      card={null}
      court={null}
      plan={null}
      fill={null}
    />
  );
}
