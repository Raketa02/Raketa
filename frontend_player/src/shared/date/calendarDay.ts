/**
 * **A calendar day, spelled** — the one formatter for the `YYYY-MM-DD` value this platform
 * arranges games on, and the shape of that value, shared with the zone conversions beside it.
 *
 * A calendar day is a string with **no instant in it** (`platformZone.ts` — *"a calendar day is
 * a string here, and that is deliberate"*), so nothing here touches a zone: `2026-08-09` is the
 * ninth of August on every phone, and turning it into a `Date` to ask would be the one step that
 * could put two people in one room on two different dates. `docs/architecture.md` Part 11 puts
 * every date formatter in `src/shared/`, which is why this is here rather than beside the one
 * card that draws it.
 */

/** `YYYY-MM-DD`, and nothing else reaches either table. Read by the zone conversions too. */
export const CALENDAR_DAY = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * The months, short — one row beside a weekday that is already whole.
 *
 * **The first month names in this app.** The Now card's `DAY` slot is the first surface to draw
 * a date ([#413](https://github.com/Rakieta02/Rakieta/issues/413)); §5.4 refused one on the game
 * screen because *the horizon is seven chips, so a weekday is exact*, and the design wins on the
 * card.
 */
const MONTH_SHORT: readonly string[] = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

/**
 * **The date beside the weekday** — `9 Aug`: the day of the month with no leading zero and the
 * month short. Read off the string and in no zone, exactly as `weekdayOf` reads the weekday.
 *
 * A value that is not a calendar day is printed as it stands, which is `dayChipName`'s own
 * fall-back for the weekday — the belt rather than the braces, since the mapper would already
 * have dropped it.
 */
export function dayDate(day: string): string {
  const match = CALENDAR_DAY.exec(day);
  if (match === null) return day;

  const month = MONTH_SHORT[Number(match[2]) - 1];
  if (month === undefined) return day;

  return `${Number(match[3])} ${month}`;
}
