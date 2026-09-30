/**
 * **When a card's game is, as the court block says it** — *Today*, *Tomorrow*, *Saturday*, or a
 * weekday with its date once the game is a week or more away — and the fortnight a deck deals
 * into, for the weekly cap's line.
 *
 * Every day here is the **platform's** (`shared/date/platformZone`): a court hour at a club in
 * Kraków is Saturday 16:00 on every phone that draws it, and a device zone would put it a day off
 * for somebody abroad. *Today* is the day of the instant the deck was read, never of this phone's
 * clock, on `durationLeft`'s rule.
 */

import { daysAfter, daysBetween, platformDay, weekdayOf } from '@/shared/date/platformZone';
import type { Weekday } from '@/shared/vocabulary/week';

/** How the court block names a game's day. */
export type GameDay =
  | { readonly kind: 'today' }
  | { readonly kind: 'tomorrow' }
  /** Within the week ahead, the weekday is enough: *Saturday*. */
  | { readonly kind: 'weekday'; readonly weekday: Weekday }
  /** A week or more ahead, a weekday alone would name two days: *Saturday 10 Oct*. */
  | { readonly kind: 'dated'; readonly weekday: Weekday; readonly day: string };

/** A weekday name alone is ambiguous from this many days ahead — the same weekday next week. */
const A_WEEK = 7;

/** **A game is an hour** — a court is sold by the hour (ADR-0189), and the wire says so. */
export const GAME_LENGTH_MS = 3_600_000;

/** When a game ends: an hour after it starts. `undefined` for a value that is not an instant. */
export function gameEndsAt(startsAt: string): string | undefined {
  const at = Date.parse(startsAt);
  return Number.isNaN(at) ? undefined : new Date(at + GAME_LENGTH_MS).toISOString();
}

/** The platform's calendar day of an instant held as milliseconds — the deck's clock. */
function dayAt(instant: number): string | undefined {
  return platformDay(new Date(instant).toISOString());
}

/** **The weekday an instant falls on**, on the platform's calendar — the grid's white letter. */
export function weekdayAt(instant: number | string): Weekday | undefined {
  const day = typeof instant === 'number' ? dayAt(instant) : platformDay(instant);
  return day === undefined ? undefined : weekdayOf(day);
}

/**
 * The game's day against the day the deck was read. `undefined` for a value that is not an
 * instant, which names no day.
 */
export function gameDayOf(startsAt: string, readAt: number): GameDay | undefined {
  const day = platformDay(startsAt);
  const today = dayAt(readAt);
  if (day === undefined || today === undefined) return undefined;

  const ahead = daysBetween(today, day);
  const weekday = weekdayOf(day);
  if (ahead === undefined || weekday === undefined) return undefined;

  if (ahead === 0) return { kind: 'today' };
  if (ahead === 1) return { kind: 'tomorrow' };
  if (ahead < A_WEEK) return { kind: 'weekday', weekday };
  return { kind: 'dated', weekday, day };
}

/**
 * **The Mondays of the deck's fortnight** — the week the deck was read in and the one after, as
 * the capped weeks name them (`starts_on`, a Monday on the club's clock).
 */
export function fortnightOf(
  readAt: number,
): { readonly thisMonday: string; readonly nextMonday: string } | undefined {
  const today = dayAt(readAt);
  const weekday = today === undefined ? undefined : weekdayOf(today);
  if (today === undefined || weekday === undefined) return undefined;

  const thisMonday = daysAfter(today, 1 - weekday);
  const nextMonday = thisMonday === undefined ? undefined : daysAfter(thisMonday, A_WEEK);
  if (thisMonday === undefined || nextMonday === undefined) return undefined;
  return { thisMonday, nextMonday };
}
