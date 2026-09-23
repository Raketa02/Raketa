/**
 * **The court's pairing, read beside the game** — the forecast, the split, what is at stake and
 * each seat's Level, computed for the reader and stored nowhere
 * ([ADR-0161](../../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
 *
 * `GET /games/{game_id}/pairing` answers it, and it is **not on the game**: `GameSeat` still
 * carries a handle and nothing else (ADR-0141), and this is a second read under a key of its own
 * that means what a card means *because this game has not happened* — the route refuses once it
 * has. So the type stands beside {@link Game} rather than inside it, and a screen that holds both
 * has made two reads and knows it.
 *
 * ## Every figure is the server's, and the client computes nothing
 *
 * `the-play-screens.md` §5's *no forecast arithmetic on the client*, applied whole. The gap is
 * `your_side − their_side` **as served** — signed, subtracted unrounded by the engine, and read
 * in the reader's direction so two people across the net see the sign flip. The range is μ ± σ as
 * published, never derived from the confidence; the band is a **name**, never derived from the
 * Level. What the bar draws from the gap is `balanceShare`'s one fixed scale, which is a mapping
 * of a served number and not a computation over two.
 *
 * ## Three absences, and each is its own
 *
 * `forecast` and `split` are one computation and are **omitted together** when the pairing cannot
 * be computed — somebody unrated in the sport, or a seat the index cannot describe. There is no
 * reason beside the absence and the screen draws nothing and says nothing (ADR-0161 §4). `atStake`
 * is omitted on a friendly — *meaningless rather than unavailable* — and where the rule has
 * nothing to move. `seats` names whoever holds a rating, in the court's own order; somebody
 * unrated is simply not in it, and their row draws a handle with no Level under it.
 */

import type { AppError } from '@/shared/errors';

import type { GameSeat } from './game';

/** How even the game is forecast to be, **in your direction** — the served evenness, whole or not. */
export interface PairingForecast {
  readonly pct: number;
}

/** The two side strengths the forecast was read from, and the gap between them **as served**. */
export interface PairingSplit {
  readonly yourSide: number;
  readonly theirSide: number;
  /** `yourSide − theirSide`, signed by the engine. Never subtracted here. */
  readonly gap: number;
}

/** What a **counted** result would do to your Level — the pair, and the same pair for your side. */
export interface AtStake {
  readonly winDelta: number;
  readonly lossDelta: number;
}

/** The likely range a Level sits in — μ ± σ as published. Not the band's edges. */
export interface LikelyRange {
  readonly low: number;
  readonly high: number;
}

/** One seat's Level, as the rating engine published it: the four figures a record prints. */
export interface PairingSeat {
  readonly playerId: string;
  readonly level: number;
  /** The band's published **name**, printed as it came. */
  readonly band: string;
  readonly range: LikelyRange;
  /** A whole percentage — the engine's own figure. */
  readonly confidence: number;
}

export interface Pairing {
  /** The instant the game's standing was folded at and the pairing computed against. */
  readonly readAt: string;
  /** Absent together with {@link split} when the pairing cannot be computed. */
  readonly forecast?: PairingForecast;
  readonly split?: PairingSplit;
  /** Absent on a friendly, and where you or the whole other side holds no rating. */
  readonly atStake?: AtStake;
  /** One row per seat whose person holds a rating, in the court's own order. */
  readonly seats: readonly PairingSeat[];
}

/**
 * The court **as the players card reads it**: your side first — you, then your partner — then
 * the other side, each side in the court's own order.
 *
 * The one re-ordering this feature makes, and it is a rule rather than a drawing decision: a
 * list of people is read from the reader outward, and the court arrives in whatever order the
 * challenge seated it. A reader holding no seat is a stale link the screen has already answered
 * for, so the court is handed back as it came rather than given an order about nobody.
 */
export function courtForReader(seats: readonly GameSeat[], playerId: string): readonly GameSeat[] {
  const sides = sidesForReader(seats, playerId);
  return sides === undefined ? seats : [...sides.yours, ...sides.theirs];
}

/** The court split in two, each half in the reader's order. */
export interface CourtSides {
  /** You first, then whoever else is on your side. */
  readonly yours: readonly GameSeat[];
  readonly theirs: readonly GameSeat[];
}

/**
 * The same order as **two halves** — for the bar's two labels and the split row's two names,
 * which are one split of one court and must not be made twice. `undefined` where no seat is the
 * reader's: there is no *yours* to lead with.
 */
export function sidesForReader(
  seats: readonly GameSeat[],
  playerId: string,
): CourtSides | undefined {
  const mine = seats.find((seat) => seat.playerId === playerId);
  if (mine === undefined) return undefined;

  return {
    yours: [mine, ...seats.filter((seat) => seat.side === mine.side && seat.playerId !== playerId)],
    theirs: seats.filter((seat) => seat.side !== mine.side),
  };
}

/**
 * The route's three refusals, by **code** and never by status or message
 * (`.claude/rules/query-and-errors.md`).
 *
 * A `Record` keyed by the union rather than a list, on `gameMappers`' argument: a fourth refusal
 * added to the contract is a `pnpm typecheck` failure in the one place that has to decide whether
 * it is an answer or an outage.
 */
export type PairingRefusal = 'game_not_found' | 'pairing_is_history' | 'account_held';

const REFUSALS: Readonly<Record<PairingRefusal, true>> = {
  /** No game of **yours** has that id — one code for two cases, so an id cannot be probed. */
  game_not_found: true,
  /** The game has happened, or its entry window closed on silence. There is no pairing to read. */
  pairing_is_history: true,
  /** The account is held. Met here as everywhere, and drawn as nothing. */
  account_held: true,
};

/**
 * Whether this failure is the route saying **no pairing**, by name.
 *
 * Each of the three is an answer rather than an outage: nothing to retry, nothing to report, and
 * — since #410 decided the block says nothing about why it is absent — nothing to draw. What the
 * name buys is that the read resolves to *no pairing* rather than erroring, so a refused game is
 * not retried on every focus as though the platform were down.
 */
export function pairingRefusedByName(error: AppError): boolean {
  return error.code !== undefined && Object.hasOwn(REFUSALS, error.code);
}
