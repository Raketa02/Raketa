/**
 * Whether the card draws **what's at stake** — a rule about the sport, not about the pair
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * The two figures are the rating engine's own update rule read forward, and they are honest
 * about a **singles** game and only that:
 *
 * > A win against one named person isn't a thing that exists until the other three seats are
 * > known.
 *
 * On a doubles seat the game will be a four, and the searcher is looking at one of them. The
 * server prices the pairing anyway — *"the magnitude carries that sport's weighting while the
 * pairing is the one you are looking at"* — because a matcher may compare candidates by it. A
 * **card** may not print it: `+0,08 if you win` beside one handle, on a court that needs three
 * more, is a promise the platform cannot keep and would not be able to explain afterwards.
 *
 * ## It is keyed off the seat count and never off a flag
 *
 * `courtSeatCount` is `Court`'s own coordinates counted, and `isDoubles` is the one boundary
 * over it — already what every other singles-or-doubles decision in this feature reads: the
 * court entry card's wording, the builder's title, the pool's *add* sentence. A
 * `singles: boolean` beside them would be a second answer to a question that already has one,
 * and this file writing its own `seats === 2` would be a third
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7:
 * what somebody could be **wrong** about lives in `domain/`, which is why the predicate moved
 * here from the copy deck rather than being read backwards out of it).
 *
 * **The absence is the sport's, and the other absence is the contract's.** `at_stake` is
 * omitted in for fun — where a counted result is *meaningless* rather than unavailable — and
 * omitted in competitive where either of the two holds no rating in this sport. Neither of
 * those reaches this rule at all: they arrive as no field, and no field is no boxes. What is
 * decided here is the third case, where the figures are real and the card still must not print
 * them.
 */

import type { AtStake } from './candidate';
import { isDoubles } from './lineup';

/**
 * The pair the card may draw, or nothing.
 *
 * `seats` is `courtSeatCount(origin.sport)`, held one component up because the Sport is a fact
 * about the **search** rather than about the person — the same placement `sportName` takes. It
 * is always a real court's count by the time it reaches here: the pool draws no candidate card
 * at all until it knows its Sport, so there is no *seat count unknown* third case to invent.
 */
export function stakeOnACard(facts: {
  readonly atStake?: AtStake;
  readonly seats: number;
}): AtStake | undefined {
  return isDoubles(facts.seats) ? undefined : facts.atStake;
}
