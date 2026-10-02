/**
 * **What the Bookings page is asked for, and what its acts post.** The page's address says the
 * day, the filter and a booking to point at, `/bookings?date=2026-10-12&filter=waiting&booking=…`;
 * an act on a booking says which, on which booking, and what the desk chose.
 */

import { formId, formText, isId } from '@/ui/forms';

import { FILTERS, isCancelReason, type BookingsFilter, type CancelReason } from './mappers';

/** The page's address, read. */
export interface DayQuery {
  /** A local day, `2026-10-12`; `null` for today, which the backend knows. */
  readonly date: string | null;
  readonly filter: BookingsFilter;
  /** The booking a link pointed at (an exception refused over it), or `null`. */
  readonly booking: string | null;
}

/** How each filter is written in the address: a word a desk could read; *all* is no word. */
const SLUGS: Readonly<Record<BookingsFilter, string | null>> = {
  ALL: null,
  WAITING_FOR_YOU: 'waiting',
  SEAT_OPEN: 'seat-open',
  CALLED_OFF: 'called-off',
};

const DAY = /^(\d{4})-(\d{2})-(\d{2})$/;

/** A real calendar day written `2026-10-12`, or `null`: `2026-02-30` is none. */
export function realDay(text: string): string | null {
  const match = DAY.exec(text);
  if (match === null) return null;
  const [, year = '', month = '', date = ''] = match;
  const at = new Date(Date.UTC(Number(year), Number(month) - 1, Number(date)));
  return at.toISOString().slice(0, 10) === text && Number(year) >= 2000 ? text : null;
}

/** The day `days` after a local day (before it, when negative). */
export function dayAfter(day: string, days: number): string {
  const [year = 0, month = 1, date = 1] = day.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, date + days)).toISOString().slice(0, 10);
}

function one(value: string | string[] | undefined): string {
  return typeof value === 'string' ? value : '';
}

/** The page's address as asked: anything it does not understand reads as today, all of it. */
export function readDayQuery(
  params: Readonly<Record<string, string | string[] | undefined>>,
): DayQuery {
  const slug = one(params.filter);
  const id = one(params.booking);
  return {
    date: realDay(one(params.date)),
    filter: FILTERS.find((filter) => SLUGS[filter] === slug) ?? 'ALL',
    booking: isId(id) ? id : null,
  };
}

/** The page's address for a day and a filter: today and *all* are left out. */
export function dayHref(query: {
  readonly date: string | null;
  readonly filter: BookingsFilter;
}): string {
  const params = new URLSearchParams();
  if (query.date !== null) params.set('date', query.date);
  const slug = SLUGS[query.filter];
  if (slug !== null) params.set('filter', slug);
  const search = params.toString();
  return search === '' ? '/bookings' : `/bookings?${search}`;
}

/** What the desk can do to a booking from the page. */
export type BookingAct = 'accept' | 'refuse' | 'move' | 'cancel';

const ACTS: readonly BookingAct[] = ['accept', 'refuse', 'move', 'cancel'];

export function isBookingAct(value: unknown): value is BookingAct {
  return typeof value === 'string' && (ACTS as readonly string[]).includes(value);
}

/** The longest note a refusal keeps for the club's own records. */
export const REFUSAL_NOTE_MOST = 200;

/** An act as posted: which, on which booking, as the desk saw it, and what it chose. */
export interface PostedAct {
  /** `null` for anything that is none of the four. */
  readonly act: BookingAct | null;
  readonly id: string | null;
  /** The game as the page named it to the desk: *the 19:00 game on Sat 3 Oct*. */
  readonly name: string;
  /** A refusal's note, tidied: `''` for none. */
  readonly note: string;
  readonly courtId: string | null;
  readonly cancel: CancelReason | null;
}

export function readAct(form: FormData): PostedAct {
  const reason = formText(form, 'reason');
  const act = formText(form, 'act');
  return {
    act: isBookingAct(act) ? act : null,
    id: formId(form, 'id'),
    name: formText(form, 'name'),
    note: formText(form, 'note').trim().replace(/\s+/g, ' '),
    courtId: formId(form, 'court_id'),
    cancel: isCancelReason(reason) ? reason : null,
  };
}

/**
 * **What the page refuses before asking the backend**, as the backend's or the site's own code,
 * or `null` when the act can go: a refusal's note too long for the club's records, a move with
 * no court chosen, a cancel with no reason.
 */
export function checkAct(posted: PostedAct): string | null {
  if (posted.act === null) return 'request_invalid';
  if (posted.id === null) return 'booking_not_found';
  if (posted.act === 'refuse' && [...posted.note].length > REFUSAL_NOTE_MOST) {
    return 'refusal_note_too_long';
  }
  if (posted.act === 'move' && posted.courtId === null) return 'court_required';
  if (posted.act === 'cancel' && posted.cancel === null) return 'cancel_reason_required';
  return null;
}
