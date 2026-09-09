/**
 * What rides a conversation's stream: **two shapes, one order, and the codes a system line can
 * be.**
 *
 * ADR-0146 decided a system line is *a code and its values*, never a Message with a `kind`, and
 * [ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §4 made the two a **discriminated union** on the wire — because one shape forces either a
 * stored rendered sentence, which freezes copy into history so rewriting a line cannot rewrite
 * the backlog, or a text field real for one kind and meaningless for the other. **Nobody typed
 * *Tomek set the day*.** This file is that union on this side of the mapper, and the surface keeps
 * it: two components, never one with a branch.
 *
 * ## `seq` is the identity, and nothing may read a gap
 *
 * A message has **no id of its own** — `(conversation_id, seq)` already identifies it — and the
 * sequence is gapless and starts at 1, which is why nothing on this wire carries `has_more`.
 * **The gaplessness is the server's promise and nothing here depends on it**: no reader infers
 * loss from a gap, so there is no rule in this file about one.
 *
 * ## Seven codes, and the two the values decide
 *
 * The sentences are [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §23 and
 * live in `components/conversationPresentation.ts`; what is here is the vocabulary and the
 * narrowing. Two of the seven are a code **plus** a value:
 *
 * - **A seat leaving is one code with the answer as a value.** *That seat is open again* is the
 *   same news either way, so the two facts stay apart in `values.departure` rather than in a
 *   second code — and **a lapse is still not a decline**, which is §13's rule holding one layer
 *   down.
 * - **The three plan codes each carry the value that was recorded** — the place as it was typed,
 *   the day as `YYYY-MM-DD`, the hour as `HH:MM`. Setting a slot and moving one are **one code
 *   told twice**, which is the opposite rule for the opposite case: they are the same fact, where
 *   a lapse and a decline are two.
 *
 * ## The day is a calendar date, and that is what makes it zone-free
 *
 * `DAY_RECORDED` carries `YYYY-MM-DD` and the sentence names a weekday. A date with no time in it
 * is a **calendar** date rather than an instant, so which weekday it is cannot depend on where the
 * phone is — which is the same thing the day separator needs from the platform zone, arrived at
 * from the other end. Two people in one room read one weekday, by construction.
 */

import type { Weekday } from '@/shared/vocabulary/week';

/** The seven a system line can be. §23, and a code outside them is one this build cannot read. */
export const SYSTEM_LINE_CODES = [
  'SEAT_ACCEPTED',
  'SEATS_INVITED',
  'SEAT_LEFT',
  'GAME_PLAYED',
  'PLACE_RECORDED',
  'DAY_RECORDED',
  'HOUR_RECORDED',
] as const;

export type SystemLineCode = (typeof SYSTEM_LINE_CODES)[number];

/** How a seat left. One code, two facts, and they are never told as one. */
export const DEPARTURES = ['DECLINED', 'LAPSED'] as const;

export type Departure = (typeof DEPARTURES)[number];

/**
 * What a line needs beyond a handle — and **nothing membership already says**.
 *
 * A raw record rather than a shape per code, because the wire is one: `values` is
 * `{[key: string]: string}` and every reading of it is a narrowing this file does. A typed
 * variant per code would be seven shapes the mapper had to guess between before the presentation
 * could refuse one.
 */
export type EntryValues = Readonly<Record<string, string>>;

/** Somebody's own words, unrendered and unchanged. */
export interface Message {
  readonly kind: 'message';
  readonly seq: number;
  readonly authorId: string;
  readonly sentAt: string;
  readonly text: string;
  /** The id the sending client generated, echoed back — the key an optimistic bubble replaces on. */
  readonly clientMessageId: string;
}

/** Something that happened, told by a context that does not know this one exists. */
export interface SystemLine {
  readonly kind: 'system-line';
  readonly seq: number;
  /** Absent when the server sent a code this build has no words for. See the module note. */
  readonly code?: SystemLineCode;
  readonly occurredAt: string;
  /** Who did it, or nobody. `{name}` is filled from membership and never from `values`. */
  readonly actorId?: string;
  readonly values: EntryValues;
}

export type Entry = Message | SystemLine;

/** The code, or nothing where this build has no words for it. */
export function toSystemLineCode(code: string): SystemLineCode | undefined {
  return SYSTEM_LINE_CODES.find((known) => known === code);
}

/**
 * How a seat left, or nothing where the value is one this build cannot read.
 *
 * The absence is the same fact a missing code is — *this app is too old to read this one* — and
 * it is treated the same way, for the reason `conversationPresentation.ts` states: a system line
 * **is** the whole of the slot it is drawn in, so there is nothing left to say when its sentence
 * cannot be picked.
 */
export function departureOf(values: EntryValues): Departure | undefined {
  return DEPARTURES.find((known) => known === values.departure);
}

/** How many seats an invitation asked for, or nothing where the value is not a count. */
export function invitedCount(values: EntryValues): number | undefined {
  const count = Number(values.count);
  return values.count !== undefined && Number.isInteger(count) && count > 0 ? count : undefined;
}

/** ISO weekday numbering, off `Date`'s Sunday-first `getUTCDay`. */
const ISO_WEEKDAYS: readonly Weekday[] = [7, 1, 2, 3, 4, 5, 6];

/**
 * Which weekday a recorded day falls on, or nothing where the value is not a calendar date.
 *
 * Read at UTC because the value **has no time in it**: `2026-09-12` names a square on a calendar,
 * and parsing it as an instant in the device's zone is what would let one room read Saturday on
 * one phone and Friday on another. See the module note.
 */
export function weekdayOf(day: string): Weekday | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return undefined;

  const at = new Date(`${day}T00:00:00Z`);
  if (Number.isNaN(at.getTime())) return undefined;

  return ISO_WEEKDAYS[at.getUTCDay()];
}
