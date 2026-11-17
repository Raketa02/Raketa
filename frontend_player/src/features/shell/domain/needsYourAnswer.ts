/**
 * **Needs your answer — where the sheet stands** ([#816](https://github.com/Raketa02/Raketa/issues/816),
 * [ADR-0205](../../../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
 * §1, §2).
 *
 * Pure. The shell draws the envelope and the sheet from these, and nothing here knows what waits,
 * only how many items each section holds.
 *
 * - **The envelope** shows while anything waits. A section whose read has not answered holds
 *   nothing, so a refused or slow read never opens a sheet that turns out empty.
 * - **The sheet** is `closed`, `open`, or `aside`: stepped aside under a record a face opened. Open,
 *   it is up only while something waits, so it is never drawn empty.
 * - **The last answer closes it for good** (`emptied`). A request arriving after that shows the
 *   envelope, never the sheet again by itself.
 * - **A record hands back** (Q24): closing the record a face opened brings the sheet back if anything
 *   waits **when the record closes** — whatever arrived while it was up, since the sheet never went.
 *   With nothing left, answered from the record, it closes with it.
 * - **Aside is under, not gone.** iOS drops a second native window opened while the first is still
 *   closing (#800, `discovery`'s vibe sheet), so the record is drawn over the sheet, inside it, and
 *   the sheet stays up beneath it — the record's own scrim covers it — until the record closes. That
 *   holds while the last item is answered from the record: the sheet must not close under it.
 * - **A screen closes it for good** (`handedToScreen`): the questionnaire cannot stand behind a
 *   sheet, and nothing navigates from inside one.
 */

export type NeedsYourAnswerSheet =
  | { readonly kind: 'closed' }
  | { readonly kind: 'open' }
  /** Stepped aside for the record of `reading`, a face's player id. */
  | { readonly kind: 'aside'; readonly reading: string };

export type NeedsYourAnswerEvent =
  | { readonly kind: 'envelopePressed' }
  /** ✕, a swipe down or the backdrop. */
  | { readonly kind: 'dismissed' }
  | { readonly kind: 'faceTapped'; readonly playerId: string }
  | { readonly kind: 'recordClosed'; readonly stillWaits: boolean }
  /** Nothing waits any more: the last item was answered, here or elsewhere. */
  | { readonly kind: 'emptied' }
  | { readonly kind: 'handedToScreen' };

export const CLOSED: NeedsYourAnswerSheet = { kind: 'closed' };
const OPEN: NeedsYourAnswerSheet = { kind: 'open' };

/** Whether the envelope shows — `waiting` is each section's count, `undefined` for a read not in. */
export function envelopeShows(waiting: readonly (number | undefined)[]): boolean {
  return waiting.some((count) => (count ?? 0) > 0);
}

export function needsYourAnswer(
  sheet: NeedsYourAnswerSheet,
  event: NeedsYourAnswerEvent,
): NeedsYourAnswerSheet {
  switch (event.kind) {
    case 'envelopePressed':
      return sheet.kind === 'closed' ? OPEN : sheet;
    // Three ways an open sheet goes for good, and one rule: a record over it keeps it up.
    case 'dismissed':
    case 'handedToScreen':
    case 'emptied':
      return sheet.kind === 'open' ? CLOSED : sheet;
    case 'faceTapped':
      return sheet.kind === 'open' ? { kind: 'aside', reading: event.playerId } : sheet;
    case 'recordClosed':
      if (sheet.kind !== 'aside') return sheet;
      return event.stillWaits ? OPEN : CLOSED;
  }
}

/** Whether the sheet is drawn up — open with something in it, or beneath a record it opened. */
export function sheetIsUp(sheet: NeedsYourAnswerSheet, anythingWaits: boolean): boolean {
  return sheet.kind === 'aside' || (sheet.kind === 'open' && anythingWaits);
}

/** The player whose record is up in the sheet's place, if a face opened one. */
export function readingRecordOf(sheet: NeedsYourAnswerSheet): string | undefined {
  return sheet.kind === 'aside' ? sheet.reading : undefined;
}
