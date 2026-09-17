/**
 * **What the Skill passport decides about a rating's card** — one rule, about the ring's tick
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2: *the confidence ring with its ceiling tick on an Initial estimate*).
 *
 * The result screen draws the tick wherever a ceiling was served, because a run's result is
 * always the questionnaire's own. The passport draws ratings that matches may since have
 * moved, and a rating that has left its Initial estimate is no longer bound by the ceiling —
 * so the tick would state a limit that no longer applies. The rule takes the status and the
 * ceiling, and answers where the tick sits or that there is none.
 *
 * **The ceiling is told, never known.** `GET /ratings` serves none today, so every passport
 * card draws no tick; the rule is written for the day the read carries the number, and a
 * constant here would be the copy 7.8's amendment removed.
 */

/** Every rating leaves onboarding at this status; the two after it are matches' doing. */
const INITIAL_ESTIMATE = 'initial_estimate';

export interface PassportRating {
  /** Machine-readable, as served. */
  readonly status: string;
  /** Where the questionnaire's ceiling sits, where the read served one. */
  readonly confidenceCeiling?: number | undefined;
}

export function passportCeiling(rating: PassportRating): number | undefined {
  if (rating.status !== INITIAL_ESTIMATE) return undefined;
  return rating.confidenceCeiling;
}
