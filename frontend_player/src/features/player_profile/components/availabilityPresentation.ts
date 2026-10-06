/**
 * The words the availability **step** says about the week it collects.
 *
 * **The step says what it is not.** A week of hours looks enough like a diary that a
 * player could reasonably think they were promising to turn up, so the screen states in as
 * many words that this is a preference and not a promise, and that nobody ever sees it as a
 * calendar. That is the same obligation the photos step's copy carries about what is and is
 * not checked: the one kind of copy defect that survives a redesign, because nobody
 * re-reads a sentence they believe.
 *
 * **What a day and a cell are called moved to
 * [`@/shared/vocabulary/availabilityPresentation`](../../../shared/vocabulary/availabilityPresentation.ts)**
 * — Play names the next cell two players share inside a reason line, which made this the
 * third caller of one table of seven days
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1). What stayed is
 * what this step says about its own rule.
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
 * ADR-0102 made one ticked hour required. The tag step's copy already settled where
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

import type { WeekStanding } from '../domain/availabilityWeek';

import { stepEyebrow } from './socialStepPresentation';

/** The one thing this step must not let a player misread about their own answer. */
export const AVAILABILITY_PROMISE_TITLE = 'A preference, not a promise';

/**
 * **It promises nothing the step has not been given.** It names what the week is *for* (how
 * much of it another player shares) rather than what the platform will do about it, and the
 * overlap is the only thing anybody is ever shown.
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
  return `${stepEyebrow('availability')} · Pick at least one hour`;
}

/**
 * What the continue control says.
 *
 * A blocked control names what is missing rather than merely being grey, exactly as the tag
 * step's does. There is no countdown to run: the floor is one, so the control is either
 * asking for an hour or it is not.
 */
export function availabilityContinueLabel(standing: WeekStanding): string {
  return standing.kind === 'empty' ? 'Pick at least one hour to continue' : 'Continue';
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
  const hours = standing.count === 1 ? '1 hour' : `${standing.count} hours`;
  return `${hours} ticked. Overlap with another player is counted from these.`;
}
