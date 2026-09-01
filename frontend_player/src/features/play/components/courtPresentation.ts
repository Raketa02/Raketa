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
 *
 * ## A third vocabulary joined them with the builder
 *
 * `OptimisedFor` is the court's statement about **the answer** rather than about a seat, and
 * it is here for the same reason the other two are: a code the engine names and the client
 * writes the sentence for.
 */

import type { SeatGuard } from '../domain/lineup';
import type { GroupReason, OptimisedFor, UnfilledReason } from '../domain/vocabulary';

import { SWAP_TOGGLE_LABEL } from './accessibilityPresentation';

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
 * The two seats a tap **refuses**, in the court's own words.
 *
 * A `Record` keyed by `SeatGuard` for §1's reason: a third guard added to the truth table
 * fails `pnpm typecheck` here rather than refusing a player in silence.
 *
 * **Both name the way out.** A refusal that only says no is a control a player presses twice.
 * Your own seat is refused *because swap mode is where sides change*, so the sentence names
 * the toggle — through `SWAP_TOGGLE_LABEL` rather than beside it, because the switch's own
 * label **is** that word and two spellings of one control is how a screen starts referring to
 * something that is not on it. An accepted seat is refused permanently, so its sentence says
 * what it costs instead: they keep their place, and you can still move them across the net.
 *
 * **Neither is drawn on the clear badge**, because the badge is not drawn where either would
 * fire (`domain/lineup.ts`'s `seatIsClearable`) — the prototype offered the ×, refused the
 * press, and then had to explain itself.
 */
const GUARD: Readonly<Record<SeatGuard, (name: string) => string>> = {
  SEAT_IS_YOURS: () => `That seat is yours — turn on ${SWAP_TOGGLE_LABEL} to change sides`,
  ALREADY_ACCEPTED: (name) => `${name} already accepted — they keep their place`,
};

/**
 * Why a seat would not take the tap.
 *
 * `name` is §15's `playerName()` — the whole handle, because a toast is a sentence and a
 * sentence never truncates. `SEAT_IS_YOURS` does not quote it: the seat is yours, and *You
 * already accepted* is not a thing to be told.
 */
export function seatGuardLine(guard: SeatGuard, name: string): string {
  return GUARD[guard](name);
}

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
 */
export function optimisedForLine(optimised: OptimisedFor | null): string | undefined {
  return optimised === null ? undefined : (OPTIMISED[optimised] ?? undefined);
}
