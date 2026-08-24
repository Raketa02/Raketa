/**
 * The one thing this client is allowed to work out for itself.
 *
 * `ADR-0053`: *"a client's only derivation is subtracting the current time from a
 * moment it was handed."* There is no kernel on the phone, nothing provisional,
 * nothing to mark and nothing to reconcile — so this module is the whole of the
 * feature's arithmetic over server data, and the walk in
 * `components/nowDiscipline.test.ts` is what keeps it the whole of it.
 *
 * **Reaching zero changes nothing on screen.** The countdown stops; the card does
 * not become another card, because becoming another card is a rule and the phone
 * holds none. Zero is instead the fourth of `ADR-0054`'s four asks: the client
 * says *the clock you gave me has run out, and you will know more than I do*, and
 * fetches.
 *
 * **`now` is a parameter, never read here.** That is what makes every rule below
 * testable without a fake clock, and it is why the two places that do read the
 * device's clock are countable.
 */

import type { Moment, ComposedScreen } from './ComposedScreen';

/**
 * How long is left, in milliseconds. Negative once the moment has passed.
 *
 * `undefined` for a moment that does not parse — which is a contract failure and
 * not a state, so it is answered by *there is no countdown here* rather than by a
 * number that would render as decades.
 */
export function remainingMs(moment: Moment, now: number): number | undefined {
  const at = Date.parse(moment);
  return Number.isNaN(at) ? undefined : at - now;
}

/**
 * Every moment the payload named, in no particular order.
 *
 * Both slots on a match card count: the card's own clock, and a live seat claim's
 * five minutes. Which of the two a card *shows* is the match card's rule
 * (`Raketa02/Raketa#87`); which of them can run out is not a choice at all, so the
 * ask watches both and needs no precedence to be correct.
 *
 * Selecting fields is not deriving from them — nothing below computes a value the
 * server did not send.
 */
export function momentsOnScreen(screen: ComposedScreen): readonly Moment[] {
  const cards = [
    ...screen.offers.cards,
    ...screen.yourMatches.cards,
    // A door holds no cards and no moment, so it contributes nothing to watch.
    ...screen.shelves.blocks.flatMap((block) => (block.kind === 'shelf' ? block.cards : [])),
  ];

  return cards.flatMap((card) => {
    if (card.kind !== 'match') return [];
    return [card.clock, card.claimExpiresAt].filter(
      (moment): moment is Moment => moment !== undefined,
    );
  });
}

/**
 * Milliseconds until the soonest of these moments that has not passed, or
 * `undefined` when there is none.
 *
 * A moment already behind us is skipped rather than answered as zero: it has
 * already had its ask, and answering zero would fetch — or repaint — on every
 * render for the rest of the screen's life.
 *
 * **Over a list rather than over the screen**, because the two callers hold two
 * different things: the composed screen's own next zero, and whatever moments a
 * screen off Now is counting to. Two copies of this loop is how one of them comes
 * to skip a passed moment and the other does not.
 */
export function soonestMs(moments: readonly Moment[], now: number): number | undefined {
  let soonest: number | undefined;

  for (const moment of moments) {
    const left = remainingMs(moment, now);
    if (left === undefined || left <= 0) continue;
    if (soonest === undefined || left < soonest) soonest = left;
  }

  return soonest;
}

/**
 * Milliseconds until the soonest moment **on the composed screen** that has not
 * passed, or `undefined` when there is none.
 */
export function msUntilNextZero(screen: ComposedScreen, now: number): number | undefined {
  return soonestMs(momentsOnScreen(screen), now);
}

/**
 * The band in which the countdown draws seconds, and in which it repaints every
 * second.
 *
 * `ADR-0088` fixes the cadence — *"one second while under ten minutes remain, one
 * minute above it"* — and ten rather than five so the boundary does not sit on top
 * of a seat claim's own five-minute lifetime.
 *
 * **It is one number because it decides two things that must agree.** Above it the
 * screen repaints once a minute, so a label showing seconds up there would be a
 * digit the cadence cannot keep true — the *"frozen number reads as broken rather
 * than static"* failure `ADR-0053` names, arrived at by drawing rather than by
 * polling. So the format never prints a unit the cadence cannot maintain, and both
 * halves read this constant.
 */
export const SECONDS_BAND_MS = 10 * 60 * 1000;

const SECOND_MS = 1000;
const MINUTE_MS = 60 * SECOND_MS;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

/**
 * How long until the screen should repaint, given the soonest moment on it.
 *
 * `undefined` when nothing is counting — a screen with no live moment arms nothing
 * at all, which is what keeps a phone in a pocket free.
 *
 * **Not aligned to anybody's second.** `UI` §G Open Decision 17 recommended a
 * minute-aligned tick; a screen holds several moments that do not share a
 * boundary, so aligning to one card's second leaves every other card's flip up to
 * a second late and costs a rule to buy it.
 */
export function repaintDelayMs(soonestMs: number | undefined): number | undefined {
  if (soonestMs === undefined) return undefined;
  return soonestMs <= SECONDS_BAND_MS ? SECOND_MS : MINUTE_MS;
}

/**
 * What the clock slot reads, given how long is left.
 *
 * Four bands, and the seam between the first two is `SECONDS_BAND_MS` — the same
 * number the repaint cadence turns on, so the label never prints a digit that is
 * about to sit still for a minute.
 *
 * | Left | Reads |
 * | --- | --- |
 * | under ten minutes | `4:37` — a clock face, `ADR-0088`'s own spelling |
 * | under an hour | `42 min` |
 * | under a day | `2 h 14 min` |
 * | a day or more | `3 d 4 h` |
 *
 * **The three lower bands are the repo's shared table verbatim** —
 * `docs/value-formatting.md` writes a duration as `60 min` / `1 h 30 min`, space
 * before the unit — so a length of time reads the same here as it does in the club
 * console. The day band extends it, because that table has no row for one and a
 * hold twenty days out is a real clock on this screen.
 *
 * **The clock face is deliberately not that table's duration.** `1 min 30 s`
 * ticking once a second is unreadable, and `ADR-0088` draws `1:30`.
 *
 * A moment already behind us reads `0:00` rather than a negative: reaching zero is
 * the fourth ask and the answer is already on its way, so the card holds still and
 * says so. It is never the empty string, which would collapse the slot under the
 * player's thumb.
 */
export function countdownLabel(leftMs: number): string {
  if (leftMs < SECONDS_BAND_MS) {
    const clamped = Math.max(leftMs, 0);
    const minutes = Math.floor(clamped / MINUTE_MS);
    const seconds = Math.floor((clamped % MINUTE_MS) / SECOND_MS);
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  }

  if (leftMs < HOUR_MS) {
    return `${Math.floor(leftMs / MINUTE_MS)} min`;
  }

  if (leftMs < DAY_MS) {
    return span(
      Math.floor(leftMs / HOUR_MS),
      'h',
      Math.floor((leftMs % HOUR_MS) / MINUTE_MS),
      'min',
    );
  }

  return span(Math.floor(leftMs / DAY_MS), 'd', Math.floor((leftMs % DAY_MS) / HOUR_MS), 'h');
}

/**
 * `2 h 14 min`, and `2 h` when the smaller part is zero.
 *
 * Dropping the zero rather than printing `2 h 0 min`: the shared table's own
 * examples never carry a zero component, and a slot reading `0 min` invites the
 * reading *no minutes left* on a card that has two hours.
 */
function span(large: number, largeUnit: string, small: number, smallUnit: string): string {
  return small === 0 ? `${large} ${largeUnit}` : `${large} ${largeUnit} ${small} ${smallUnit}`;
}
