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
 * **The comparison is the only thing decided here, and both numbers come from the server.**
 * The ceiling is version-scoped and arrives on the result beside the Confidence it bound; a
 * copy held here would answer for an engine that has since been retuned, and would do it in
 * a build already on phones. The ceiling is a floor on σ rather than a display cap, so a
 * Confidence that reached it reached it in the arithmetic; this reads that arithmetic, it
 * does not repeat it.
 *
 * **A rating with no served ceiling has no answer here and must not be given one.** Its
 * engine has been retired, so what it *could* have proved is not knowable — the caller shows
 * no sentence, exactly as it shows none when the engine's own confidence reason is absent.
 * That is why this takes a ceiling rather than reaching for a default: there is no default
 * that would be true.
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

export type ConfidenceLimit =
  /** The questionnaire's own ceiling. The evidence would have supported more. */
  | 'ceiling'
  /** The answers themselves. The ceiling was never reached, so it bound nothing. */
  | 'evidence';

/**
 * @param confidence The Confidence the engine produced, 0–100.
 * @param ceiling The ceiling that engine served beside it, on the same scale.
 */
export function confidenceLimit(confidence: number, ceiling: number): ConfidenceLimit {
  return confidence >= ceiling ? 'ceiling' : 'evidence';
}
