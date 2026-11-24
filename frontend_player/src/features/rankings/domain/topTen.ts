/**
 * **Top 10 on Home** ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home rows mechanics
 * §10, the screens §7; ADR-0204) — places 1 to 10 of General in one sport, the true top of the
 * Rankings page: everybody at their true place, whoever blocked whom.
 *
 * **Everything here is the server's answer, carried** — the order, each place, level and chip, and
 * whether anybody is ranked anywhere. What is this feature's own is which read the row asks for
 * (`topTenAsk`) and what it draws for an answer (`topTenFace`).
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { Chip } from './ranking';

/**
 * **The week's move on a card** — *▲ 2* or *▼ 1*. Only the two: a card draws no chip for no change,
 * nor for *New* (the README's override 10).
 */
export type Moved = Extract<Chip, { readonly kind: 'UP' | 'DOWN' }>;

/** **One card** — the numeral, the portrait, the nickname, the Level and the week's move. */
export interface TopTenPlayer {
  /** Their true place in General — the numeral, 1 to 10. */
  readonly place: number;
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Their first photograph; absent draws their court poster. */
  readonly photoUrl?: string;
  readonly level: number;
  /** Absent for no change, for *New*, and for anything this build cannot read: no chip drawn. */
  readonly chip?: Moved;
  /** The reader's own card — it reads *You*, its numeral volt and the card ringed in volt. */
  readonly isYou: boolean;
}

/** **One read of the row** — `GET /top-10`. */
export interface TopTen {
  /** The sport the row shows: the one picked, or the one the opening sport fell through to. */
  readonly sport: Sport;
  /** Whether anybody is ranked in General in **any** sport — while nobody is, the row is hidden. */
  readonly anyoneListed: boolean;
  /** Places 1 to 10, best first — fewer while fewer are ranked, none while nobody is. */
  readonly players: readonly TopTenPlayer[];
}

/**
 * **Which read the row asks for** (the mechanics §10.3): a sport picked on the pill **exactly** — a
 * sport with nobody in it reads *Nobody ranked in squash yet* — and otherwise the opening sport as
 * the **preferred** one, so the server falls through to the next sport where somebody is ranked.
 * Nothing while the opening sport is still being worked out.
 */
export type TopTenAsk =
  | { readonly kind: 'sport'; readonly sport: Sport }
  | { readonly kind: 'prefer'; readonly sport: Sport };

export function topTenAsk(
  picked: Sport | undefined,
  opening: Sport | undefined,
): TopTenAsk | undefined {
  if (picked !== undefined) return { kind: 'sport', sport: picked };
  if (opening !== undefined) return { kind: 'prefer', sport: opening };
  return undefined;
}

/**
 * **What the row draws** (the screens §7.1): nothing at all — heading included — until a read has
 * answered, for an answer this build cannot read (`null`), and while nobody is ranked in any sport; the cards it holds, one or two as well as ten;
 * or *Nobody ranked in squash yet* in a sport with nobody in it.
 */
export type TopTenFace =
  | { readonly kind: 'hidden' }
  | { readonly kind: 'nobody'; readonly sport: Sport }
  | { readonly kind: 'cards'; readonly sport: Sport; readonly players: readonly TopTenPlayer[] };

export function topTenFace(read: TopTen | null | undefined): TopTenFace {
  if (read == null || !read.anyoneListed) return { kind: 'hidden' };
  if (read.players.length === 0) return { kind: 'nobody', sport: read.sport };
  return { kind: 'cards', sport: read.sport, players: read.players };
}

/**
 * **Whether Top 10's read has finished, for Home's reveal** (#871) — its own read, once asked: landed,
 * refused, held for a connection, or failed once and retrying. **Until it is asked it waits behind its
 * opening sport** — Home's read and the ratings — **and one of those failing with nothing read counts
 * it as finished too**: Top 10 cannot set out until that read answers, and one failing read must not
 * hold Home through its backoff (the loading shimmer log Q13). A call, recorded in the shell's record.
 */
export function topTenReadFinished({
  asked,
  askedFinished,
  behindAFailure,
}: {
  /** Whether a Top 10 read has been asked for — its sport known. */
  readonly asked: boolean;
  /** Whether an asked one has finished. */
  readonly askedFinished: boolean;
  /** Whether a read the opening sport waits on has failed with nothing read. */
  readonly behindAFailure: boolean;
}): boolean {
  return asked ? askedFinished : behindAFailure;
}
