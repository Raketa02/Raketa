/**
 * **The one zone this platform arranges in**, and the three conversions that depend on it.
 *
 * A locale assumption recorded as one rather than a constant to tune
 * ([ADR-0144](../../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)),
 * in the shape `availability.py`'s `_WEEKEND` already uses on the other side of the wire. **Its
 * falsifier is the first shard whose players are somewhere else**, and on that day this becomes a
 * fact about a club or a court rather than about the platform.
 *
 * ## It left `features/conversations/domain/entry.ts` on the third-caller rule
 *
 * The day separator wrote it first, the quick chips read it second, and the plan's day row is the
 * third — and unlike the tables that moved before it, a second copy of this one is not merely
 * drift. **Two implementations of *which day is it in Warsaw* would put two surfaces of one screen
 * on two different days**, and the falsifier above would have to be found twice. Nothing about it
 * is a conversation's, which is what makes `shared/date/` its home rather than a feature's
 * `domain/` (`docs/architecture.md` Part 1: *utilities get semantic homes*).
 *
 * ## Poland's two offsets, and the rule that picks one
 *
 * `Intl.DateTimeFormat` with a `timeZone` is the obvious way to do this and it is **refused for
 * the reason `shared/formatting/ratingFormat.ts` already records**: *"Hermes ships without the
 * full ICU data unless it is explicitly built in"*, so a zone-aware formatter can silently fall
 * back — and what it would fall back to here is the **device's** day, which is precisely the
 * failure the platform zone exists to prevent. A wrong number that announces itself is
 * survivable; this one would not, and Node's full ICU means no test in this repository could
 * see it.
 *
 * So the conversion is arithmetic. `Europe/Warsaw` is **CET all winter and CEST all summer**, and
 * the changeover is the EU's single rule rather than a national one: summer time runs from 01:00
 * UTC on the **last Sunday in March** to 01:00 UTC on the **last Sunday in October**, for every
 * member state at the same instant.
 *
 * **Two falsifiers, and neither is hypothetical.** The first is ADR-0144's own — *the first shard
 * whose players are somewhere else* — and the second is the EU abolishing seasonal changes, which
 * has been proposed and not enacted. Either one makes this table wrong rather than imprecise,
 * which is why it is one function with a name that says what it is about.
 *
 * ## A calendar day is a string here, and that is deliberate
 *
 * `YYYY-MM-DD` is what the wire spells a day as, what a `DAY_RECORDED` line carries and what
 * `PUT /plans/{id}/day` takes. Turning it into a `Date` to move it about would put an instant —
 * and therefore a zone — back into a value that has neither, which is the bug every function here
 * exists to avoid. {@link daysAfter} does the arithmetic without ever leaving the calendar.
 */

import type { Weekday } from '@/shared/vocabulary/week';

/**
 * Named rather than computed with: **nothing passes this to a formatter**, for the reason the
 * module note gives. It is here so the assumption has a name a reader can search for, and so the
 * two halves of it — *this zone*, and *these two offsets* — sit in one file rather than one being
 * implied by the other.
 */
export const PLATFORM_ZONE = 'Europe/Warsaw';

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;
const CET = HOUR;
const CEST = 2 * HOUR;

/** ISO weekday numbering, off `Date`'s Sunday-first `getUTCDay`. */
const ISO_WEEKDAYS: readonly Weekday[] = [7, 1, 2, 3, 4, 5, 6];

const CALENDAR_DAY = /^\d{4}-\d{2}-\d{2}$/;

/** The last Sunday of a month, at 01:00 UTC — the instant the EU changes its clocks. */
function lastSundayAtOneUtc(year: number, month: number): number {
  const lastDay = new Date(Date.UTC(year, month + 1, 0));

  return Date.UTC(year, month, lastDay.getUTCDate() - lastDay.getUTCDay(), 1);
}

/** How far ahead of UTC the platform's zone is at this instant. */
function platformOffset(at: number): number {
  const year = new Date(at).getUTCFullYear();
  const summerBegins = lastSundayAtOneUtc(year, 2);
  const summerEnds = lastSundayAtOneUtc(year, 9);

  return at >= summerBegins && at < summerEnds ? CEST : CET;
}

/** `YYYY-MM-DD` for a `Date` read at UTC — the one spelling every function here answers in. */
function spell(at: Date): string {
  const pad = (value: number) => String(value).padStart(2, '0');

  return `${at.getUTCFullYear()}-${pad(at.getUTCMonth() + 1)}-${pad(at.getUTCDate())}`;
}

/**
 * Which calendar day an instant falls on **in the platform's zone**, as `YYYY-MM-DD`.
 *
 * The conversion the day separator, the quick chips' *today* and the plan's day row all need:
 * **a device zone would put two people in one room on two different days**
 * ([`the-loop-screens.md`](../../../../docs/specs/the-loop/the-loop-screens.md) §3.3), and would
 * offer one of them a Saturday the other's horizon had already run past.
 *
 * It answers `undefined` for a value that is not an instant, which is the same nothing every
 * other narrowing here answers with: there is no day to name, and inventing one would be a claim
 * about when something happened.
 */
export function platformDay(instant: string): string | undefined {
  const at = Date.parse(instant);
  if (Number.isNaN(at)) return undefined;

  // The wall clock in Warsaw, read as though it were UTC — which is what turns an instant into a
  // square on a calendar, and the one step that must not consult the device.
  return spell(new Date(at + platformOffset(at)));
}

/**
 * Which weekday a calendar day falls on, or nothing where the value is not one.
 *
 * Read at UTC because the value **has no time in it**: `2026-09-12` names a square on a calendar,
 * and parsing it as an instant in the device's zone is what would let one room read Saturday on
 * one phone and Friday on another.
 */
export function weekdayOf(day: string): Weekday | undefined {
  if (!CALENDAR_DAY.test(day)) return undefined;

  const at = new Date(`${day}T00:00:00Z`);
  if (Number.isNaN(at.getTime())) return undefined;

  return ISO_WEEKDAYS[at.getUTCDay()];
}

/**
 * The calendar day `count` days after this one, or nothing where the value is not a calendar day.
 *
 * **Read and returned at UTC, so it never touches a zone.** A day plus a day is arithmetic on a
 * calendar rather than on a clock: adding twenty-four hours to a local instant is what gets a
 * row of chips wrong twice a year, and there is no instant here to get wrong.
 */
export function daysAfter(day: string, count: number): string | undefined {
  if (!CALENDAR_DAY.test(day)) return undefined;

  const at = new Date(`${day}T00:00:00Z`);
  if (Number.isNaN(at.getTime())) return undefined;

  return spell(new Date(at.getTime() + count * DAY));
}
