/**
 * Thirty-six situations, and what each one says.
 *
 * The wire carries `{situation, facts}` and neither the tag nor the tone
 * (`ADR-0041`); `ADR-0072` added the alert strip as a fourth column of the same
 * table, on the grounds that it is a total function of the situation and a flag
 * would let the server and the phone disagree about whether a card is urgent.
 * `ADR-0075` fixes where the table lives, what one entry looks like, and that it
 * ships in **English** — with the honest cost recorded there: these thirty-six
 * sentences will be *rewritten* in Polish rather than translated.
 *
 * **An entry is a function, not a template string.** A template cannot be
 * type-checked against its payload, and the counting noun is the case that
 * breaks it — *3 of 4* stops meaning one thing across a screen where one card
 * counts seats paid, another counts shares, and a third counts who played.
 *
 * **The context is an object rather than a positional argument list.**
 * `ADR-0075` writes the entry as `(facts, audience) => …`; nothing on the wire
 * distinguishes an audience today, and the departure payload that will is
 * `Raketa02/Raketa#74`'s. A field added to `SituationContext` reaches the rows
 * that read it and leaves the other thirty-odd untouched, where a second
 * positional parameter would be a signature change at thirty-six sites for the
 * sake of a value none of them can read yet.
 *
 * The order below is the kernel's ladder order, so that reading the table is
 * reading the specification.
 */

import type { SituationCopy } from '../domain/presentation';

import type { AssertTrue, IsClosedUnion, Situation, SituationFacts } from './codes';
import { holdReasonClause } from './holdReasons';

/**
 * Everything a sentence may read.
 *
 * `clubName` and `price` are the **spine's**, not the situation half's — the
 * spine is drawn by every phone whether or not it can name the situation, so a
 * sentence built from it degrades to nothing worse than silence.
 *
 * `price` arrives already formatted. Money formatting belongs to the repo's
 * shared value-formatting table and to the card that draws it
 * (`Raketa02/Raketa#87`); a copy table that formatted its own amounts would be a
 * second place `38,00 zł` is decided.
 */
export interface SituationContext {
  readonly facts: SituationFacts;
  readonly clubName: string;
  readonly price: string;
}

export type SituationEntry = (context: SituationContext) => SituationCopy;

/**
 * The alert strip, verbatim from `UI` §B6.4 with the leaver's name removed —
 * the wire carries no name, and inventing one is worse than the gap.
 *
 * Three rows, not the prototype's two. `ADR-0072`: anything still short a player
 * inside the rescue window carries the alert, and it stops only when a seat is
 * actually being taken — so `rescueLate` alerts and `replacementTransfer` does
 * not, because a transfer in progress is good news.
 */
const PAYMENT_UNCHANGED = 'Your payment will not change.';

/** Held on a court that is being kept aside, whatever the situation calls it. */
function held(context: SituationContext, fallback: string): string {
  const clause = holdReasonClause(context.facts.hold);
  return clause === undefined ? fallback : `Held — ${clause}.`;
}

export const SITUATION_COPY: Readonly<Record<Situation, SituationEntry>> = {
  // 1-4 · cancelled.
  inventoryLost: () => ({
    // `UI` §G decides the retone: the prototype declared `bad`, its own tone map
    // had no such key, and the dot rendered colourless.
    line: 'Gone — the last court of this kind was sold.',
    tag: 'Cancelled',
    tone: 'ended',
    alert: null,
  }),
  cancelledClub: (c) => ({
    line: `Cancelled by ${c.clubName} — everybody refunded.`,
    tag: 'Cancelled',
    tone: 'ended',
    alert: null,
  }),
  cancelledIncomplete: () => ({
    line: 'Released back to the club — it never filled.',
    tag: 'Cancelled',
    tone: 'ended',
    alert: null,
  }),
  cancelledCheckpoint: () => ({
    line: 'Released back to the club — the seat was never refilled.',
    tag: 'Cancelled',
    tone: 'ended',
    alert: null,
  }),

  // 5 · played.
  playedNoShow: () => ({
    line: 'Settled — somebody did not turn up.',
    tag: 'Played',
    tone: 'idle',
    alert: null,
  }),
  playedShort: () => ({
    line: 'Settled — you played a player short.',
    tag: 'Played',
    tone: 'idle',
    alert: null,
  }),
  completed: () => ({
    line: 'Settled — the result is agreed.',
    tag: 'Completed',
    tone: 'good',
    alert: null,
  }),
  playedNoScore: () => ({
    // An evening, never evidence: never entering a score carries no penalty.
    line: 'Settled — nobody entered a score.',
    tag: 'Played',
    tone: 'idle',
    alert: null,
  }),
  confirmResult: () => ({
    line: 'A score is on the table — confirm it, or say what you had.',
    tag: 'Confirm the result',
    tone: 'watch',
    alert: null,
  }),
  needsResult: () => ({
    line: 'Settled — the score has not been entered yet.',
    tag: 'Needs result',
    tone: 'watch',
    alert: null,
  }),

  // 6 · a seat is on the table for this viewer. Two names because they are two
  // sentences: one is a reservation and the other is a race, and nothing may
  // claim a seat is held when it is not.
  seatOffered: () => ({
    line: 'A seat is being offered to you — nobody else can take it for the hour.',
    tag: 'Seat offered',
    tone: 'time',
    alert: null,
  }),
  seatOpened: () => ({
    line: 'A seat just opened — first to take it.',
    tag: 'Seat open',
    tone: 'time',
    alert: null,
  }),

  // 7 · queueing for a seat rather than holding one.
  waitlisted: () => ({
    line: 'Fully paid — you are on standby for the next seat that frees.',
    tag: 'On standby',
    tone: 'idle',
    alert: null,
  }),

  // 8 · somebody's own court.
  privateOpen: () => ({
    line: 'Yours — one seat is open to the marketplace.',
    tag: 'Reserved',
    tone: 'good',
    alert: null,
  }),
  privateFull: () => ({
    line: 'Yours — every share is paid.',
    tag: 'Reserved',
    tone: 'good',
    alert: null,
  }),
  privatePartial: () => ({
    line: 'Yours — you cover the court until every share is paid.',
    tag: 'Reserved',
    tone: 'good',
    alert: null,
  }),
  privateReserved: () => ({
    line: 'Yours — invite whoever you like.',
    tag: 'Reserved',
    tone: 'good',
    alert: null,
  }),

  // 9 · a committed match lost somebody, and the money is still moving. The
  // court's total is the same number for every audience, so this line does not
  // vary with who is looking.
  replacementTransfer: (c) => ({
    line: `${c.price} settled to the club — somebody is taking the free seat.`,
    tag: 'Replacement pending',
    tone: 'watch',
    alert: null,
  }),
  rescueLate: (c) => ({
    line: `${c.price} settled to the club — the seat stays funded.`,
    tag: 'Rescue active',
    tone: 'time',
    alert: `Still looking for a replacement, and the match starts soon. ${PAYMENT_UNCHANGED}`,
  }),
  rescue: (c) => ({
    line: `${c.price} settled to the club — the seat stays funded.`,
    tag: 'Rescue active',
    tone: 'time',
    alert: `Still looking for a replacement. ${PAYMENT_UNCHANGED}`,
  }),
  replacement: (c) => ({
    line: `${c.price} settled to the club — the seat stays funded.`,
    tag: 'Replacement pending',
    tone: 'watch',
    alert: `Somebody left after the commitment deadline. We are looking for a replacement. ${PAYMENT_UNCHANGED}`,
  }),

  // 10 · somebody left before commitment, recently.
  protectedBack: () => ({
    line: 'Somebody left, and the court is still held.',
    tag: 'Court protected',
    tone: 'good',
    alert: null,
  }),
  formingBack: () => ({
    line: 'Somebody left, and the court is no longer held.',
    tag: 'Forming',
    tone: 'watch',
    alert: null,
  }),

  // 11 · complete.
  ready: () => ({
    line: 'Everything is paid and the court is yours.',
    tag: 'Ready to play',
    tone: 'good',
    alert: null,
  }),
  confirmedOnFill: (c) => ({
    line: `${c.price} settled to the club — it committed the moment it filled.`,
    tag: 'Confirmed',
    tone: 'good',
    alert: null,
  }),
  confirmed: (c) => ({
    line: `${c.price} settled to the club.`,
    tag: 'Confirmed',
    tone: 'good',
    alert: null,
  }),
  full: () => ({
    line: 'Every seat is paid — it settles to the club at the commitment deadline.',
    tag: 'Full',
    tone: 'good',
    alert: null,
  }),

  // 12 · posted after its own commitment deadline, which is not the same
  // sentence as a deadline that has since passed.
  formingLateHeld: () => ({
    line: 'Posted after the commitment deadline, and a court is held.',
    tag: 'Forming',
    tone: 'idle',
    alert: null,
  }),

  // 13 · a court is being kept aside.
  clubHeld: (c) => ({
    line: `Committed by ${c.clubName}.`,
    tag: 'Court committed',
    tone: 'good',
    alert: null,
  }),
  heldSoft: (c) => ({
    line: held(c, 'Held for this match.'),
    tag: 'Court held',
    tone: 'watch',
    alert: null,
  }),

  // 14-17 · forming.
  heldReleased: (c) => ({
    line: `Released — back on sale at ${c.clubName}.`,
    tag: 'Court released',
    tone: 'watch',
    alert: null,
  }),
  formingHeld: () => ({
    line: 'No court is held yet — a seat is held but not paid.',
    tag: 'Forming',
    tone: 'idle',
    alert: null,
  }),
  formingLate: () => ({
    line: 'Past the commitment deadline, and no court is held yet.',
    tag: 'Forming',
    tone: 'idle',
    alert: null,
  }),
  forming: (c) => ({
    line: `Not held — ${c.clubName} is still selling this slot.`,
    tag: 'Forming',
    tone: 'idle',
    alert: null,
  }),

  // W1-W2 · the club's two amendments, applied after the ladder.
  heldStale: (c) => ({
    line: `Released — back on sale at ${c.clubName}.`,
    tag: 'Court released',
    tone: 'watch',
    alert: null,
  }),
  heldExtended: (c) => ({
    line: held(c, 'Held beyond what the ladder guarantees.'),
    tag: 'Court held',
    tone: 'good',
    alert: null,
  }),
};

/** Fails to compile if `Situation` ever arrives as a bare string. */
export type SituationIsClosed = AssertTrue<IsClosedUnion<Situation>>;

/**
 * What this situation says, or `undefined` for a name this build has never heard
 * of.
 *
 * **The argument is a `string` on purpose.** A phone that cannot name the
 * situation draws the spine and omits the status line — it never skips the card
 * and never asks the server for a compatibility map — and typing the parameter
 * as `Situation` would make that path unreachable in the one place it has to
 * work. Old app versions live on real phones for months; a thirty-seventh
 * situation must cost them one sentence and nothing else.
 */
export function situationCopy(
  situation: string,
  context: SituationContext,
): SituationCopy | undefined {
  const entry: SituationEntry | undefined = (
    SITUATION_COPY as Readonly<Record<string, SituationEntry | undefined>>
  )[situation];
  return entry === undefined ? undefined : entry(context);
}
