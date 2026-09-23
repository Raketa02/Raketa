/**
 * `SH.whyfit`'s own words and figures — the five zones' headings, and the one sentence the
 * sheet owes about what a weight *is*.
 *
 * The term labels, the reason lines, the concerns, the stood-down sentences, the modifier
 * rows and the header are all written elsewhere and cited here: this file holds only what the
 * **sheet** says, which is a title, three headings, a basis line and four figures.
 *
 * ## The basis line replaces a sentence that was arithmetic in prose
 *
 * §B17 closed with *"in competitive mode the level terms carry 54 of 100; for fun, vibe and
 * availability carry 42"* — **43 and 38** against the shipped nominal vector, and neither is a
 * number this sheet may print anyway: the weights that cross are *renormalised per candidate*
 * and no route publishes the nominal table, because weights are configuration rather than
 * contract ([ADR-0106](../../../../../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).
 * A client table would go stale on the next ruleset release with nothing going red, since
 * `make gen-ruleset-diff` does not read TypeScript. So the sentence is **dropped** and the
 * basis takes its slot: it is true by construction, needs no ruleset knowledge, and is the one
 * thing a reader has to know to read the column at all
 * ([#233](https://github.com/Raketa02/Raketa/issues/233) §2, §5).
 *
 * ## The figures are signed where the sign is the fact
 *
 * A modifier may take points away and `applied` may be negative, so both carry their sign
 * explicitly — a bare `6` beside *from adjustments* is unreadable as a direction, and colour
 * is not allowed to be the one that says it (Part 13).
 */

/**
 * The sheet's visible title — `Why ✦ 78`.
 *
 * Its **accessible name is not this string**: `whyFitSheetLabel` writes `Why fit 78`, because
 * the ✦ must not be spoken and a glyph is doing work in the visible one. It is the one place
 * in the feature where the two differ, and §20.6 records it as such.
 *
 * **Rounded, like every other drawing of this number.** Fit arrives with its decimals on; the
 * pill makes it whole, the control beneath it always has, and a title carrying `Why ✦ 78,42131`
 * would be the sheet disagreeing with the button that opened it.
 */
export function whyFitTitle(fit: number): string {
  return `Why ✦ ${Math.round(fit)}`;
}

/**
 * The **control** that opens it — `Why 78?`.
 *
 * It is the one thing on the competitive card that used to be invisible: *Why 78?* was the
 * card body's press and nothing said so, and the designs draw it as a secondary button beside
 * the primary action ([#309](https://github.com/Raketa02/Raketa/issues/309)).
 *
 * **It is not `whyFitTitle`, and the ✦ is why.** The sheet's title carries the glyph because
 * the sheet has no fit pill on it; the card has one two rows above this button, and a second
 * ✦ beside the same number is [6.8](../../../../docs/design-system.md#68-the-availability-grid)'s
 * double announcement drawn in ink. The question mark is the other half of the split: the sheet
 * **states** what the number is made of, and the button is the reader **asking**.
 *
 * **The figure is rounded, because this button names the sheet it opens** — `seatedNameLabel`'s
 * own rule, for its own reason: `whyFitColumn` writes the whole column against `Math.round(fit)`
 * and the sheet's title is that number, so a served `78,4` printed whole here would promise
 * *Why 78,4* and open *Why 78*.
 */
export function whyFitControlWord(fit: number): string {
  return `Why ${Math.round(fit)}?`;
}

/** What the sheet's own close control closes. Never *Close* — `CloseControl`'s rule. */
export function whyFitCloseLabel(name: string): string {
  return `Close why ${name} fits`;
}

/**
 * `×26 → 18` — the row's one mono figure, and the reason its meter is hidden.
 *
 * The weight is the **renormalised share of a hundred over the terms that fired**, as a whole
 * number; the second figure is this row's contribution **as apportioned**, so the column sums
 * to the sub-total printed under it (`domain/whyFitColumn`). The arrow is the arithmetic, not
 * a decoration: weight times value is contribution, and the row shows the two ends of it.
 */
export function termFigure(row: {
  readonly weight: number;
  readonly contribution: number;
}): string {
  return `×${row.weight} → ${row.contribution}`;
}

/**
 * A figure whose **direction is part of it** — `+6`, `-5`, `0`.
 *
 * Used for the adjustments total and for every modifier row. Nought keeps no sign, because a
 * `+0` reads as an adjustment that happened and did nothing.
 */
export function signedFigure(points: number): string {
  const rounded = Math.round(points);
  return rounded > 0 ? `+${rounded}` : String(rounded);
}

/** The heading over the terms that stood down. A list, and deliberately not term rows. */
export const NOT_COUNTED_HEADING = 'Not counted for the two of you';

/**
 * What a weight on this sheet is a share of — stated **once, beneath the rows**, because it is
 * a property of the sheet rather than of any row.
 */
export const WEIGHT_BASIS =
  'Each weight is that term’s share of a hundred, over the terms that counted.';

/** The two version stamps, in the footer, in mono. `ADR-0104`'s reason is in `SearchEnvelope`. */
export function versionStamp(versions: {
  readonly rulesetVersion: string;
  readonly engineVersion: string;
}): string {
  return `${versions.rulesetVersion} · ${versions.engineVersion}`;
}
