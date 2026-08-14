/**
 * A Skill rating, as this app reads it back.
 *
 * A rating is never only a number. It is a **Level** inside a **likely range**, with a
 * **Confidence** and a **Band** — two players both showing 3,0 at very different
 * Uncertainties are not the same player, and nothing in this app may present one as if it
 * were.
 *
 * **Band boundaries come from the response.** They are deliberately uneven and were wrong
 * once already; restating them anywhere in the client is how the two copies disagree.
 */

import type { Sport } from "./Sport";

export interface LikelyRange {
  readonly low: number;
  readonly high: number;
}

export interface Band {
  readonly name: string;
  /** The Band's own edges, as the engine defines them. Never hard-coded here. */
  readonly lower: number;
  readonly upper: number;
}

export interface SkillRating {
  readonly sport: Sport;
  /** The Level. `mu` on the wire. */
  readonly level: number;
  /** The Uncertainty. `sigma` on the wire. */
  readonly uncertainty: number;
  /** 0-100. Onboarding never exceeds 30, which the result screen explains. */
  readonly confidence: number;
  readonly range: LikelyRange;
  readonly band: Band;
  /** `initial_estimate` after onboarding. Machine-readable; never rendered raw. */
  readonly status: string;
  /** Which engine produced it, so a retune can be attributed and falsified. */
  readonly engineVersion: string;
  /** ISO-8601 instant, as the backend sent it. Parsed at the presentation boundary. */
  readonly updatedAt: string;
}
