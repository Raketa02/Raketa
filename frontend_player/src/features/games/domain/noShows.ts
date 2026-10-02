/**
 * **Marking somebody as not coming** — who a player may say *Kuba didn't come* about, where the
 * result of a **booked** game is entered ([#560](https://github.com/Raketa02/Raketa/issues/560); the
 * Games & Fill in mechanics §15.3; the backend's #547).
 *
 * A row per other player on the court, in its order. **A player the club's desk checked in keeps
 * their row and cannot be marked**: the scan is evidence they were there, and the row saying so is
 * what tells the reader why there is nothing to press. The rows are offered where the entry is —
 * nobody has said the game happened, the court is whole — and go on being offered while a report's
 * day runs, so the second player who did not come to a doubles game can be marked after the first.
 * **They go for a player who was marked themselves**: their answer is the dispute, and the backend
 * refuses them a report (`you_were_reported_as_a_no_show`).
 *
 * **Which game is booked is not this feature's to know.** `GET /games` does not say, and nor does it
 * carry the desk's check-ins; both are the booking's, so whoever composes a booked game's screen
 * hands the check-ins in, and a Classic game — which has no hour anybody could fail to come to —
 * has no rows because nobody hands any in.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import type { Game } from './game';
import { resultArgument, whoIs } from './resultArgument';

/** One other player on the court, as the *didn't come* block draws them. */
export interface NoShowRow {
  readonly playerId: string;
  /** The whole name, or `?` where `users` no longer has the account. Never *you*. */
  readonly who: NamedPlayer;
  /** The club's desk checked them in: drawn, and never markable. */
  readonly checkedIn: boolean;
}

/**
 * **The rows of the block, or none where it is not drawn** — `checkedIn` is the desk's word, by
 * player id, handed in by the composer of a booked game's screen.
 */
export function noShowRows(
  game: Game,
  reader: string,
  checkedIn: readonly string[],
): readonly NoShowRow[] {
  const argument = resultArgument(game, reader);
  const offered =
    (argument.kind === 'awaiting-entry' && !argument.seatOpen) ||
    (argument.kind === 'no-show-reported' && argument.yours === undefined);
  if (!offered) return [];

  const marked = new Set(game.noShows.map((report) => report.playerId));
  return game.seats.flatMap((seat) =>
    seat.playerId === undefined || seat.playerId === reader || marked.has(seat.playerId)
      ? []
      : [
          {
            playerId: seat.playerId,
            who: whoIs(game, reader, seat.playerId),
            checkedIn: checkedIn.includes(seat.playerId),
          },
        ],
  );
}
