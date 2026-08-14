/**
 * Where a signed-in player belongs on launch.
 *
 * This is the whole entry gate as a pure function, which is the point: routing a player
 * into a flow they cannot leave is a business rule, and a rule expressed as a chain of
 * `if` statements inside a layout is a rule nobody can test.
 *
 * The order is deliberate and not arbitrary:
 *
 *   run in progress  -> resume it, at its outstanding question
 *   no ratings at all -> onboarding, from welcome
 *   otherwise         -> the app
 *
 * **An unfinished run outranks an existing rating**, because a player rated at padel with
 * a tennis run half-answered should land back in the tennis questionnaire, not in the app
 * with those answers stranded.
 *
 * The two inputs answer genuinely different questions and neither substitutes for the
 * other: one asks whether a *run* is unfinished, the other whether a *rating exists*.
 */

import type { AssessmentRun } from "./Assessment";
import type { SkillRating } from "./SkillRating";

export type EntryDestination =
  /** The authenticated tree. Onboarding is behind them, at least for one sport. */
  | { readonly kind: "app" }
  /** Onboarding from the beginning: what it produces, then the sports picker. */
  | { readonly kind: "welcome" }
  /** Straight back to the outstanding question of a run they already started. */
  | { readonly kind: "resume"; readonly run: AssessmentRun };

export interface EntryInput {
  readonly ratings: readonly SkillRating[];
  readonly runInProgress: AssessmentRun | undefined;
}

export function entryDestination({ ratings, runInProgress }: EntryInput): EntryDestination {
  if (runInProgress !== undefined) return { kind: "resume", run: runInProgress };
  if (ratings.length === 0) return { kind: "welcome" };
  return { kind: "app" };
}
