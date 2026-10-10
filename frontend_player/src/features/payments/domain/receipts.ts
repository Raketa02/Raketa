/**
 * **You › Payments' *RECEIPTS*** — every share the reader paid, and every refund, newest first,
 * **the club named as the seller** ([#555](https://github.com/Raketa02/Raketa/issues/555); the
 * screens A7.3; mock 49; the mechanics §12.1).
 *
 * Pure: the read's rows as the section draws them, and the one decision the row makes over them —
 * how the game's day is named.
 */

import { daysBetween, platformDay, weekdayOf } from '@/shared/date/platformZone';
import type { Sport } from '@/shared/vocabulary/sport';
import type { Weekday } from '@/shared/vocabulary/week';

import type { Seller } from './seatCharge';

/**
 * A charge (✓) or a refund (↩). The wire serves a third, a hold let go (`RELEASED`, #641) — *40 zł
 * held · released* — which this phone does not draw yet (#644): the mapper leaves those rows out,
 * and `mappers/wireVocabulary.ts` holds the rest of the wire's kinds equal to this union.
 */
export type ReceiptKind = 'CHARGE' | 'REFUND';

export interface Receipt {
  readonly seatChargeId: string;
  readonly kind: ReceiptKind;
  readonly club: Seller;
  readonly sport: Sport;
  /** The game's hour. */
  readonly startsAt: string;
  /** What was paid, or refunded — always positive; the kind says which way it went. */
  readonly amountGrosze: number;
}

/** How a receipt names its game's day — *Today*, *Yesterday*, *Saturday*, *26 Sep*. */
export type ReceiptDay =
  | { readonly kind: 'today' }
  | { readonly kind: 'tomorrow' }
  | { readonly kind: 'yesterday' }
  /** Within the week ahead the weekday is enough. */
  | { readonly kind: 'weekday'; readonly weekday: Weekday }
  /** Further off, either way: the date. */
  | { readonly kind: 'dated'; readonly day: string };

/** A weekday name alone would name two days from this far. */
const A_WEEK = 7;

/**
 * **The game's day, against today on the platform's calendar** — the court block's words where a
 * receipt is for a game ahead, and *Yesterday* or the date for one played. `undefined` for a value
 * that is not an instant.
 */
export function receiptDayOf(startsAt: string, now: number): ReceiptDay | undefined {
  const day = platformDay(startsAt);
  const today = platformDay(new Date(now).toISOString());
  if (day === undefined || today === undefined) return undefined;

  const ahead = daysBetween(today, day);
  const weekday = weekdayOf(day);
  if (ahead === undefined || weekday === undefined) return undefined;

  if (ahead === 0) return { kind: 'today' };
  if (ahead === 1) return { kind: 'tomorrow' };
  if (ahead === -1) return { kind: 'yesterday' };
  if (ahead > 1 && ahead < A_WEEK) return { kind: 'weekday', weekday };
  return { kind: 'dated', day };
}
