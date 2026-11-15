/**
 * **A Joiner** — a player on New in Raketa: who **joined** (the profile commit that ends onboarding)
 * in the last 30 days ([#801](https://github.com/Raketa02/Raketa/issues/801); ADR-0204 §5; the Home
 * rows mechanics §7). The backend's word for the same person (#793); the glossary bars *newcomer*,
 * which is the **Newcomer**'s 14 days.
 *
 * The rows' rules are the server's — who, how many, in which order, the Warsaw days — and this
 * feature draws its answer. What is left here is **the Joined ladder**, which the words key by, and
 * where a request from the row was found. See all's paging and pill are every people row's
 * (`seeAll.ts`).
 */

import type { FoundIn, FriendRelation } from '@/features/friends/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { SeeAllPage } from './seeAll';

/**
 * **Where a request from this row was found** — the tile's round button and the record a tile opens
 * both send it, and the other person's Home reads *Found you among new players* (the mechanics §12).
 */
export const FOUND_AMONG_NEW_PLAYERS: FoundIn = { from: 'NEW_PLAYERS' };

/** One sport a Joiner holds a level in — *Padel 2,35*. */
export interface JoinerSport {
  readonly sport: Sport;
  readonly level: number;
}

export interface Joiner {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Their first photograph; absent draws their court poster. */
  readonly photoUrl?: string;
  /** Warsaw days since they joined — the server's count (the mechanics §7.3). */
  readonly daysSinceJoined: number;
  /** Every sport they hold a level in, in the sports' own order — **none** for a player with no level. */
  readonly sports: readonly JoinerSport[];
  /** Where the reader stands with them — the round friend button. */
  readonly relation: FriendRelation;
}

/**
 * **One page of See all** — 20 Joiners, the cursor behind them, and the pill's sports: every sport at
 * least one of them holds a level in.
 */
export type JoinerPage = SeeAllPage<Joiner>;

/**
 * **The *Joined …* ladder** (the mechanics §7.3, the words §31.7) — no weekday names:
 *
 * | Days | Line |
 * | --- | --- |
 * | 0 | *Joined today* |
 * | 1 | *Joined yesterday* |
 * | 2–6 | *Joined 2 days ago* … *Joined 6 days ago* |
 * | 7–13 | *Joined last week* |
 * | 14 and up | *Joined 2 weeks ago* … *Joined 4 weeks ago* — days ÷ 7, rounded down, at most 4 |
 */
export type JoinedAgo =
  | { readonly kind: 'today' }
  | { readonly kind: 'yesterday' }
  | { readonly kind: 'days'; readonly days: number }
  | { readonly kind: 'lastWeek' }
  | { readonly kind: 'weeks'; readonly weeks: number };

/** The most weeks the ladder says — a Joiner is on the rows for 30 days. */
const MOST_WEEKS = 4;

export function joinedAgo(days: number): JoinedAgo {
  if (days <= 0) return { kind: 'today' };
  if (days === 1) return { kind: 'yesterday' };
  if (days < 7) return { kind: 'days', days };
  if (days < 14) return { kind: 'lastWeek' };
  return { kind: 'weeks', weeks: Math.min(MOST_WEEKS, Math.floor(days / 7)) };
}
