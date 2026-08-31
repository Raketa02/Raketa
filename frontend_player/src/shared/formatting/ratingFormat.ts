/**
 * The rating's numbers, as they are written.
 *
 * **Comma decimals, two places** (design-system Appendix B). Every figure here is drawn in
 * a mono, tabular role, which is the mechanism that stops a row reflowing when a level goes
 * from 2,71 to 2,80 — the formatting is only the other half of it.
 *
 * `toFixed` and a substitution rather than `toLocaleString`: Hermes ships without the full
 * ICU data unless it is explicitly built in, so a locale-aware formatter would produce a
 * comma on one device and a point on another for the same rating. This is a **house
 * convention**, not a localisation — when the app is genuinely localised it becomes one,
 * in one place, which is here.
 *
 * **It is in `shared/` because a level is printed wherever a player is.** It was
 * `onboarding/components/` while the result screen was the only thing that drew one; Play
 * prints a level on every card, in every reason line about a level gap, and on every seat of
 * a court, and ESLint blocks a deep import between features outright — so the two options
 * were promotion or a second copy of *two fixed decimals, decimal comma*. A second copy of
 * that is the drift the design system's *every number is mono and tabular* rule exists to
 * prevent ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §7).
 */

const DECIMALS = 2;

/** The en dash is the range dash, and it is spaced so two 4-character numbers stay apart. */
const RANGE_DASH = ' – ';

function decimal(value: number): string {
  return value.toFixed(DECIMALS).replace('.', ',');
}

/** A Level, an Uncertainty, a band edge — anything on the 1,00–5,00 scale. */
export function formatLevel(value: number): string {
  return decimal(value);
}

export function formatRange(range: { readonly low: number; readonly high: number }): string {
  return `${decimal(range.low)}${RANGE_DASH}${decimal(range.high)}`;
}

/**
 * A percentage — **whole, always**.
 *
 * A confidence, a forecast's evenness, a term's value read as a share: none of them survives
 * being read as "28,4% sure", the engine's own precision is not a fact about the pairing, and
 * nothing on any screen compares two of them closely enough for a decimal to answer a
 * question. One shape for every percentage in the app is §B16's rule; this is where it is.
 */
export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}
