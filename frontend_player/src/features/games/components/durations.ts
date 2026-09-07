/**
 * How long is left, as words — **measured from `read_at`, never from this phone's clock.**
 *
 * Every deadline on the games contract is *"a moment the backend computed, never a duration and
 * never a rule the client applies"*, and the list carries `read_at` as the instant every
 * standing beside it was folded against. Subtracting from `Date.now()` instead would let a
 * countdown drift out of agreement with the word printed next to it — *awaiting an answer* over
 * *0 hours left* — which is the one failure that field exists to prevent.
 *
 * **There is no date and no clock time in it, and that is the product rather than an
 * omission.** This platform has no calendar: the grid is *an ordinary week*, a `Window` is a
 * label on a search and never a proposed time, and there is no date picker anywhere in this
 * app. A duration is the only time-shaped thing these screens are entitled to draw.
 *
 * It **floors**. A deadline is a promise, and 23 h 50 m stated as *24 hours* is wrong in the
 * one direction that costs somebody their turn.
 *
 * It is here rather than in `shared/formatting` on that file's own rule: `answerWindowLine` in
 * `challenges` takes its duration as a **string from the caller** and has no producer, so this
 * is the first implementation rather than the third copy. It moves the day a second surface
 * asks for one.
 */

import { counted } from '@/shared/formatting/counted';

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** Beyond this, hours stop being the readable unit. A day and a half is *36 hours*, not *a day*. */
const DAYS_ABOVE = 2 * DAY;

/**
 * A span of time in one unit, floored, with `less than a minute` under the bottom of the scale.
 *
 * One ladder for both directions: a deadline and an arrangement are the same arithmetic read
 * two ways, and two ladders would eventually round differently in one sentence.
 */
function spanWords(ms: number): string {
  if (ms < MINUTE) return 'less than a minute';
  if (ms < HOUR) return counted(Math.floor(ms / MINUTE), 'minute', 'minutes');
  if (ms < DAYS_ABOVE) return counted(Math.floor(ms / HOUR), 'hour', 'hours');
  return counted(Math.floor(ms / DAY), 'day', 'days');
}

/** How long until a deadline the backend computed, from the instant it folded the standing. */
export function durationLeft(deadline: string, readAt: string): string {
  // A deadline at or behind `read_at` cannot happen on a standing that says the window is open —
  // the two were folded together — but a list can be a minute old on screen, and *0 hours* is
  // the sentence that makes somebody think they have already missed it.
  return spanWords(Date.parse(deadline) - Date.parse(readAt));
}

/**
 * How long ago something happened, from the same instant.
 *
 * The only thing that tells two padel games apart in a list, and it is a **duration** rather
 * than a date for the reason at the top of this file: there is no calendar in this product to
 * print one against.
 */
export function durationSince(moment: string, readAt: string): string {
  return spanWords(Date.parse(readAt) - Date.parse(moment));
}
