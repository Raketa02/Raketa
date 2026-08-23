/**
 * The header eyebrow's day and time — the one line on Now that is about the
 * **player** rather than about a club.
 *
 * `docs/value-formatting.md` renders a time in the zone its value names, and
 * names exactly one exception: *"Now's header eyebrow, which is the device's own
 * clock, because that line says it is now 14:30 where you are."* Everything else
 * on this screen — a match's start, an offer's expiry — carries the club's IANA
 * zone and is formatted against that, never against this.
 *
 * **No `Intl`, and the reason is the same one the money table gives.**
 * `Intl.DateTimeFormat` is locale-dependent at runtime and varies with the ICU
 * build, so the same instant can render two ways on two phones. The device's own
 * weekday and wall clock need no timezone database — `Date` already answers both
 * in local time — so the table below is the whole mechanism.
 *
 * **The line does not tick, and that is deliberate.** The UI authority proposes a
 * minute-aligned 60 s repaint; `ADR-0054` leaves the client no timer, and the
 * eyebrow is a greeting rather than a control. It is composed when the screen is,
 * which is on arrival — the overwhelming majority of the reads.
 */

/** `Date#getDay()` is Sunday-first, so this table is too. */
const WEEKDAYS: readonly string[] = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

/** `Saturday · 14:00`, on the device's clock. 24-hour and zero-padded. */
export function dayAndTime(now: number): string {
  const at = new Date(now);
  const hours = String(at.getHours()).padStart(2, '0');
  const minutes = String(at.getMinutes()).padStart(2, '0');

  return `${WEEKDAYS[at.getDay()]} · ${hours}:${minutes}`;
}
