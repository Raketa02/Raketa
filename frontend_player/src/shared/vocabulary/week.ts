/**
 * The week the platform reads: seven days, sixteen hours, and one **weekly hour** — a cell of
 * the grid.
 *
 * **Two features draw this week and neither owns it.** `player_profile` collects it as a
 * preference; Play reads it back as *overlap* — the count of hours two people both ticked and
 * the name of the next one. Both spell an hour the same way, and a second spelling of
 * *Tuesday 19:00* is the drift `recoveryMessage.ts`'s third-caller rule exists to stop
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1: Play must not re-type
 * `Weekday`).
 *
 * **Hours, since [ADR-0189](../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
 * §5.** The week was seven days by three parts of the day until a court began to be booked by
 * the hour; a player is now free for a game only when its whole hour is inside their week, so
 * the week is held at that precision and at no finer one (the glossary's *Weekly hours*).
 */

/**
 * The wall-clock hour a cell **starts** at — 7 is 07:00 to 08:00, 22 is 22:00 to 23:00.
 *
 * A closed union rather than a `number`, for the reason `Weekday` beside it is one: sixteen is
 * the whole of it, and a `hour: 23` is a cell the grid does not have and a type can refuse.
 */
export type Hour = 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22;

/** The sixteen hours of the week's day, 07:00 to 23:00, in the order a day runs. */
export const HOURS: readonly Hour[] = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22];

/**
 * ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.
 *
 * A closed union rather than a `number`: seven is the whole of it, and a `day: 0` is a bug a
 * type can refuse.
 */
export type Weekday = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/**
 * Monday first, as ISO weekdays.
 *
 * The order is the contract's as well as the design system's: `WeeklyHourResource` numbers
 * days 1-7 as ISO weekdays and says the grid is Monday-first, so nothing on either side of the
 * wire sorts.
 */
export const WEEKDAYS: readonly Weekday[] = [1, 2, 3, 4, 5, 6, 7];

/**
 * One **weekly hour**: a day, and the hour its cell starts at — Tuesday 19:00 is 19:00 to
 * 20:00.
 *
 * The pair names a cell whatever its state — ticked on a profile, shared by a pair, or
 * neither — which is why the rules and the words both take one of these rather than a loose
 * day and hour.
 */
export interface WeeklyHour {
  readonly day: Weekday;
  readonly hour: Hour;
}

/**
 * The hours drawn at places on the week grid — **the hours run down and the days across**,
 * 07:00 and Monday in the top corner (design-system 6.8, mock 36) — in the order given, with a
 * place the grid does not have left out.
 *
 * Here because every screen that draws the grid builds its rows from `HOURS` and its cells from
 * `WEEKDAYS`, and the grid reports a drag by where it drew the cells it crossed: turning those
 * places back into hours is the same fact read the other way, written once. A place is any
 * `{ row, column }`, so this folder need not know the grid's own type for one.
 */
export function weeklyHoursAt(
  places: readonly { readonly row: number; readonly column: number }[],
): readonly WeeklyHour[] {
  return places.flatMap(({ row, column }) => {
    const hour = HOURS[row];
    const day = WEEKDAYS[column];
    return hour === undefined || day === undefined ? [] : [{ day, hour }];
  });
}

/**
 * Whether two cells are the same cell — the identity every rule over a week turns on.
 *
 * A day and an hour together, never either alone: Tuesday 09:00 and Tuesday 19:00 are two
 * cells, and a comparison that read only the day would tick both.
 */
export function sameCell(one: WeeklyHour, other: WeeklyHour): boolean {
  return one.day === other.day && one.hour === other.hour;
}

/** Whether a week has this cell ticked. */
export function isTicked(week: readonly WeeklyHour[], cell: WeeklyHour): boolean {
  return week.some((ticked) => sameCell(ticked, cell));
}

/**
 * Press a cell: tick it, or untick it.
 *
 * Ticks are kept in **press order**. What a player ticked first is a fact about them, and
 * re-sorting into the grid's own order would throw it away before anything downstream saw it.
 *
 * **Here rather than in either feature**, on this folder's own test — *"whether a second
 * feature would have written the identical table"*. `player_profile` toggles these cells for
 * the availability step and Play toggles them for the week it searches on, and the second one
 * was written identically to the first. What is **not** here is what either feature means by a
 * toggle: the step's floor of one ticked hour is `player_profile`'s rule, and whether the week
 * still matches the profile is Play's.
 */
export function toggleCell(week: readonly WeeklyHour[], cell: WeeklyHour): readonly WeeklyHour[] {
  if (isTicked(week, cell)) return week.filter((ticked) => !sameCell(ticked, cell));
  return [...week, cell];
}

/**
 * A drag across the grid: every cell of `run` made `on`, or made off.
 *
 * **Painting is not toggling a run.** A drag that began on an unticked hour ticks every hour
 * it crosses, and leaves the ones already ticked as they were; one that began on a ticked hour
 * clears them. Which of the two it is, is the first cell's to say and the grid's to report —
 * this only lands it.
 *
 * **Idempotent, on purpose.** The grid reports the run painted so far, whole, on every move,
 * so the same hours arrive again and again, one longer each time. Painting a run twice is
 * painting it once — which is what lets a screen one render behind the finger paint from the
 * week it has and still land every hour the drag crossed. New ticks go on the end in the order
 * the finger crossed them, as `toggleCell`'s press order does.
 */
export function paintCells(
  week: readonly WeeklyHour[],
  run: readonly WeeklyHour[],
  on: boolean,
): readonly WeeklyHour[] {
  if (!on) return week.filter((ticked) => !isTicked(run, ticked));
  return run.reduce<readonly WeeklyHour[]>(
    (painted, cell) => (isTicked(painted, cell) ? painted : [...painted, cell]),
    week,
  );
}
