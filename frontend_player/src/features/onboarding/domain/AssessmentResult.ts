/**
 * What a finished run produced: a Skill rating, and the account it gives of itself.
 *
 * **A rating explains itself, and the explanation is computed, never authored**
 * (`CONTEXT.md`). Every label, detail and sentence below is copy the *server* wrote, so
 * wording can be corrected without an App Store release; every direction is the engine
 * comparing one category's own evidence against the final estimate, so retuning a constant
 * moves the explanation with it. The client renders. It does not derive, re-order or
 * second-guess any of this.
 *
 * The two halves are deliberately kept apart, because they answer different questions.
 * **Something that widened the range did not move the level**, and presenting them together
 * would describe a different rating than the one produced.
 */

import type { Band, LikelyRange } from './SkillRating';

/**
 * One evidence category, fused on its own evidence, and where that sits relative to the
 * estimate the player was given.
 *
 * `direction` is the engine's word — `up` / `down` / `neutral` today — and is carried
 * across as it arrives. A direction this build does not recognise renders without a mark
 * rather than with a guessed one: a client-side arrow is a second opinion about the
 * arithmetic, and two clients would eventually hold two of them.
 */
export interface EvidenceContribution {
  readonly key: string;
  readonly label: string;
  readonly direction: string;
  readonly level: number;
}

/**
 * Something that widened the range instead of moving the estimate — a layoff, a
 * contradiction, an uneven profile — reporting how much uncertainty it actually added.
 *
 * **It has no direction, and none may be invented for it.**
 */
export interface RangeWidener {
  readonly key: string;
  readonly label: string;
  readonly detail: string;
  /** How much σ this added. The rows add up to the range the player sees. */
  readonly sigmaAdded: number;
}

/** Why Confidence landed where it did: a stable key, and the sentence to show. */
export interface ConfidenceReason {
  readonly key: string;
  readonly sentence: string;
}

export interface AssessmentResult {
  /** The Level. `mu` on the wire. */
  readonly level: number;
  /** The Uncertainty. `sigma` on the wire. */
  readonly uncertainty: number;
  /** 0-100, at or below {@link AssessmentResult.confidenceCeiling} for every onboarding run. */
  readonly confidence: number;
  /**
   * The highest Confidence the engine that produced this rating could reach, as a whole
   * percent. It is what the ring's tick marks and what `confidenceLimit` reads a Confidence
   * against.
   *
   * **Served, never held.** The questionnaire is the entire evidence surface and self-report
   * has an irreducible ceiling (`CONTEXT.md`), enforced as a floor on σ rather than as a
   * display cap — so nothing here clamps anything to it. It is *version-scoped*: a copy in
   * the bundle would be a number nothing can keep honest, and it would be wrong the first
   * time the engine retuned, in a build already on phones.
   *
   * `undefined` for a rating replayed from an engine version that has since been retired —
   * exactly the case that carries no {@link AssessmentResult.confidenceReason}. Such a rating
   * keeps its numbers and loses its explanation, and what a *retired* engine could prove is
   * part of that explanation. **Draw no tick and say nothing about the ceiling. Never fall
   * back to a constant**, which would be wrong in the one case it fired.
   */
  readonly confidenceCeiling: number | undefined;
  readonly range: LikelyRange;
  readonly band: Band;
  /** `initial_estimate` after onboarding. Machine-readable; never rendered raw. */
  readonly status: string;
  readonly questionsAsked: number;
  /** Which engine produced it, so a retune can be attributed and falsified. */
  readonly engineVersion: string;
  /** How urgently this estimate wants real matches. A property of the estimate, never of
   *  the player. `standard` / `elevated` today. */
  readonly calibrationPriority: string;
  readonly confidenceReason: ConfidenceReason | undefined;
  /** What moved the Level. Empty is possible and is not a failure. */
  readonly contributions: readonly EvidenceContribution[];
  /** What widened the range. Empty is the ordinary case. */
  readonly wideners: readonly RangeWidener[];
}
