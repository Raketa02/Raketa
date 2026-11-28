/**
 * **One view of the ranking, as the page draws it** ([#776](https://github.com/Rakieta02/Rakieta/issues/776),
 * [#777](https://github.com/Rakieta02/Rakieta/issues/777)) — what General's pages (`useGeneral`) and the
 * Friends table (`useFriendsTable`) each hand the page, so the card, the podium, the list, the
 * *You · 4th* button, the pull and the refusals are drawn once for both.
 *
 * General is read in pages of 50, from the top or around the reader; Friends is read whole, so its
 * ends ask for nothing, it has no page to refuse, and its button only ever scrolls.
 */

import type { AppError } from '@/shared/errors';

import type { RankedRow, Ranking } from '../domain/ranking';

/** A page of the list that could not be read — said where it was asked for, with its Try again. */
export interface PageFailure {
  readonly error: AppError;
  readonly retry: () => void;
}

/** **The jump** — the reader's place, while they are listed and, in General, shown. */
export interface Jump {
  readonly place: number;
  /**
   * Read the page around the reader — for a row the list has not read yet. **Absent in Friends**,
   * which is drawn whole: the reader's row is always on hand to scroll to.
   */
  readonly toMe?: () => void;
  readonly failure: PageFailure | undefined;
}

/** Which window of the list is drawn — a new one is a new list, centred on the reader. */
export type ListWindow = 'fromTheTop' | 'aroundMe';

export interface RankingRead {
  /** The main read — the card, the podium, how many are listed. `undefined` until it lands. */
  readonly ranking: Ranking | undefined;
  /** The main read's own failure, while there is nothing to draw. */
  readonly error: AppError | null;
  /** The main read is waiting for a connection. */
  readonly paused: boolean;
  readonly window: ListWindow;
  /** The rows drawn, best first. */
  readonly rows: readonly RankedRow[];
  /** The rows start at place 1 — the card and the podium stand above them. */
  readonly atTheTop: boolean;
  readonly loadEarlier: () => void;
  readonly loadLater: () => void;
  /** The page above, and the page below, refused. */
  readonly earlierFailure: PageFailure | undefined;
  readonly laterFailure: PageFailure | undefined;
  /** Absent while the reader isn't listed: no button. */
  readonly jump: Jump | undefined;
  /** A pull: everything drawn, read again. Settles once every read has landed, refused or not. */
  readonly reread: () => Promise<unknown>;
  readonly retry: () => void;
}
