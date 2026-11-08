/**
 * **A ranking, as the page draws it** ([#775](https://github.com/Raketa02/Raketa/issues/775);
 * [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md); the rankings
 * mechanics and screens) — the reader's place card, the podium and the rows, for one sport and one
 * view.
 *
 * **Everything here is the server's answer, carried.** The order, every place, *of N*, the chip, the
 * gap and how many wins close it are worked out by the backend — the win count reads the rating
 * engine's own update rule, so nobody else may compute it (the mechanics §7.2). What is this
 * feature's own is below the types: which sports the pill offers, which sport the page opens on, and
 * how three rows stand on the podium.
 */

import type { GameResult } from '@/shared/vocabulary/gameResult';
import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import type { RankingView } from './vocabulary';

/**
 * **Places moved in the last 7 days** (the mechanics §6): *▲ 2*, *▼ 1*, *—* or *New*. A count only
 * where there is one to say.
 */
export type Chip =
  | { readonly kind: 'UP'; readonly places: number }
  | { readonly kind: 'DOWN'; readonly places: number }
  | { readonly kind: 'SAME' }
  | { readonly kind: 'NEW' };

/** **One listed player the reader can see** (the screens §5.2). */
export interface RankedRow {
  /** The true place — a hidden or blocked row leaves a gap, so places may skip a number. */
  readonly place: number;
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Omitted when they have no photograph: the face draws their poster. */
  readonly photoUrl?: string;
  /** The last five results with a winner in the sport, **oldest first**, never padded. */
  readonly form: readonly GameResult[];
  /** Absent only where the server sent one this build cannot read — nothing drawn, not a guess. */
  readonly chip?: Chip;
  readonly level: number;
  /** The reader's own row — it reads *You* and is tinted. */
  readonly isYou: boolean;
}

/** **The player just above the reader**, among the rows the reader can see (the mechanics §7). */
export interface PlayerAbove {
  readonly nickname: string;
  /** How far behind them the reader is, two decimals; `0` when tied. */
  readonly gap: number;
  /**
   * **How many even wins close the gap**: 1 is *one win closes it*, 2–5 *about n wins close it*.
   * Absent when more than five would, when one win moves no level, and when tied.
   */
  readonly wins?: number;
  /** Level with them, and they stand above on the tie rule: *Level with Ewa · one win puts you ahead*. */
  readonly tied: boolean;
}

/** **The player just below the reader** — *Zofia is 0,02 behind you*, or level with you at `0`. */
export interface PlayerBelow {
  readonly nickname: string;
  readonly gap: number;
}

/**
 * **The line under the fold** (the mechanics §7.1): *Top of the list* in first place, which is the
 * whole line; otherwise the part about the player above, then the part about the player below —
 * either absent where there is nobody the reader can see that way.
 */
export type GapLine =
  | { readonly kind: 'top' }
  | { readonly kind: 'between'; readonly above?: PlayerAbove; readonly below?: PlayerBelow };

/** **A place to show** — the card's left and right halves. */
export interface Placed {
  readonly place: number;
  /** How many are listed, hidden players and rows the reader can't see included. */
  readonly of: number;
  readonly level: number;
  /** Absent only where the server sent one this build cannot read — nothing drawn, not a guess. */
  readonly chip?: Chip;
}

/**
 * **The reader's place card** (the screens §4) — a place with its gap line, a place hidden from
 * General, or one of the not-listed cards in its stead.
 */
export type PlaceCard =
  | ({ readonly state: 'LISTED'; readonly gapLine: GapLine } & Placed)
  | ({ readonly state: 'HIDDEN' } & Placed)
  | {
      readonly state: 'NEEDS_RESULTS';
      /** The reader's results in the sport — the *2* of *2 of 5 games*. */
      readonly results: number;
      /** How many put a player on the view's list — 5 in General, 1 in Friends. */
      readonly resultsToEnter: number;
    }
  | {
      readonly state: 'NO_LEVEL';
      /** What a level then needs to be listed — 5 results in General, 1 in Friends. */
      readonly resultsToEnter: number;
    }
  | { readonly state: 'OFF_THE_LIST' }
  | { readonly state: 'JUST_YOU' }
  | { readonly state: 'NO_FRIEND_LISTED' };

/** **One read of the page** — `GET /rankings/{sport}?view=…`, for the sport the page asked for. */
export interface Ranking {
  readonly view: RankingView;
  /**
   * Absent where the server sent a card this build cannot read — a state it has never heard of, or a
   * place without its number — and then no card is drawn rather than a guess.
   */
  readonly card?: PlaceCard;
  /** How many are listed in the view and sport, the reader included — `0` is *Nobody ranked*. */
  readonly listed: number;
  /** The first three rows the reader sees — empty with fewer than three. */
  readonly podium: readonly RankedRow[];
  /** General's first page of 50, best first; Friends whole. */
  readonly rows: readonly RankedRow[];
  /**
   * **The cursor General's second page is read after** (#776) — opaque, handed back as it came.
   * Absent when the first page is the whole list, and always in Friends.
   */
  readonly next?: string;
}

/**
 * **A page of General** (#776; the screens §5.3) — 50 places of the list, the rows of them the reader
 * sees, best first, and the cursors either side: `previous` to read the page above, `next` the page
 * below, each absent at that end of the list. A page with rows the reader can't see holds fewer.
 */
export interface GeneralPage {
  readonly rows: readonly RankedRow[];
  readonly previous?: string;
  readonly next?: string;
}

/**
 * **Where a page of General is read from** — the main read's own first page, the page with the
 * reader in the middle (*You · 212th*), or the page below or above a cursor.
 */
export type PageAt =
  | { readonly at: 'top' }
  | { readonly at: 'aroundMe' }
  | { readonly at: 'after'; readonly cursor: string }
  | { readonly at: 'before'; readonly cursor: string };

/**
 * **General's pages, end to end** (#776). Each page is read against the order as it stands at that
 * read, so a row that moved past a cursor between two reads comes back on the next page that way. It
 * is drawn once, **where it already stands** — on the page nearest the one the window read first,
 * `first`, which is 0 from the top and the reader's own page after a jump — so nothing the reader is
 * looking at moves under them. A pull reads every page again, and puts it right.
 */
export function joinPages(
  pages: readonly Pick<GeneralPage, 'rows'>[],
  first = 0,
): readonly RankedRow[] {
  const byNearest = pages
    .map((_page, at) => at)
    .sort((one, other) => Math.abs(one - first) - Math.abs(other - first));
  const keptOn = new Map<string, number>();
  for (const at of byNearest) {
    for (const row of pages[at]?.rows ?? []) {
      if (!keptOn.has(row.playerId)) keptOn.set(row.playerId, at);
    }
  }
  return pages.flatMap((page, at) => page.rows.filter((row) => keptOn.get(row.playerId) === at));
}

/**
 * **The place the floating *You · 212th* button names** (the screens §5.3): the reader's, while they
 * are listed. **None when they are hidden from General** (the mechanics §10) or not listed, and none
 * where the card could not be read — no button.
 */
export function jumpPlace(card: PlaceCard | undefined): number | undefined {
  return card?.state === 'LISTED' ? card.place : undefined;
}

/**
 * **The sports the pill offers** — all four, the reader's rated sports first, then the rest, each
 * part in the app's sport order (the mechanics §9; PRD #766 call 9). Every sport has a ranking,
 * and a sport with no level is where *Get your {sport} level* stands.
 */
export function pillSports(rated: readonly Sport[]): readonly Sport[] {
  return [
    ...SPORTS.filter((sport) => rated.includes(sport)),
    ...SPORTS.filter((sport) => !rated.includes(sport)),
  ];
}

/** **The sport a reader with no level anywhere sees** — padel (the mechanics §9). */
export const FIRST_SPORT: Sport = 'padel';

/**
 * **What the page knows about where it could open** — each `undefined` while it is still being read,
 * and `null` once read and empty.
 */
export interface OpeningReads {
  /**
   * The trophy's sport — the sport of the reader's latest result, off Home's read. `null` with no
   * result anywhere.
   */
  readonly trophy: Sport | null | undefined;
  /**
   * The sport a group's deck last showed. `null` when it shows none, because the reader is rated in
   * nothing — and a ratings read that failed is read as that.
   */
  readonly deck: Sport | null | undefined;
}

/**
 * **Which sport the page opens on** (the mechanics §9): the trophy's — the sport of the reader's
 * latest result — else the sport the deck last showed, else padel.
 *
 * `asked` is the sport in the page's address: the trophy's, carried by its tap, or the one a pass
 * returns to. With none — a tap made before Home had answered, or a link with no sport — the page
 * reads the trophy's sport itself, so the race never opens it on the deck's. **It waits rather than
 * guessing**: `undefined` until each read it needs has answered, so the page never draws one sport
 * and then another.
 */
export function openingSport(asked: Sport | undefined, reads: OpeningReads): Sport | undefined {
  if (asked !== undefined) return asked;
  if (reads.trophy === undefined) return undefined;
  if (reads.trophy !== null) return reads.trophy;
  if (reads.deck === undefined) return undefined;
  return reads.deck ?? FIRST_SPORT;
}

/** **Three rows on their steps** — first in the middle, the tallest; second left; third right. */
export interface Podium {
  readonly first: RankedRow;
  readonly second: RankedRow;
  readonly third: RankedRow;
}

/**
 * **The podium** (the screens §5.1): the first three rows the reader sees, each labelled with its
 * true place — so with second hidden from the reader the steps read 1, 3 and 4. **None with fewer
 * than three**, when the list shows alone.
 */
export function podiumOf(rows: readonly RankedRow[]): Podium | undefined {
  const [first, second, third] = rows;
  if (first === undefined || second === undefined || third === undefined) return undefined;
  return { first, second, third };
}
