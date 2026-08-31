/**
 * The week the platform reads: seven days, three parts of a day, and one cell of the grid.
 *
 * **Two features draw this week and neither owns it.** `player_profile` collects it as a
 * preference; Play reads it back as *overlap* — the count of cells two people both ticked
 * and the name of the next one. Both spell a cell the same way, and a second spelling of
 * *Tuesday evening* is the drift `recoveryMessage.ts`'s third-caller rule exists to stop
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1: Play must not
 * re-type `DayPart` or `Weekday`).
 *
 * **The wire spells a part `EVENING` and this app spells it `evening`**, which is the same
 * split `Sport` takes: the two meet in a feature's `mappers/`, and only there.
 */

/** Which part of a day one cell of the availability grid belongs to. */
export type DayPart = 'morning' | 'afternoon' | 'evening';

/** The three parts of the day, in the order `DayPart` declares them. */
export const DAY_PARTS: readonly DayPart[] = ['morning', 'afternoon', 'evening'];

/**
 * ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.
 *
 * A closed union rather than a `number`, for the same reason `DayPart` beside it is not a
 * string: seven is the whole of it, and a `day: 0` is a bug a type can refuse.
 */
export type Weekday = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/**
 * Monday first, as ISO weekdays.
 *
 * The order is the contract's as well as the design system's: `AvailabilitySlotResource`
 * numbers days 1-7 as ISO weekdays and says the grid is Monday-first, so nothing on either
 * side of the wire sorts.
 */
export const WEEKDAYS: readonly Weekday[] = [1, 2, 3, 4, 5, 6, 7];

/**
 * One cell of the grid: a day, and one of the three parts of it.
 *
 * The pair names a cell whatever its state — ticked on a profile, shared by a pair, or
 * neither — which is why the rules and the words both take one of these rather than a loose
 * day and part.
 */
export interface WeekCell {
  readonly day: Weekday;
  readonly part: DayPart;
}
