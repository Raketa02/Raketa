/**
 * The seven acts a card may name, and where each one goes.
 *
 * `ADR-0083` closed the set at six on one rule — *a card names an act when the
 * viewer can take it now and a v1 surface can receive it* — and `ADR-0087`
 * exercised that rule once, adding `leaveStandby` **with** the write that
 * receives it. That is the only way an eighth arrives.
 *
 * **There is no fallback.** `Open match` died with its destination when the
 * match-detail screen went out of scope. Twenty-six of the thirty-six situations
 * name no act, and a card with none has no primary button and no tappable body —
 * that is not a hole to be patched with a button that opens something
 * irrelevant.
 *
 * **A code, and no target beside it.** Each code determines its own destination
 * and the card already identifies the thing it is about, so a target on the wire
 * would be a second answer to one question. This table is that determination.
 */

import type { ActCopy } from '../domain/presentation';

import type { ActCode, AssertTrue, IsClosedUnion } from './codes';

/**
 * What a label may read.
 *
 * `price` arrives already formatted, for the same reason the situation table's
 * does: money formatting is the card's and the repo's shared value-formatting
 * table's, and a copy table that formatted its own amounts would be a second
 * place `38,00 zł` is decided.
 */
export interface ActContext {
  readonly price: string;
}

export type ActEntry = (context: ActContext) => ActCopy;

/** Total over the seven. Deleting a row fails `pnpm typecheck`. */
export const ACT_COPY: Readonly<Record<ActCode, ActEntry>> = {
  // The prototype's own label, kept verbatim: the amount is the decision, and a
  // button that hides it asks her to tap to find out what it costs.
  takeSeat: (c) => ({ label: `Take the seat · ${c.price}`, surface: 'seatClaim' }),
  // A live claim wins — this overrides whatever the situation named, the same
  // override the card's one clock slot already makes for the claim's five
  // minutes. A card counting *1:30 to pay* under a button offering anything else
  // is two instructions.
  finishPaying: (c) => ({ label: `Finish paying · ${c.price}`, surface: 'claimPayment' }),
  enterResult: () => ({ label: 'Enter the score', surface: 'result' }),
  // Answering is accepting *or* countering, and a counter carries a score rather
  // than a bare rejection — so the label does not promise agreement.
  answerResult: () => ({ label: 'Answer the score', surface: 'result' }),
  seeAlternatives: () => ({ label: 'See alternatives', surface: 'find' }),
  gettingIn: () => ({ label: 'Getting in', surface: 'gettingIn' }),
  leaveStandby: () => ({ label: 'Leave standby', surface: 'standbyWrite' }),
};

/** Fails to compile if `ActCode` ever arrives as a bare string. */
export type ActCodeIsClosed = AssertTrue<IsClosedUnion<ActCode>>;

/**
 * The act, or `undefined` for a code this build has never heard of.
 *
 * An unknown act draws **no button**, which is the same answer a card naming no
 * act gets. The alternative — a button whose destination this build cannot
 * resolve — is the one outcome worse than silence.
 */
export function actCopy(act: string, context: ActContext): ActCopy | undefined {
  const entry: ActEntry | undefined = (ACT_COPY as Readonly<Record<string, ActEntry | undefined>>)[
    act
  ];
  return entry === undefined ? undefined : entry(context);
}
