/**
 * What a day, a part of a day and one cell of the week are called.
 *
 * **Every name here exists because a cell carries its fact in a drawing.** The grid
 * announces a cell's day and part of the day, because the row it is in and the column it is
 * under are decoration to assistive technology
 * ([6.8](../../../docs/design-system.md#68-the-availability-grid)).
 *
 * It was `player_profile/components/availabilityPresentation.ts` while the grid was the only
 * thing that named a day. Play is the **third** caller — an availability-overlap reason line
 * names the next shared cell, *next Tue evening* — so the tables are promoted rather than
 * copied ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1, §18). The
 * step's own sentences — the promise note, the eyebrow, the footnote, the continue control —
 * stayed behind: they are about a rule that step enforces, and they quote a count only that
 * step holds.
 */

import type { DayPart, Weekday, WeekCell } from './week';

/** The full day, for the name a cell announces. Nothing abbreviates when it is spoken. */
const DAY_NAME: Readonly<Record<Weekday, string>> = {
  1: 'Monday',
  2: 'Tuesday',
  3: 'Wednesday',
  4: 'Thursday',
  5: 'Friday',
  6: 'Saturday',
  7: 'Sunday',
};

/**
 * The day, short, for a label column capped at a quarter of the content width.
 *
 * Three letters rather than one: `T` and `S` each name two days, and a column that made a
 * player count rows to tell Tuesday from Thursday would have saved nothing worth having.
 */
const DAY_SHORT: Readonly<Record<Weekday, string>> = {
  1: 'Mon',
  2: 'Tue',
  3: 'Wed',
  4: 'Thu',
  5: 'Fri',
  6: 'Sat',
  7: 'Sun',
};

const DAY_PART_HEAD: Readonly<Record<DayPart, string>> = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
};

export function dayLabel(day: Weekday): string {
  return DAY_SHORT[day];
}

export function dayPartHead(part: DayPart): string {
  return DAY_PART_HEAD[part];
}

/**
 * What one cell is called: **its day and its part of the day**, and nothing else.
 *
 * Whether it is ticked is `accessibilityState.checked`'s to say — a name that carried the
 * state would announce it twice, and a `checkbox` whose name changed as it was pressed is
 * a different control every time it is read.
 */
export function cellLabel(cell: WeekCell): string {
  return `${DAY_NAME[cell.day]} ${cell.part}`;
}

/**
 * A cell **named inside a sentence** — *Tue evening*.
 *
 * The short day, because this one is read in a line of prose beside other facts rather than
 * alone in a grid, and the part in lower case for the same reason: it is a phrase, not a
 * heading. The one caller today is the availability-overlap reason line's *next {slot}*,
 * which is why it is built from these two tables rather than from a third list of names
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §6.2).
 */
export function slotName(cell: WeekCell): string {
  return `${DAY_SHORT[cell.day]} ${cell.part}`;
}
