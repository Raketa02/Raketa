/**
 * Where a signed-in player belongs on launch.
 *
 * This is the whole entry gate as a pure function, which is the point: routing a player
 * into a flow they cannot leave is a business rule, and a rule expressed as a chain of
 * `if` statements inside a layout is a rule nobody can test.
 *
 * The order is deliberate and not arbitrary:
 *
 *   run in progress, not set aside -> resume it, at its outstanding question
 *   no ratings at all              -> onboarding, from welcome
 *   no Player profile              -> onboarding's second part, from its first step
 *   otherwise                      -> the app
 *
 * **An unfinished run outranks an existing rating**, because a player rated at padel with
 * a tennis run half-answered should land back in the tennis questionnaire, not in the app
 * with those answers stranded.
 *
 * The first two inputs answer genuinely different questions and neither substitutes for
 * the other: one asks whether a *run* is unfinished, the other whether a *rating exists*.
 *
 * The third is the player's own decision, and it is the only reason this gate is not a
 * trap. A run they asked to come back to later is still unfinished — the server is right
 * — and resuming it the instant they leave would mean the questionnaire had no exit.
 * The deferral lasts one app session, so the next launch resumes exactly as it should;
 * the permanent way out is abandonment, which changes the run rather than the routing.
 *
 * ## The fourth destination, and why it is not the flag the glossary bans
 *
 * Onboarding is two parts ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)),
 * and **the part is the checkpoint unit**. The second part holds a client-side draft and
 * writes nothing until its final commit, so a player who reaches it and closes the app has
 * a Skill rating and no Player profile — and a gate reading only *is there a rating* sends
 * them into the app past the second part, permanently, with no route back to it.
 *
 * *Does a Player profile exist* is a per-player question with a per-player answer, which is
 * why it is allowed to be one. The glossary bans a per-player flag standing in for a fact
 * that is genuinely per sport, and its own test — *is this really asking whether a rating
 * exists for this sport?* — answers no here: tags, photos, a week, a location and a consent
 * have no sport dimension at all.
 *
 * **It is read after ratings, never before.** The second part is only reachable once the
 * first has produced something, so a brand-new account — no ratings, no profile — belongs
 * at welcome. Reading the profile first would open the social steps to a player who has not
 * been rated, which is the one shape the flow cannot produce.
 */

import type { AssessmentRun } from './Assessment';
import type { SkillRating } from './SkillRating';

export type EntryDestination =
  /** The authenticated tree. Onboarding is behind them, at least for one sport. */
  | { readonly kind: 'app' }
  /** Onboarding from the beginning: what it produces, then the sports picker. */
  | { readonly kind: 'welcome' }
  /**
   * Onboarding's second part, **from its first step**. Never from the middle: the draft is
   * client-held and starts empty, so a player dropped at step four would commit a profile
   * built from screens they never saw.
   */
  | { readonly kind: 'social-steps' }
  /** Straight back to the outstanding question of a run they already started. */
  | { readonly kind: 'resume'; readonly run: AssessmentRun };

export interface EntryInput {
  readonly ratings: readonly SkillRating[];
  readonly runInProgress: AssessmentRun | undefined;
  /** Runs the player chose to come back to later, since this launch. */
  readonly deferredRunIds: readonly string[];
  /**
   * Whether the second part has been committed. Served on the authenticated player rather
   * than fetched separately, and read from the profile's own event stream rather than from
   * a projection — so it is correct in the moment after the commit, which is exactly when
   * a lagging read model would send a player back into steps they just finished.
   */
  readonly hasPlayerProfile: boolean;
}

export function entryDestination({
  ratings,
  runInProgress,
  deferredRunIds,
  hasPlayerProfile,
}: EntryInput): EntryDestination {
  if (runInProgress !== undefined && !deferredRunIds.includes(runInProgress.assessmentId)) {
    return { kind: 'resume', run: runInProgress };
  }
  if (ratings.length === 0) return { kind: 'welcome' };
  if (!hasPlayerProfile) return { kind: 'social-steps' };
  return { kind: 'app' };
}
