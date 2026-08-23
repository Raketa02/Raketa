/**
 * The fit badge, in this app's vocabulary — a number, a warning and its reasons.
 *
 * `ADR-0037` decides four things about it, and three of them land here:
 *
 * - **The badge always prints a number, clamped 20–99 at display time.** The engine
 *   keeps its measured 0–100 range and the true value ranks the list; the pill never
 *   shows an 8 or a 100. The two reasons are the product's, not the arithmetic's —
 *   *"a score of 3 is not more useful than a score of 20 — both mean no"*, and never
 *   100 *"because certainty is never warranted"* — which is why the bound is applied
 *   where the wire is read rather than asked of the server. It is the same rule the
 *   rating context already holds for Confidence.
 * - **Up to three reasons**, already resolved to sentences. The server sends a term
 *   code and a typed fact payload and never a sentence, so the words are this app's
 *   and re-wording one is a client release rather than a backend one.
 * - **Coverage is never a number the player sees, in any form.** It ranks, it gates
 *   emphasis, and it may become *words* — which is what `unsure` is. There is no
 *   field for it here because there is no field for it on the wire either, and
 *   `nowMappers.ts` pins that with a type-level assertion rather than a comment.
 *
 * The fourth — **at most one card on the screen is emphatic** — is not here, because
 * it is not a fact about a badge at all: it depends on the other cards, so it is a
 * property of the composed screen (`ADR-0032`) and arrives as a flag on the card.
 *
 * **The true score never enters this app.** Clamping in the mapper rather than in
 * the component means there is exactly one number in the client, and no later
 * session can print an unclamped one by reaching past a component that clamped.
 */

/**
 * The display floor. Below it every score means *no*, and saying so with a
 * different number is precision the player cannot use.
 */
export const BADGE_MIN = 20;

/** The display ceiling. Nothing scores 100, because certainty is never warranted. */
export const BADGE_MAX = 99;

/** How many reasons a card may carry. The server sends at most this many; the client
 *  takes at most this many, so a server that one day sends four grows a card here
 *  instead of on somebody's phone. */
export const MAX_REASONS = 3;

/** `ADR-0037`'s display rule, and the only arithmetic this feature does to a score. */
export function clampBadgeScore(score: number): number {
  return Math.min(BADGE_MAX, Math.max(BADGE_MIN, Math.round(score)));
}

/**
 * What the badge claims, and what stands behind it.
 *
 * `unsure` is a boolean and never a percentage: a second gauge on the card is the
 * thing `ADR-0037` refused, and the client turns the boolean into a warning line.
 * `reasons` are sentences rather than codes, because resolving a code to copy is
 * `mappers/`' job and `domain/` may not name a generated union.
 */
export interface FitBadge {
  /** Already clamped to `BADGE_MIN`–`BADGE_MAX`. There is no other score here. */
  readonly score: number;
  readonly unsure: boolean;
  /** At most `MAX_REASONS`, and empty when this build knows none of the codes. */
  readonly reasons: readonly string[];
}
