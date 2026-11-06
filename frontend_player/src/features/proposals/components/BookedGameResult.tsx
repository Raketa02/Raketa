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
 *
 * **And the booking's facts the Game does not carry** ([#560](https://github.com/Raketa02/Raketa/issues/560),
 * [#658](https://github.com/Raketa02/Raketa/issues/658)): that it is booked, when its hour starts
 * and at which club — so the screen says who's here in the first half hour, and names the club when
 * a tap is made away from it — with the re-read of Home and these details, so the status, the badge
 * and the door under this screen follow a score or a tap at once.
 *
 * **And PLAYED WITH** ([#754](https://github.com/Raketa02/Raketa/issues/754); the friends screens
 * §3): the others on the game, each with where the reader stands with them, between the score and
 * the star card. The people are this booking's — its seats and its `played_with`, joined by
 * `playedWithOf` — and the card is `friends`', which this feature may not import, not even its
 * types (`friends` reads `proposals`' keys and Home, and a cycle is a defect), so **the route hands
 * the card in** (`playedWith`) and this builds what it is handed, in this feature's own words
 * (`PlayedWithInput`). A row's tap opens the record here, with the game's group and sport, as
 * Members' does; a pill waits for the booking to read again, and the record closing reads it again
 * too, since what was pressed on it moves the row it was opened from. **The screen is hidden behind
 * the record** while it is up (`behindOverlay`), the caller's half of a sheet's obligations.
 */

import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { GameScreen } from '@/features/games/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { playedWithOf, type PlayedWithPerson } from '../domain/home';
import { bookingReadState, useBooking, useRereadBooking } from '../hooks/useHome';

import { BookingAbsent } from './BookingAbsent';
import { HOME_GAME_COPY } from './homeCopy';

const COPY = HOME_GAME_COPY.details;

/** **What PLAYED WITH is drawn from** — built here off the booking, drawn by the card handed in. */
export interface PlayedWithInput {
  /** Everybody else on the game, each named off their seat with the reader's relation to them. */
  readonly people: readonly PlayedWithPerson[];
  readonly sport: Sport;
  /** The game's group, which a request asked from the card names. */
  readonly groupId: string;
  /** A tap on the rest of a row: their record, opened here. */
  readonly onPerson: (playerId: string) => void;
  /** The booking's re-read, which a pill awaits. */
  readonly reread: () => Promise<unknown>;
}

export interface BookedGameResultProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
  /** **PLAYED WITH** — `friends`' card, handed in by the route; this builds its input (#754). */
  readonly playedWith: (input: PlayedWithInput) => ReactNode;
}

export function BookedGameResult({ bookingId, playedWith }: BookedGameResultProps) {
  const read = useBooking(bookingId);
  const reread = useRereadBooking(bookingId);
  const game = read.data ?? undefined;
  /** Whose record is open from PLAYED WITH — route-local, as Members' is. */
  const [reading, setReading] = useState<string>();

  // A booking with no Game — one payment still awaited — has no result: the one sentence.
  if (game?.gameId === undefined) {
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
    <>
      <View style={s.root} {...behindOverlay(reading !== undefined)}>
        <GameScreen
          gameId={game.gameId}
          entryLead="the-score"
          card={null}
          court={null}
          plan={null}
          fill={null}
          booked={{
            reread,
            startsAt: game.startsAt,
            ...(game.where.name === undefined ? {} : { club: game.where.name }),
          }}
          playedWith={playedWith({
            people: playedWithOf(game),
            sport: game.sport,
            groupId: game.groupId,
            onPerson: setReading,
            reread: () => read.refetch(),
          })}
        />
      </View>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => {
            setReading(undefined);
            void read.refetch();
          }}
          subject={{ kind: 'player', playerId: reading }}
          sport={game.sport}
          groupId={game.groupId}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
});
