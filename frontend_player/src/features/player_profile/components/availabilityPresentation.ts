/**
 * The words on the availability step.
 *
 * **The step says what it is not.** A seven-by-three grid looks enough like a diary that a
 * player could reasonably think they were promising to turn up, so the screen states in as
 * many words that this is a preference and not a promise, and that nobody ever sees it as a
 * calendar. That is the same obligation the photos step's copy carries about what is and is
 * not checked: the one kind of copy defect that survives a redesign, because nobody
 * re-reads a sentence they believe.
 *
 * **Every accessible name here exists because a cell carries its fact in a drawing.** The
 * grid announces a cell's day and part of the day, because the row it is in and the column
 * it is under are decoration to assistive technology (design-system 6.8).
 *
 * The footnote's two messages share one reserved slot, and 6.8 caps it at two lines of
 * `tiny`. A third line is an amendment, not a copy tweak.
 *
 * **The onboarding step draws neither the promise note nor the footnote any more** — it is
 * the grid and nothing else. Both are kept here for the profile editor, which is where a
 * week is read back rather than given for the first time, and where a count of ticked slots
 * is something a player is actually looking for.
 */

import type { AvailabilitySlot, DayPart, Weekday } from '../domain/ProfileDraft';
import type { WeekStanding } from '../domain/availabilityWeek';

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
export function cellLabel(cell: AvailabilitySlot): string {
  return `${DAY_NAME[cell.day]} ${cell.part}`;
}

/** The one thing this step must not let a player misread about their own answer. */
export const AVAILABILITY_PROMISE_TITLE = 'A preference, not a promise';

/**
 * **It promises nothing the step has not been given.** Saying that games would be put in
 * front of the player would state as settled the consent step six has yet to collect — so
 * this names what the week is *for* (how much of it another player shares) rather than what
 * the platform will do about it, and the overlap is the only thing anybody is ever shown.
 */
export const AVAILABILITY_PROMISE_BODY =
  'Nobody ever sees this as a calendar and nothing here books anything. It says when you ' +
  'would usually rather play, so another player can tell how much of your week they share ' +
  '— you are never held to it.';

/**
 * The line under the grid — the consequence of a blank week, or the count.
 *
 * **The blank week's line is not a warning and it does not block anything.** It says what
 * blank means before it says what it costs, in that order, because a player who reads only
 * the first half must still come away with the true half: *no preference*, never
 * *unavailable*, and it excludes them from nothing.
 */
export function availabilityFootnote(standing: WeekStanding): string {
  if (standing.kind === 'empty') {
    return 'Nothing ticked means no preference, never unavailable. It leaves no overlap for anyone to share.';
  }
  const slots = standing.count === 1 ? '1 slot' : `${standing.count} slots`;
  return `${slots} ticked. Overlap with another player is counted from these.`;
}
