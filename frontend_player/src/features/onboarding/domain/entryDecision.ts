/**
 * Where a signed-in player belongs on launch.
 *
 * This is the whole entry gate as a pure function, which is the point: routing a player
 * into a flow they cannot leave is a business rule, and a rule expressed as a chain of
 * `if` statements inside a layout is a rule nobody can test.
 *
 * The order is deliberate and not arbitrary:
 *
 *   any rating at all              -> the app
 *   run in progress, not set aside -> resume it, at its outstanding question
 *   otherwise                      -> onboarding, from welcome
 *
 * **A rating outranks an unfinished run, and it did not always.** The original order
 * resumed a run whatever else the player held, on the argument that *"a player rated at
 * padel with a tennis run half-answered should land back in the tennis questionnaire, not
 * in the app with those answers stranded."* That argument is **right about the player it
 * was written for and wrong about the one the door creates** (`ADR-0084`): four squash
 * questions answered on a tram must never stand between a player and the padel match she
 * has paid for. Nothing is stranded any more, because the run **parks** and Now's door is
 * the way back into it — continuing where it stopped, however old.
 *
 * So a run in progress takes the screen only for a player holding **no rating at all**,
 * for whom there is no app to be kept out of and no door to be shown, and for whom this is
 * still the first walk through onboarding.
 *
 * The first two inputs answer genuinely different questions and neither substitutes for
 * the other: one asks whether a *run* is unfinished, the other whether a *rating exists*.
 *
 * The third is the player's own decision, and it is the only reason this gate is not a
 * trap. A run they asked to come back to later is still unfinished — the server is right
 * — and resuming it the instant they leave would mean the questionnaire had no exit.
 * The deferral lasts one app session, so the next launch resumes exactly as it should;
 * the permanent way out is abandonment, which changes the run rather than the routing.
 * It survives for exactly the case it was built for: a player with nothing, who has no
 * other way out of the questionnaire.
 */

import type { AssessmentRun } from './Assessment';
import type { SkillRating } from './SkillRating';

export type EntryDestination =
  /** The authenticated tree. Onboarding is behind them, at least for one sport. */
  | { readonly kind: 'app' }
  /** Onboarding from the beginning: what it produces, then the sports picker. */
  | { readonly kind: 'welcome' }
  /** Straight back to the outstanding question of a run they already started. */
  | { readonly kind: 'resume'; readonly run: AssessmentRun };

export interface EntryInput {
  readonly ratings: readonly SkillRating[];
  readonly runInProgress: AssessmentRun | undefined;
  /** Runs the player chose to come back to later, since this launch. */
  readonly deferredRunIds: readonly string[];
}

export function entryDestination({
  ratings,
  runInProgress,
  deferredRunIds,
}: EntryInput): EntryDestination {
  if (ratings.length > 0) return { kind: 'app' };
  if (runInProgress !== undefined && !deferredRunIds.includes(runInProgress.assessmentId)) {
    return { kind: 'resume', run: runInProgress };
  }
  return { kind: 'welcome' };
}
