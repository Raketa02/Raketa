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
    ...screen.shelves.shelves.flatMap((shelf) => shelf.cards),
  ];

  return cards.flatMap((card) => {
    if (card.kind !== 'match') return [];
    return [card.clock, card.claimExpiresAt].filter(
      (moment): moment is Moment => moment !== undefined,
    );
  });
}

/**
 * Milliseconds until the soonest moment on screen that has not passed, or
 * `undefined` when there is none.
 *
 * A moment already behind us is skipped rather than answered as zero: it has
 * already had its ask, and answering zero would fetch on every render for the
 * rest of the screen's life.
 */
export function msUntilNextZero(screen: ComposedScreen, now: number): number | undefined {
  let soonest: number | undefined;

  for (const moment of momentsOnScreen(screen)) {
    const left = remainingMs(moment, now);
    if (left === undefined || left <= 0) continue;
    if (soonest === undefined || left < soonest) soonest = left;
  }

  return soonest;
}
