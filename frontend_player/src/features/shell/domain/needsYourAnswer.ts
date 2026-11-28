/**
 * **Needs your answer — where the sheet stands** ([#816](https://github.com/Rakieta02/Rakieta/issues/816),
 * [#817](https://github.com/Rakieta02/Rakieta/issues/817),
 * [ADR-0205](../../../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
 * §1, §2).
 *
 * Pure. The shell draws the envelope and the sheet from these, and nothing here knows what waits,
 * only how many items each section holds.
 *
 * - **The envelope** shows while anything waits. A section whose read has not answered holds
 *   nothing, so a refused or slow read never opens a sheet that turns out empty.
 * - **The sheet** is `closed`, `asked`, `open`, `aside` — stepped aside under a record a face opened —
 *   or `underTheFill`, stepped aside under a sheet the fill opened from it. Open, it is up only while
 *   something waits, so it is never drawn empty.
 * - **The last answer closes it for good** (`emptied`). A request arriving after that shows the
 *   envelope, never the sheet again by itself.
 * - **A record hands back** (Q24): closing the record a face opened brings the sheet back if anything
 *   waits **when the record closes** — whatever arrived while it was up, since the sheet never went.
 *   With nothing left, answered from the record, it closes with it.
 * - **Aside is under, not gone.** iOS drops a second native window opened while the first is still
 *   closing (#800, `discovery`'s vibe sheet), so the record is drawn over the sheet, inside it, and
 *   the sheet stays up beneath it — the record's own scrim covers it — until the record closes. That
 *   holds while the last item is answered from the record: the sheet must not close under it.
 * - **The fill hands back too** (#817, Q24): **Confirm**, **Fix** and an invitation's *Accept* open
 *   the fill's sheets — the payment confirmation, the card setup — drawn over the sheet for the
 *   record's reason, and the sheet is back when the last of them closes if anything still waits.
 *   ***It's a game!* closes it for good** (`itsAGame`): once it was raised, the sheet goes with it,
 *   whatever still waits, as it goes for a screen.
 * - **A screen closes it for good** (`handedToScreen`): the questionnaire cannot stand behind a
 *   sheet, and nothing navigates from inside one.
 * - **A link or a notice asks for it** (#817, Q25): the friend link and a friends game invitation's
 *   notice open Home with the sheet up. Asked, it waits for the reads the link or the notice re-read
 *   (`settled`), and opens only if something waits by then: **Home opens as it is, with no sheet,
 *   when nothing does** — the sheet is never shown empty.
 */

export type NeedsYourAnswerSheet =
  | { readonly kind: 'closed' }
  /** Asked for by a link or a notice — up once the reads land, if anything waits by then. */
  | { readonly kind: 'asked' }
  | { readonly kind: 'open' }
  /** Stepped aside for the record of `reading`, a face's player id. */
  | { readonly kind: 'aside'; readonly reading: string }
  /**
   * Stepped aside for a sheet the fill opened from it — and, once `itsAGame`, under *It's a game!*,
   * which closes it for good.
   */
  | { readonly kind: 'underTheFill'; readonly itsAGame: boolean };

export type NeedsYourAnswerEvent =
  | { readonly kind: 'envelopePressed' }
  /** ✕, a swipe down or the backdrop. */
  | { readonly kind: 'dismissed' }
  | { readonly kind: 'faceTapped'; readonly playerId: string }
  | { readonly kind: 'recordClosed'; readonly stillWaits: boolean }
  /** The fill put a sheet up — or *It's a game!*. */
  | { readonly kind: 'fillRaised'; readonly itsAGame: boolean }
  /** The fill has nothing up any more. */
  | { readonly kind: 'fillGone'; readonly stillWaits: boolean }
  /** Nothing waits any more: the last item was answered, here or elsewhere. */
  | { readonly kind: 'emptied' }
  | { readonly kind: 'handedToScreen' }
  /** A link or a notice asked for the sheet. */
  | { readonly kind: 'asked' }
  /** The reads behind the sheet have landed — with something waiting in them, or nothing. */
  | { readonly kind: 'settled'; readonly stillWaits: boolean };

export const CLOSED: NeedsYourAnswerSheet = { kind: 'closed' };
const OPEN: NeedsYourAnswerSheet = { kind: 'open' };
const ASKED: NeedsYourAnswerSheet = { kind: 'asked' };

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
      return sheet.kind === 'closed' || sheet.kind === 'asked' ? OPEN : sheet;
    // Three ways an open sheet goes for good, and one rule: a sheet over it keeps it up. Asked, it is
    // waiting for the reads, and a read not in yet is not nothing waiting.
    case 'dismissed':
    case 'handedToScreen':
    case 'emptied':
      return sheet.kind === 'open' ? CLOSED : sheet;
    case 'faceTapped':
      return sheet.kind === 'open' ? { kind: 'aside', reading: event.playerId } : sheet;
    case 'recordClosed':
      if (sheet.kind !== 'aside') return sheet;
      return event.stillWaits ? OPEN : CLOSED;
    case 'fillRaised':
      if (sheet.kind === 'open') return { kind: 'underTheFill', itsAGame: event.itsAGame };
      if (sheet.kind !== 'underTheFill' || sheet.itsAGame || !event.itsAGame) return sheet;
      return { kind: 'underTheFill', itsAGame: true };
    case 'fillGone':
      if (sheet.kind !== 'underTheFill') return sheet;
      return !sheet.itsAGame && event.stillWaits ? OPEN : CLOSED;
    case 'asked':
      return sheet.kind === 'closed' ? ASKED : sheet;
    case 'settled':
      if (sheet.kind !== 'asked') return sheet;
      return event.stillWaits ? OPEN : CLOSED;
  }
}

/**
 * Whether the sheet is drawn up — open with something in it, or beneath a record or a fill's sheet
 * it opened.
 */
export function sheetIsUp(sheet: NeedsYourAnswerSheet, anythingWaits: boolean): boolean {
  return (
    sheet.kind === 'aside' ||
    sheet.kind === 'underTheFill' ||
    (sheet.kind === 'open' && anythingWaits)
  );
}

/**
 * **Whether the sheet just went for good** (#819, ADR-0205 §3), from `before` to `after`: what
 * records the visit. **Every way it goes away from standing up counts**: ✕, a swipe, the backdrop,
 * the last answer, a screen it handed over to, a record or a fill's sheet closing over nothing left,
 * and *It's a game!*. Stepping aside for one of those does not, since the sheet comes back, and
 * neither does a sheet a link or a notice asked for that never opened: nothing was shown.
 */
export function wentForGood(before: NeedsYourAnswerSheet, after: NeedsYourAnswerSheet): boolean {
  const wasUp = before.kind !== 'closed' && before.kind !== 'asked';
  // Asked again in the render that closed it — a link or a notice in the same breath — is still a
  // close: nothing steps from standing up to asked without closing first.
  return wasUp && (after.kind === 'closed' || after.kind === 'asked');
}

/**
 * **Whether the sheet is shown** (#819) — open with something in it. Up beneath a record or a fill's
 * sheet is not shown: their scrim covers it, so a read that lands then is read in but not seen, and
 * only counts once the sheet is back on top.
 */
export function sheetIsShown(sheet: NeedsYourAnswerSheet, anythingWaits: boolean): boolean {
  return sheet.kind === 'open' && anythingWaits;
}

/** Whether the sheet is waiting for its reads, asked for by a link or a notice. */
export function sheetIsAsked(sheet: NeedsYourAnswerSheet): boolean {
  return sheet.kind === 'asked';
}

/** The player whose record is up in the sheet's place, if a face opened one. */
export function readingRecordOf(sheet: NeedsYourAnswerSheet): string | undefined {
  return sheet.kind === 'aside' ? sheet.reading : undefined;
}
