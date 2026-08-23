/**
 * The four outcomes and the four standings, in the words a player reads.
 *
 * The wire carries labels — `refundedHalf`, `stillPossible` — and never a
 * sentence. That split is `ADR-0075`'s and the reason is the same one it gives
 * everywhere: retuning what an outcome *is* is a server change, and rewording it
 * is this app's, and a server that wrote the sentence would be the single
 * precedent for server-held copy anywhere in the contract.
 *
 * **Three renderings per outcome, in one entry.** The same label is a row in the
 * table of four, the label on the one button while it is the quote, and the
 * acknowledgement once it is what the departure was made at. Writing all three out
 * rather than deriving two of them from the first is deliberate: `Leave — nothing
 * comes back` and `Nothing comes back` differ by more than a prefix, and a
 * derivation would put a copy rule in code where a copy editor can only reach the
 * table.
 *
 * **Nothing here mentions transferring a seat**, and that is `ADR-0086`'s own
 * ruling rather than an omission: it is the leaver's *best* outcome and it belongs
 * to the invite flow, which this map rules out — *"advertising a door that is not
 * there is worse than the gap."* `departureDiscipline.test.ts` walks this feature
 * so it cannot arrive by accident.
 */

import type { QuoteCopy, StandingCopy } from '../domain/Departure';

import type { AssertTrue, IsClosedUnion, Outcome, OutcomeStanding } from './codes';

/**
 * Total over the four outcomes. Deleting a row fails `pnpm typecheck`.
 *
 * **No amount anywhere.** `ADR-0033` fixes the quote as *a label and never an
 * amount*, and the phone could not print one honestly in any case: it holds what
 * she paid, not half of it, and halving is arithmetic the phone does not do
 * (`ADR-0053`). The figure she is deciding against is her seat's amount, printed
 * once beside the quote as one of its three reasons.
 */
export const OUTCOME_COPY: Readonly<Record<Outcome, QuoteCopy>> = {
  reversed: {
    name: 'Payment reversed',
    leaving: 'Leave — your payment is reversed',
    left: 'You have left. Your payment is being reversed, as though it never left.',
  },
  refundedInFull: {
    name: 'Refunded in full',
    leaving: 'Leave — refunded in full',
    left: 'You have left. You are refunded in full.',
  },
  refundedHalf: {
    name: 'Half refunded',
    leaving: 'Leave — half refunded',
    left: 'You have left. Half of what you paid is coming back.',
  },
  forfeited: {
    name: 'Nothing comes back',
    leaving: 'Leave — nothing comes back',
    left: 'You have left. Nothing comes back.',
  },
};

/** Fails to compile if `Outcome` ever arrives as a bare string. */
export type OutcomeIsClosed = AssertTrue<IsClosedUnion<Outcome>>;

/**
 * Total over the four standings, each with the mark that sits beside it.
 *
 * The marks are **decoration and are hidden from assistive technology** — the note
 * is what carries the state, which is this app's rule wherever a mark stands
 * beside a sentence. Two of the four are open circles and differ only in their
 * words, and that is fine for the same reason: the words are the cue, and *In
 * 2 h 14 min* and *Once the match fills* are not close to each other.
 *
 * **`stillPossible` names a condition and never a moment**, because there is no
 * moment to name: what stands between her and it is an **event** rather than a
 * clock. A match that has not committed reaches none of the money outcomes until
 * it fills, and nothing can say when that will be — so naming a moment there would
 * be the screen promising a turn that may never come.
 */
export const STANDING_COPY: Readonly<Record<OutcomeStanding, StandingCopy>> = {
  searching: { mark: '●', note: () => 'What leaving is worth now' },
  opens: {
    mark: '○',
    // A moment that does not parse is a contract failure rather than a state, and
    // the answer is the vaguest true thing rather than a figure in decades — the
    // same answer the card's own countdown gives when it cannot read its moment.
    note: (countdown) => (countdown === undefined ? 'Later on' : `In ${countdown}`),
  },
  stillPossible: { mark: '○', note: () => 'Once the match fills' },
  spent: { mark: '×', note: () => 'Behind you' },
};

/** Fails to compile if `OutcomeStanding` ever arrives as a bare string. */
export type OutcomeStandingIsClosed = AssertTrue<IsClosedUnion<OutcomeStanding>>;

/**
 * What one outcome is called, or `undefined` for a label this build has never
 * heard of.
 *
 * **The argument is a `string` on purpose**, the same as the situation table's. A
 * fifth outcome must cost an installed phone one row's words and nothing else —
 * old app versions live on real phones for months — and typing the parameter as
 * `Outcome` would make that path unreachable in the one place it has to work.
 */
export function outcomeCopy(outcome: string): QuoteCopy | undefined {
  return own(OUTCOME_COPY, outcome);
}

/** Where a row stands, or `undefined` for a standing this build has never heard of. */
export function standingCopy(standing: string): StandingCopy | undefined {
  return own(STANDING_COPY, standing);
}

/**
 * A table's own entry for a key, and never one off `Object.prototype`.
 *
 * Indexing a `Record` with an arbitrary `string` reaches the prototype chain, and
 * these two are indexed with an arbitrary string **on purpose** — an outcome this
 * build has never heard of has to resolve to nothing, which is what lets an
 * installed phone meet a fifth one and lose only a row. Without this guard a wire
 * value spelled `toString` resolves to a function and the row draws whatever that
 * stringifies to, which is the one failure worse than the missing row.
 */
function own<T>(table: Readonly<Record<string, T>>, key: string): T | undefined {
  return Object.prototype.hasOwnProperty.call(table, key) ? table[key] : undefined;
}
