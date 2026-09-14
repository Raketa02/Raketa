/**
 * An empty seat, and who the answer was for.
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
 * ## `GroupReason` has no sentence here any more
 *
 * Five codes had five lines, drawn in a row of their own under the forecast card's names —
 * *the evenest way to split these four*, *the four of you share the most slots*, *these four
 * read each other well*, and two deliberate silences. **The row is gone**, and the copy went
 * with it rather than staying behind as a table nothing renders.
 *
 * What it was competing with is what decided it. The card already prints two side strengths,
 * a signed gap, an evenness percentage and its word, and — since the seats became faces — the
 * four people themselves, each a control into their own record. A sentence naming what the
 * engine went looking for reads, underneath all of that, as a caption on an answer the reader
 * has already been given four views of. The code is still on the wire and still in
 * `domain/vocabulary`; nothing about the response changed, only what the client says about it.
 *
 * ## `OptimisedFor` is the other vocabulary, and it stays
 *
 * It is the court's statement about **the answer** rather than about a seat, and it survives
 * the row above for the reason that row did not: it says something no figure on the card
 * carries — that the engine stopped optimising for *you* — and it is a consequence of an act
 * the player took, said before they discover it.
 */

import type { OptimisedFor, UnfilledReason } from '../domain/vocabulary';

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

/**
 * Whom the answer was optimised for — **and the one value that says nothing.**
 *
 * `GROUP` is what a hand-seated court gets: *"send `locked_seats` to hand-seat people. From
 * that moment the engine optimises for the group and says so in `search.optimised_for`,
 * because you may end up with a worse individual match than an empty court would have given
 * you."* That is a consequence of an act the player took, said before they discover it — which
 * is the same job a provisional figure's caveat does, and
 * [`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §11.2 asks
 * for it in the same voice.
 *
 * **`SEARCHER` has no sentence, and `null` is not an empty one.** A `Record` keyed by the
 * union with `null` for *say nothing* is `availabilityDiffCellLabel`'s shape, and it draws the
 * same line here: an answer optimised for you is the ordinary case and announcing it would
 * make the exception unreadable by putting a sentence under every court.
 */
const OPTIMISED: Readonly<Record<OptimisedFor, string | null>> = {
  SEARCHER: null,
  GROUP:
    'Seated around the people you picked, so this is the best game for the four of you rather than your own best match.',
};

/**
 * What the court says about who the answer was for. `undefined` where there is nothing to say
 * — which is `SEARCHER`, and a code this build has never seen (`SearchEnvelope.optimisedFor`).
 *
 * **And nothing on a fill that is completing a challenge**, whatever the envelope says. The
 * engine answers `GROUP` for any locked seat, and on that journey the locked seats are the
 * people who *said yes*, never people the organiser picked — so the sentence would be false
 * in its first clause, and its second is a caveat about a court that already exists: the four
 * are not a choice the engine made around somebody, they are the line-up being finished.
 * The ordinary builder keeps the line, because there the locked seat is an act the player
 * took (`the-play-screens.md` §11.2's standing obligation).
 *
 * @param completing whether the builder is filling a challenge's open seats rather than
 *   building a court of its own — `BuilderScreen` reads it off the record's origin.
 */
export function optimisedForLine(
  optimised: OptimisedFor | null,
  completing = false,
): string | undefined {
  if (completing) return undefined;
  return optimised === null ? undefined : (OPTIMISED[optimised] ?? undefined);
}
