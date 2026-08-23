/**
 * Why a court is being kept aside, in five sentences.
 *
 * `ADR-0073` replaced `hold.note` — a sentence the server wrote, which would
 * have been the single precedent for server-held copy anywhere in the contract —
 * with a named reason plus the numbers it needs. **These are those five
 * sentences**, and they are written as clauses rather than as standalone lines
 * because the only thing that reads them is a situation's own sentence saying
 * what the court is doing.
 *
 * Five, not the kernel's thirteen. The other eight are diagnosis: a card that is
 * not describing a court does not name one, and shipping the diagnostic names
 * would oblige this client to hold seven rows it can never render.
 *
 * **An entry is a function of the whole note**, not of the reason alone. Today
 * the note carries the reason and nothing else; `Raketa02/Raketa#74` puts the
 * facts beside it — `stale` carries the hold's real age — and a function already
 * shaped to receive them widens without touching thirty-six call sites.
 */

import type { AssertTrue, CardHoldReason, HoldNote, IsClosedUnion } from './codes';

export type HoldReasonEntry = (note: HoldNote) => string;

/**
 * Total over the five reasons a card names.
 *
 * Deleting a row fails `pnpm typecheck`. That is the whole mechanism, and it
 * only works while the key stays a closed union — pinned below.
 */
export const HOLD_REASON_COPY: Readonly<Record<CardHoldReason, HoldReasonEntry>> = {
  committed: () => 'the match has committed',
  far: () => 'two seats are paid and it is more than twelve hours out',
  near: () => 'it is one seat short, and more than four hours out',
  stale: () => 'the club caps how long a court may sit held, and this one is past it',
  extended: () => 'the club has extended it beyond what the ladder guarantees',
};

/** Fails to compile if `CardHoldReason` ever arrives as a bare string. */
export type CardHoldReasonIsClosed = AssertTrue<IsClosedUnion<CardHoldReason>>;

/**
 * The clause for a note, or `undefined` for a reason this build has never heard
 * of.
 *
 * The fallback is not redundant with the typecheck. The typecheck protects the
 * repository; this protects an installed phone, which cannot be forced to update
 * and will meet a sixth reason one day. Losing the clause loses exactly the
 * clause — the situation still says the court is held.
 */
export function holdReasonClause(note: HoldNote | null | undefined): string | undefined {
  if (note === null || note === undefined) return undefined;
  const entry: HoldReasonEntry | undefined = HOLD_REASON_COPY[note.reason];
  return entry === undefined ? undefined : entry(note);
}
