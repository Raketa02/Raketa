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

/**
 * **The one zone this platform arranges in.**
 *
 * A locale assumption rather than a constant to tune
 * ([ADR-0144](../../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)),
 * and **its falsifier is the first shard whose players are somewhere else**. It is the same zone
 * the plan's day and hour are recorded in, which is what lets a separator and a `DAY_RECORDED`
 * line agree about which day Saturday is.
 */
export const PLATFORM_ZONE = 'Europe/Warsaw';

/**
 * The formatter behind {@link platformDay}, built once.
 *
 * **`formatToParts` rather than `format`**, because the parts are named and the layout is not: an
 * `en-GB` date formats as `12/09/2026` and an `en-CA` one as `2026-09-12`, so a string assembled
 * out of a locale's own order is a string that changes when somebody changes the locale. The
 * parts are the same three whatever the locale does with them.
 */
const IN_THE_PLATFORM_ZONE = new Intl.DateTimeFormat('en-GB', {
  timeZone: PLATFORM_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

/**
 * Which calendar day an instant falls on **in the platform's zone**, as `YYYY-MM-DD`.
 *
 * The one conversion the day separator needs, and the reason it is here rather than in a
 * component: **a device zone would put two people in one room on two different days**
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.3). A room
 * lives at most a few days, so *was this today* is the one time-shaped fact worth drawing — and
 * it is worth nothing at all if two phones disagree about it.
 *
 * It answers `undefined` for a value that is not an instant, which is the same nothing every
 * other narrowing in this file answers with: there is no day to name and inventing one would be
 * a claim about when something happened.
 */
export function platformDay(instant: string): string | undefined {
  const at = new Date(instant);
  if (Number.isNaN(at.getTime())) return undefined;

  const parts = IN_THE_PLATFORM_ZONE.formatToParts(at);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((one) => one.type === type)?.value;

  const [year, month, day] = [part('year'), part('month'), part('day')];

  return year === undefined || month === undefined || day === undefined
    ? undefined
    : `${year}-${month}-${day}`;
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
