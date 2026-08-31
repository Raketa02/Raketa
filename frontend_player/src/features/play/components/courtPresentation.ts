/**
 * An empty seat, and why this four.
 *
 * Two vocabularies, both the **court's own statement about itself**
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §11).
 *
 * ## An unfilled seat says what the obstacle was, per seat
 *
 * [#223](https://github.com/Raketa02/Raketa/issues/223) made these the court's shortfall
 * rather than AC-69's *"Only found N"*, and each routes its remedy to the pool, where the
 * ladder is.
 *
 * **`NO_SHARED_SLOTS` must not read as a refusal.** It is *"a dock, never a refusal: the
 * availability term zeroes and the screen says you would all have to bend, and nobody is
 * removed from the court for it."* The sentence states the state and names nobody as the
 * cause.
 *
 * ## The group reasons quote no figure, ever
 *
 * `G` is recorded and never returned — *"one closed code, never a number"* — so these five
 * sentences are the whole of the group objective's explanation. `GROUP_RAPPORT` covers two
 * group terms and gets **one** sentence: the code is the vocabulary, and splitting it in copy
 * would publish a distinction the enum deliberately does not carry.
 *
 * **And none of these appears inside the why-fit sheet.** A court seat's sheet explains the
 * *pairing's* Fit, never the `G` that seated them (#233 §9).
 */

import type { GroupReason, UnfilledReason } from '../domain/vocabulary';

const UNFILLED: Readonly<Record<UnfilledReason, string>> = {
  NO_CANDIDATE_ABOVE_FLOOR: 'Nobody in range was a good enough fit for this seat',
  NO_ADMISSIBLE_COMBINATION: 'Plenty of people, but no four of you work together',
  POOL_EXHAUSTED: 'Nobody left in range — everybody who fits is already seated',
  NO_SHARED_SLOTS: "Seated, but the four of you share no slot — you'd all have to bend",
};

export function unfilledSeatLine(reason: UnfilledReason): string {
  return UNFILLED[reason];
}

/**
 * A seated player the live gates no longer admit — **the fact, and never the cause**.
 *
 * Not a code: nothing on the wire says this. It is a **set difference** the client derives,
 * because `WithheldRowSchema` has one field and carries no id — see
 * [`lineup.ts`](../domain/lineup.ts)'s `withheldSeats`.
 *
 * Four gates reach this one sentence: a block in either direction, a hold, an account that may
 * not be shown, and the mutual gender preference. Naming which fired would tell a searcher
 * that a particular person blocked them, was suspended, or changed a safety setting — which is
 * the ceiling
 * [ADR-0130](../../../../../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)
 * puts on the withheld row itself, and it does not weaken because the client did the
 * arithmetic instead of the server.
 *
 * It says **changed**, not *unavailable*, in the register the refused send is held to, and the
 * two sentences are written down together in
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §21 so that neither can
 * drift away from the other: the fact is that
 * the line-up went out of date, and a person's standing is not the organiser's to be told.
 * *Can't be invited now* is a statement about what this app will do, not a verdict on
 * somebody.
 *
 * **The seat keeps its player.** Emptying it is silent destruction arriving from a direction
 * no acceptance criterion covers; this sentence is what makes the change something the player
 * can see and act on, one tap from the pool.
 */
export const WITHHELD_SEAT_LINE = "Something's changed — they can't be invited now";

const GROUP: Readonly<Record<GroupReason, string>> = {
  EVENEST_ARRANGEMENT: 'The evenest way to split these four',
  STRONGEST_WEAKEST_SEAT: 'Nobody here is out of their depth',
  BEST_AVERAGE_FIT: 'The best all-round fit across the four seats',
  MOST_SHARED_SLOTS: 'The four of you share the most slots',
  GROUP_RAPPORT: 'These four read each other well',
};

export function groupReasonLine(reason: GroupReason): string {
  return GROUP[reason];
}
