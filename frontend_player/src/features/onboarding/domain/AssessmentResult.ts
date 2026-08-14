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
 * The Confidence ceiling onboarding cannot exceed.
 *
 * A domain constant, not a design value: the questionnaire is the entire evidence surface
 * and self-report has an irreducible ceiling, **enforced as a floor on σ rather than as a
 * display cap** — so this is not a number the client clamps anything to. It is what the
 * confidence ring's tick marks, which is why the ring is *told* where its ceiling sits
 * rather than knowing.
 *
 * It is not on the wire. `CONTEXT.md` states it as an invariant of the rating context and
 * the engine holds it as `CONFIDENCE_CAP`; this is the third place it is written down, and
 * a rating whose confidence exceeded it would be the engine contradicting the glossary
 * rather than this constant being stale.
 */
export const ONBOARDING_CONFIDENCE_CEILING = 30;

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
  /** 0-100, at or below {@link ONBOARDING_CONFIDENCE_CEILING} for every onboarding run. */
  readonly confidence: number;
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
