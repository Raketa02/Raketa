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
 * ## Eight codes, and the two the values decide
 *
 * The sentences are [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §23 and
 * live in `components/conversationPresentation.ts`; what is here is the vocabulary and the
 * narrowing. Two of the eight are a code **plus** a value, and one is a code and nothing else:
 *
 * - **A seat leaving is one code with the answer as a value.** *That seat is open again* is the
 *   same news either way, so the two facts stay apart in `values.departure` rather than in a
 *   second code — and **a lapse is still not a decline**, which is §13's rule holding one layer
 *   down.
 * - **The three slot codes each carry the value that was recorded** — the place as it was typed,
 *   the day as `YYYY-MM-DD`, the hour as `HH:MM`. Setting a slot and moving one are **one code
 *   told twice**, which is the opposite rule for the opposite case: they are the same fact, where
 *   a lapse and a decline are two.
 * - **The lock carries no value at all**
 *   ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
 *   It is the Plan's fourth code and not a fourth slot: the three slots are the value and the
 *   room already holds a line for each, so a copy here would be the second place they are true
 *   and the first thing to disagree with the slot line above it after a later move. There is no
 *   unlocked code — the lock freezes nothing, and a slot moved afterwards keeps it and writes its
 *   own line.
 *
 * ## The day is a calendar date, and that is what makes it zone-free
 *
 * `DAY_RECORDED` carries `YYYY-MM-DD` and the sentence names a weekday. A date with no time in it
 * is a **calendar** date rather than an instant, so which weekday it is cannot depend on where the
 * phone is — which is the same thing the day separator needs from the platform zone, arrived at
 * from the other end. Two people in one room read one weekday, by construction.
 *
 * **Both conversions left this file** for `shared/date/platformZone.ts`
 * ([#366](https://github.com/Raketa02/Raketa/issues/366)): the plan's day row is the third caller,
 * and unlike the tables that were promoted before them a second copy of this one would put two
 * surfaces of one screen on two different days. What stayed is {@link separatorBefore}, which is a
 * rule about a **stream** and belongs to the feature that draws one.
 */

import { platformDay, weekdayOf } from '@/shared/date/platformZone';
import type { Weekday } from '@/shared/vocabulary/week';

/** The eight a system line can be. §23, and a code outside them is one this build cannot read. */
export const SYSTEM_LINE_CODES = [
  'SEAT_ACCEPTED',
  'SEATS_INVITED',
  'SEAT_LEFT',
  'GAME_PLAYED',
  'PLACE_RECORDED',
  'DAY_RECORDED',
  'HOUR_RECORDED',
  'PLAN_LOCKED',
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
  /**
   * Who did it, or nobody. `{name}` is filled from the response's `people` and never from
   * `values` — and never from the roster, which cannot name the one who said no.
   */
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

/**
 * When an entry happened — **the one field the two arms spell differently.**
 *
 * A message landed and a system line occurred, and both are the same fact for everything that
 * orders or dates the stream. Read through one function so a reader of the union never has to
 * remember which arm calls it what.
 */
export function entryMoment(entry: Entry): string {
  return entry.kind === 'message' ? entry.sentAt : entry.occurredAt;
}

/**
 * **The weekday to draw above an entry**, or nothing where it belongs under the separator that is
 * already there.
 *
 * `previous` is the entry **before** it in the stream — older, whichever way the list is drawn.
 * Absent means there is nothing before it in the page being held, and the separator is drawn: it
 * labels the oldest day on screen, and paging backward moves it up onto whatever arrives.
 *
 * **There is no per-message timestamp anywhere and this is the whole of what replaces one.** A
 * room lives days rather than months, so a clock beside every bubble is noise; what a reader
 * wants is where one day stops and the next starts.
 */
export function separatorBefore(entry: Entry, previous: Entry | undefined): Weekday | undefined {
  const day = platformDay(entryMoment(entry));
  if (day === undefined) return undefined;

  const before = previous === undefined ? undefined : platformDay(entryMoment(previous));

  return before === day ? undefined : weekdayOf(day);
}
