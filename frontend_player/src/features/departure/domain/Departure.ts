/**
 * What leaving a match is worth right now, and what it could still become.
 *
 * `ADR-0086`'s screen in this app's vocabulary. Three things about it are
 * decisions rather than transcription:
 *
 * - **It is not a card**, and that is why it is not a `MatchCard`. The wire sends
 *   no fit badge, no emphasis flag and no card stamp, because all three are
 *   judgements the composition made about a card's *place on Now* and none of them
 *   means anything on a screen with one thing on it. What it shares with a card is
 *   the **spine** and the **situation half**, and those are Now's types, imported
 *   rather than restated — two definitions of *where and when* is how two answers
 *   come to disagree.
 * - **Nothing here is derived.** `ADR-0053` leaves the phone one derivation —
 *   subtracting a moment it was handed from the current time — and this feature
 *   reaches it through Now's `countdown`, so there is still exactly one. Every
 *   field below arrived on the wire, and the ones that read as words arrived as
 *   codes and were resolved in `mappers/`.
 * - **The four outcomes are all four, always.** Not the reachable ones: *"a table
 *   that quietly drops forfeited once it is unreachable is also a table that never
 *   showed it while it was"* (`ADR-0086`), and the whole reason this act got a
 *   route instead of a card was room. A private court sends two rows, which is the
 *   glossary being read rather than a rule this screen applies.
 *
 * **No phase.** The four standings already say which phase she is in, and a phase
 * name would be a second vocabulary answering a question already answered.
 *
 * **The spine's own clock slot is not mapped.** The wire carries it — a screen
 * about a deadline should not be the place a card's moment goes missing — but the
 * two clocks this screen draws are the commitment deadline and the moment a row
 * opens at, both named in their own right beside the thing they explain. Mapping
 * the slot as well would be a field kept warm for a countdown nothing renders,
 * and it would arm a repaint for a moment no reader watches.
 */

import type { Moment, NowUpdate, Place, SituationCopy } from '@/features/now/types';
import type { Money } from '@/shared/lib/formatting';

/**
 * Where one outcome stands, in words and one mark.
 *
 * The **mark is decoration** and is hidden from assistive technology; the note is
 * what carries the state, because a row whose standing is a shape is a row a
 * screen-reader user does not have. That is this app's rule everywhere a mark
 * appears beside a sentence.
 */
export interface StandingCopy {
  readonly mark: string;
  /**
   * What this standing says.
   *
   * A function of the countdown because one of the four names a moment and the
   * other three do not, and the moment ticks — so the sentence is composed at
   * paint time from a label the row already has, rather than frozen into the
   * object at map time and left to go stale under the player's thumb.
   */
  readonly note: (countdown: string | undefined) => string;
}

/** One of the outcomes, and where it stands for this viewer right now. */
export interface OutcomeRow {
  /**
   * The outcome's own label, exactly as it arrived.
   *
   * Kept as a string and **never branched on for words** — the same rule a card's
   * `situation` follows. It is here so an unrecognised label is reportable and so
   * `name` being absent has a cause a reader can see.
   */
  readonly outcome: string;
  /** What this outcome is, or absent for a label this build has never heard of. */
  readonly name: string | undefined;
  /** Where it stands, or absent for a standing this build has never heard of. */
  readonly standing: StandingCopy | undefined;
  /**
   * When it becomes the quote, present **exactly** on the standing that opens.
   *
   * The phone subtracts it and derives nothing else. A moment beside *spent*
   * would be a moment nothing counts to, and a row that is *still possible* has
   * none to give — which is precisely what distinguishes the two.
   */
  readonly opensAt: Moment | undefined;
}

/**
 * The one live outcome: what leaving right now is quoted at.
 *
 * Never the set. `CONTEXT.md` orders the four over single labels, so quoting the
 * table would make the refuse-if-worse rule compare sets — and the label is what
 * goes back on the write, because *what she was shown as the basis for deciding*
 * is the thing worth refusing on. An amount moves for reasons that have nothing to
 * do with leaving (`ADR-0033`).
 */
export interface Quote {
  /** The label the write carries back, unread and unmodified. */
  readonly outcome: string;
  /** What taking it means, or absent for a label this build has never heard of. */
  readonly copy: QuoteCopy | undefined;
}

/** The three renderings of one outcome: as a row, as a button, as an acknowledgement. */
export interface QuoteCopy {
  /** The row's own name in the table of four. */
  readonly name: string;
  /** What the one button says while this is the quote. It carries the quote. */
  readonly leaving: string;
  /** What the screen says once this is what the departure was made at. */
  readonly left: string;
}

/**
 * How full the match is, counted **by money**.
 *
 * `paid` and `held` are two numbers and never one: a held-and-unpaid seat is a
 * name with no money behind it and can lapse, so folding it in would tell her the
 * match is complete while a seat may still go — and how full the match is is one
 * of the three reasons printed beside her quote.
 */
export interface SeatCounts {
  readonly seats: number;
  readonly paid: number;
  readonly held: number;
}

/** The screen: the spine, the situation, the quote, and all four outcomes. */
export interface Departure {
  readonly matchId: string;
  readonly where: Place;
  /**
   * Her seat's amount: her own share inside this match, which is the figure the
   * outcomes are percentages of. One number and never a second copy of it under
   * another name.
   */
  readonly price: Money;
  /** The situation's name as it arrived. Kept as a string and never branched on. */
  readonly situation: string;
  /** What the match is doing, or absent for a name this build has never heard of. */
  readonly status: SituationCopy | undefined;
  /**
   * Whether she may leave, as the server's boolean.
   *
   * **The phone derives none of it** (`ADR-0086`). False after the match starts,
   * under `ADR-0046`'s private-court lock, for a leaver who has already left, for
   * a viewer holding a live seat claim, and for a match that has been cancelled.
   * Past the point of departure the control is **absent rather than refusing** —
   * no door is offered that will not open.
   */
  readonly mayDepart: boolean;
  readonly quote: Quote;
  readonly outcomes: readonly OutcomeRow[];
  readonly counts: SeatCounts;
  /**
   * When this match's seats stop being freely refundable.
   *
   * Absent on a private court, and that is the fact rather than a gap: the court
   * was bought at booking, so there is no commitment for a deadline to be about.
   */
  readonly commitmentDeadline: Moment | undefined;
}

/**
 * What a tap on the one button did.
 *
 * `applied` is the outcome the departure was **made at**, and absent exactly when
 * nothing was applied. It is the only thing in the answer that is a fact about the
 * *command* rather than about the match, and it is why *was I refused* is not a
 * rule on the phone: deriving it from `mayDepart` still being true would be one,
 * and `ADR-0053` leaves the phone none.
 *
 * **A refusal is not a second shape** (`ADR-0070`). A quote that has fallen, a
 * match that has started, a second tap by somebody who has already left — every
 * one of them comes back as what a success returns, so there is one code path and
 * the player *sees* the correction rather than being told it.
 */
export interface DepartureAnswer {
  readonly screen: Departure;
  readonly applied: Quote | undefined;
  /**
   * The one card on Now that changed, so the screen behind this one corrects
   * itself off the player's own tap rather than off a second request.
   *
   * It rides in the write's answer (`ADR-0074`) and is handed to Now unread:
   * where a card sits is Now's knowledge, and a departure that decided it would
   * be a second opinion about the composition.
   */
  readonly update: NowUpdate;
}
