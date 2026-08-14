/**
 * What held a rating's Confidence where it is: the ceiling, or the evidence.
 *
 * These are two different statements about a player and only one of them is true of any
 * given rating, so a screen that shows several ratings together has to tell them apart —
 * otherwise a 30% and a 12% are presented as the same kind of fact, and the player is left
 * to conclude the difference was about them.
 *
 * **The ceiling is a floor on σ, applied before anything else** (`CONTEXT.md`). A rating
 * whose evidence would have been tighter than self-report can honestly prove therefore
 * lands *exactly* on the ceiling: nothing in the answers held it back, and the honest
 * sentence is that a questionnaire cannot prove more. A rating below the ceiling was held
 * there by the evidence itself — thin answers, time away, or answers that disagreed — and
 * the engine's own confidence sentence says which of those it was.
 *
 * **The comparison is the only thing decided here, and it is decided against the number
 * the engine sent.** The ceiling is a domain constant rather than a display cap, so a
 * Confidence that reached it reached it in the arithmetic; this reads that arithmetic, it
 * does not repeat it.
 *
 * Two things it is deliberately **not**:
 *
 * - **Not "did anything widen the range".** A beginner who answered one question has no
 *   widener at all and still sits far below the ceiling, because thin evidence is the
 *   absence of evidence rather than a widener. Reading the wideners would tell that player
 *   the ceiling was their limit, which is exactly the wrong sentence.
 * - **Not `===`.** Confidence arrives as a whole percent, and a rating that somehow
 *   arrived above the ceiling is one this rule must never describe as evidence-limited.
 */

import { ONBOARDING_CONFIDENCE_CEILING } from './AssessmentResult';

export type ConfidenceLimit =
  /** The questionnaire's own ceiling. The evidence would have supported more. */
  | 'ceiling'
  /** The answers themselves. The ceiling was never reached, so it bound nothing. */
  | 'evidence';

export function confidenceLimit(confidence: number): ConfidenceLimit {
  return confidence >= ONBOARDING_CONFIDENCE_CEILING ? 'ceiling' : 'evidence';
}
