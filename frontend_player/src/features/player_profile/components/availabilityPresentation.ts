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
 *
 * ## The floor is in the eyebrow, not only in a grey button
 *
 * ADR-0102 made one tick of twenty-one required. The tag step's copy already settled where
 * a rule like that belongs — *"a player should learn how many tags are wanted by reading
 * the screen, not by being stopped by it"* — so the week states its floor in the chrome the
 * player reads before they start pressing, and the control names what is missing on top of
 * that. A dead control with no sentence anywhere is the shape this step must not take.
 *
 * **The number is spelled out here**, unlike the tag floor, and that is the backend's call:
 * the availability minimum is not served, it is fixed, so there is no figure to wait for
 * and quote. These sentences say *one* in words because a rule a player reads is a sentence
 * rather than a figure — the rule itself is `weekStanding`'s, and nothing here decides it.
 */

import type { AvailabilitySlot, DayPart, Weekday } from '../domain/ProfileDraft';
import type { WeekStanding } from '../domain/availabilityWeek';

import { stepEyebrow } from './socialStepPresentation';

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
 * The step's eyebrow, carrying **the rule as well as the position**.
 *
 * The precedent is `socialTagsEyebrow`: a required answer is something a player should meet
 * by reading the screen rather than by being stopped by it. No served number to wait for
 * here — the floor is one and fixed — so this is unconditional, where the tag one falls
 * back to the plain position line until the bounds arrive.
 */
export function availabilityEyebrow(): string {
  return `${stepEyebrow('availability')} · Tick at least one`;
}

/**
 * What the continue control says.
 *
 * A blocked control names what is missing rather than merely being grey, exactly as the tag
 * step's does. There is no countdown to run: the floor is one, so the control is either
 * asking for a tick or it is not.
 */
export function availabilityContinueLabel(standing: WeekStanding): string {
  return standing.kind === 'empty' ? 'Tick at least one slot to continue' : 'Continue';
}

/**
 * The line under the grid — what a blank week means, or the count.
 *
 * Onboarding does not draw this any more; the profile editor will, and that is a screen
 * where a week genuinely can be emptied again. **So the blank line no longer names a cost,
 * because there is not one to name.** It used to say *it leaves no overlap for anyone to
 * share* — a measured zero invented out of silence, which is precisely the reading ADR-0102
 * withdrew. A week nobody gave is *absent*: it is left out of the matching rather than
 * counted against the player, and the half that survives unchanged is the one that always
 * mattered — never *unavailable*.
 */
export function availabilityFootnote(standing: WeekStanding): string {
  if (standing.kind === 'empty') {
    return 'Nothing ticked means we do not know when you play, never that you are unavailable.';
  }
  const slots = standing.count === 1 ? '1 slot' : `${standing.count} slots`;
  return `${slots} ticked. Overlap with another player is counted from these.`;
}
