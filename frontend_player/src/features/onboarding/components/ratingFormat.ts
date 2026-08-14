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
 * Confidence is a whole percentage. It is the one rating figure with no decimals: the
 * engine's own precision does not survive being read as "28,4% sure", and nothing on the
 * screen compares two of them.
 */
export function formatConfidence(value: number): string {
  return `${Math.round(value)}%`;
}

/** How much σ a range-widener added — the same scale as the Level, so the same shape. */
export function formatSigma(value: number): string {
  return decimal(value);
}
