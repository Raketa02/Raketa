/**
 * **A live yes** — a yes of the reader's on a game that has not filled, across every group (You ›
 * Payments' *LIVE YESES*, the screens A7.3; mock 48;
 * [#554](https://github.com/Raketa02/Raketa/issues/554)).
 *
 * The server's read (`ReadLiveYeses`, #539) lists them soonest game first and drops a game past its
 * book-by, whether or not its expiry has been recorded — so nothing here re-derives which yeses are
 * live. There is no cap on how many (removed 2026-10-05).
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from './deck';

/**
 * One yes still waiting for its game to fill, with what it would charge — the card's own fields,
 * named as the card names them: `deadline` is the game's book-by.
 */
export interface LiveYes extends Pick<
  DeckCard,
  'proposalId' | 'kind' | 'startsAt' | 'club' | 'shareGrosze' | 'deadline' | 'indoor'
> {
  /** The group the game was dealt in — its pool is filed under the group's id. */
  readonly groupId: string;
  readonly sport: Sport;
}

/** The whole list. */
export interface LiveYeses {
  readonly yeses: readonly LiveYes[];
}
