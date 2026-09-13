/**
 * Backend `code` → the sentence a refused plan write draws, over `recoveryMessage`'s fallback —
 * the three slots' and the lock's, in one table, because a code means one thing whichever act met
 * it.
 *
 * `conversationErrorMessage`'s shape one feature over, and the reason is the same: localization
 * goes **code → message, never message → message**, and the fallback under the table is by
 * *recovery category*, so a code this build has never seen still says something true about what to
 * do next.
 *
 * ## The one this card exists to draw
 *
 * **A combination already in the past is refused in written copy rather than by a disabled
 * control**, because the day and the hour are filled in either order and either one can be the
 * second. §22.2 writes it, and it **names both remedies** — the platform has no opinion about
 * which of the two is wrong — and **names no value**, because the sentence is true whichever pair
 * produced it. It is drawn under the chip row, where both remedies are one tap away.
 *
 * ## The lock's own refusals are unreachable through the UI, and handled anyway
 *
 * `the_plan_is_not_complete` is the server's guard on the lock, and the button is greyed below
 * three slots — but **the button is UX and the server is the correctness mechanism**, and a slot
 * this build cannot read draws as unfilled while the server counts it, so the two sides can
 * disagree about *complete* exactly as they can about a horizon. The sentence names the remedy in
 * the counter's own terms and no slot, because the platform has not said which one.
 *
 * `the_court_is_not_whole` is the guard asked before it (ADR-0164 §5) — **the lock waits for the
 * court** — and the button is absent while the room has no game, with the count line in its place.
 * It is reachable all the same on a game a seat has since been left open on, where the button is
 * drawn and the server still refuses; the sentence says what will change, in the count line's own
 * words, rather than naming a control.
 *
 * `plan_not_found` is one code for three cases — no such challenge, never your court, or asked and
 * not yet answered — and it is here for the lock rather than for the slots, which write a plan
 * into being: a lock on a court nobody has arranged anything on is refused by the count first, so
 * what is left is a court you have left while this card was open.
 *
 * ## Two codes are here because a mirrored number can drift, and two are not here at all
 *
 * `the_day_is_past_the_horizon` and `the_place_is_too_long` are both refusals this client already
 * makes — the day row is clamped and the box is capped — so neither is reachable while the two
 * sides agree about `PLAN_HORIZON` and the cap. **They are mirrors of numbers the wire deliberately
 * does not declare**, which is exactly the case where the two sides can stop agreeing, and a
 * sentence is what a player gets on the day they do.
 *
 * `the_place_is_empty` gets no row, because `mayRecordPlace` closes the control on a box holding
 * nothing but whitespace — the server's own trim, read one step early. And `the_hour_is_not_offered`
 * gets none for the same reason one step further: every hour on the row **is** the offered grid.
 *
 * **`account_held` never reaches this table**, and that is a decision rather than a gap. A hold is
 * a fact about the **account** rather than about the write that met it, so the room folds it into
 * `liveState` — off this feature's mutation cache, through `usePlanWriteRefusals` — and draws
 * §22.5's one amber note, above the composer and on the same screen as the greyed chips and
 * button — *you are never told off for having tapped*. A coral sentence beside the chip as well
 * would say one fact twice, in the register the hold is deliberately not in.
 */

import { codeMessage, type AppError } from '@/shared/errors';

const BY_CODE: Readonly<Record<string, string>> = {
  /** §22.2, verbatim. Both remedies, and no value — see the module note. */
  that_moment_has_already_passed: 'That moment has already passed — change the day or the hour.',

  /**
   * The game left its entry window while this card was open. **The only thing that freezes the
   * slots**, and it is not a lock: once *we played* can no longer be said, the plan is a note
   * about an evening that is over.
   */
  plan_is_history: 'This game is over, so its plan cannot change now.',

  /** The horizon moved under a row this client had already drawn. */
  the_day_is_past_the_horizon: 'That day is past what this game can be moved to.',

  /** Refused whole, never truncated — so the remedy is the sender's and it is a short one. */
  the_place_is_too_long: 'That is longer than a place can be. Shorten it and set it again.',

  /**
   * **The lock waits for the court** (ADR-0164 §5), in the count line's own words. Unreachable
   * from a room with no game, where the button is absent; a game with a seat later left open still
   * draws the button, and this is what the server says to it. The remedy is not the player's to
   * act on, so the sentence names what will change rather than what to press.
   */
  the_court_is_not_whole: "Not everyone's here yet — lock the plan once they are.",

  /** The lock's guard, in the counter's own terms. Names no slot: the platform has not said. */
  the_plan_is_not_complete: 'Set all three before locking the plan.',

  /** One code for three cases, and none is retried: the court has gone from under this card. */
  plan_not_found: 'This plan is not one you can change.',
};

export function planErrorMessage(error: AppError): string {
  return codeMessage(BY_CODE, error);
}
