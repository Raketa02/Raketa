/**
 * What a day, an hour and one cell of the week are called.
 *
 * **Every name here exists because a cell carries its fact in a drawing.** The grid
 * announces a cell's day and hour, because the row it is in and the column it is under are
 * decoration to assistive technology
 * ([6.8](../../../docs/design-system.md#68-the-availability-grid)).
 *
 * **The full day is drawn outside the grid too.** A conversation's plan lines name a weekday in
 * a sentence, so `dayName` is exported beside the grid's own two — the same table, not a fourth
 * list of names ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * It was `player_profile/components/availabilityPresentation.ts` while the grid was the only
 * thing that named a day. Play is the **third** caller — an availability-overlap reason line
 * names the next shared cell, *next Tue 19:00* — so the tables are promoted rather than
 * copied ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1, §18). The
 * step's own sentences — the promise note, the eyebrow, the footnote, the continue control —
 * stayed behind: they are about a rule that step enforces, and they quote a count only that
 * step holds.
 */

import type { Hour, Weekday, WeeklyHour } from './week';

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
 * The day, short, for a column head seven share across the grid.
 *
 * Three letters rather than one: `T` and `S` each name two days, and a head that made a
 * player count columns to tell Tuesday from Thursday would have saved nothing worth having.
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

export function dayLabel(day: Weekday): string {
  return DAY_SHORT[day];
}

/**
 * The day **whole** — *Saturday*.
 *
 * Drawn where a day is a fact in a sentence rather than a column in a grid: a conversation's
 * *{name} set the day · {value}* names one, and the plan card's filled day slot is the same word
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §22.2, §23). It reads the
 * table {@link cellLabel} already spells rather than a third list of names, which is this file's
 * whole reason for existing.
 */
export function dayName(day: Weekday): string {
  return DAY_NAME[day];
}

/**
 * The hour a row starts at, on the 24-hour clock and to the minute — *07:00*, *19:00*.
 *
 * Padded to two digits because the row labels are a column of figures read down the grid, and
 * `7:00` above `10:00` would put the colons out of line. The minutes are always `:00`: a cell
 * is a whole hour and nothing finer is held.
 */
export function hourLabel(hour: Hour): string {
  return `${String(hour).padStart(2, '0')}:00`;
}

/**
 * What one cell is called: **its day and the hour it starts at**, and nothing else —
 * *Monday 19:00*.
 *
 * Whether it is ticked is `accessibilityState.checked`'s to say — a name that carried the
 * state would announce it twice, and a `checkbox` whose name changed as it was pressed is
 * a different control every time it is read.
 */
export function cellLabel(cell: WeeklyHour): string {
  return `${DAY_NAME[cell.day]} ${hourLabel(cell.hour)}`;
}
