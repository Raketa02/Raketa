/**
 * What a leaver's own card says about her money.
 *
 * `ADR-0072` fixes that an **audience** changes a card's words and which money it
 * names, and never the situation. So this is a line *beside* the situation rather
 * than a thirty-seventh row in the table next door: a leaver keeps the match's
 * own progress, because a refill is the only thing that decides her outcome and a
 * card that hid the match's progress would hide it.
 *
 * **Two payload forms, never one with an optional amount.** `CONTEXT.md`:
 * *"`recoverable` names what she paid and what became of it; `nothingTaken` has
 * no field that could hold an amount"* — because *nothing was taken* and *nothing
 * has come back yet* are opposite sentences and a blank cannot tell them apart.
 * The union is what makes that bite: reading `paid` without narrowing does not
 * typecheck, so this table cannot accidentally print an amount for a player who
 * never paid one.
 *
 * **The unsettled sentence is its own row and not a fifth outcome.** An absent
 * `outcome` is *nothing has decided this yet*, which is a different thing from
 * every one of the four — and it is the state most leavers are in for most of the
 * time they hold a card, because settlement waits on somebody else taking the
 * seat.
 *
 * This is the one copy table here that renders an amount, and it renders it
 * through the app's single `formatMoney`. The rule `situations.ts` states — *a
 * copy table that formatted its own amounts would be a second place `38,00 zł` is
 * decided* — is about a table doing its **own** formatting; the spine's price is
 * passed in pre-formatted there because it is the *spine's*, where this payload is
 * this resolver's own to read.
 */

import type { Currency } from '@/shared/lib/formatting';
import { formatMoney } from '@/shared/lib/formatting';

import type { AssertTrue, CardDeparture, IsClosedUnion, Outcome } from './codes';

/** What became of what she paid, once something has decided it. */
export type LeaverEntry = (paid: string) => string;

/**
 * Total over the four outcomes a departure can settle at.
 *
 * Deleting a row fails `pnpm typecheck`, and that only works while the key stays
 * a closed union — pinned below.
 *
 * **The amount is what she paid in, in every row**, including the two where none
 * of it came back. `CONTEXT.md`: *"`Recoverable` names what she paid in; whether
 * any of it comes back is the outcome's answer, so a forfeited departure still
 * carries the figure."* Printing the figure on a forfeit is the sentence that
 * says what it cost her, which is the one a blank would swallow.
 */
export const LEAVER_COPY: Readonly<Record<Outcome, LeaverEntry>> = {
  reversed: (paid) => `You left — ${paid} was reversed, as though it never left.`,
  refundedInFull: (paid) => `You left — ${paid} is coming back in full.`,
  // Never *half of X came back* with a second figure worked out here: halving an
  // amount is arithmetic, the phone does none (`ADR-0053`), and the server sends
  // what she paid rather than what she recovered.
  refundedHalf: (paid) => `You left — half of ${paid} is coming back.`,
  forfeited: (paid) => `You left — ${paid} stayed with the match.`,
};

/** Fails to compile if `Outcome` ever arrives as a bare string. */
export type OutcomeIsClosed = AssertTrue<IsClosedUnion<Outcome>>;

/**
 * A leaver whose seat has not yet found anybody.
 *
 * It names the condition rather than a moment, because there is no moment to
 * name: what stands between her and her money is somebody taking the seat, and
 * nothing can say when that will be.
 */
export const LEAVER_UNSETTLED: LeaverEntry = (paid) =>
  `You left — ${paid} comes back if somebody takes your seat.`;

/**
 * A leaver whose money never left, and so a sentence with no amount at all.
 *
 * `Raketa02/Raketa#91`: *"a leaver who paid nothing before commitment sees a card
 * naming no amount — she is not invited to interpret a blank."* This is that
 * sentence, and it is a constant rather than an entry because there is nothing
 * for it to read.
 */
export const LEAVER_NOTHING_TAKEN = 'You left — nothing had been taken.';

/**
 * The line for a viewer who has left, or `undefined` for every viewer who has
 * not.
 *
 * The fallback on an unrecognised outcome is not redundant with the typecheck.
 * The typecheck protects the repository; this protects an installed phone, which
 * cannot be forced to update and would otherwise meet a fifth outcome as a blank
 * line under the situation. Losing the sentence loses exactly the sentence — the
 * card still says what the match is doing, which is the fact her money turns on.
 */
export function leaverLine(departure: CardDeparture | null | undefined): string | undefined {
  if (departure === null || departure === undefined) return undefined;
  if (departure.form === 'nothingTaken') return LEAVER_NOTHING_TAKEN;

  const currency: Currency = departure.paid.currency;
  const paid = formatMoney({ amount: departure.paid.amount, currency });

  if (departure.outcome === null || departure.outcome === undefined) {
    return LEAVER_UNSETTLED(paid);
  }

  // `hasOwnProperty` rather than a bare index, because the outcome arrives as a
  // wire value and a `Record` indexed by an arbitrary string reaches
  // `Object.prototype` — a label spelled `toString` would resolve to a function
  // and print whatever it stringifies to, which is worse than the missing line.
  const outcome = departure.outcome;
  if (!Object.prototype.hasOwnProperty.call(LEAVER_COPY, outcome)) return undefined;

  const entry: LeaverEntry | undefined = (
    LEAVER_COPY as Readonly<Record<string, LeaverEntry | undefined>>
  )[outcome];
  return entry === undefined ? undefined : entry(paid);
}
