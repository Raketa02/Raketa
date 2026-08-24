/**
 * The screen's own sentences.
 *
 * The match's own sentence comes off **Now's** situation table, and the two endings
 * come off this feature's own; what is here is everything else a screen says — the
 * title, the two clocks' labels, the controls and the pad. Three of the four
 * sentences `deltas/result-confirmation.md` §10 calls weighty are here — the entry
 * nudge, *"is it right?"* and the counter — and that section also fixes one word:
 * **the product's word is *propose a modification*, never *dispute*.**
 *
 * **Nothing here names the player who entered the score**, although the delta's own
 * example does (*"Kuba entered this — is it right?"*). `proposed_by` crosses as a
 * **side** and never as a player, on the contract's own reasoning — *"naming the
 * teammate who typed it would put a person into an argument the model holds between
 * two halves of a net"* — so the sentence says *the other side*. That is a
 * deliberate softening of the delta's wording rather than a gap: the name is not on
 * the wire, and inventing one is worse than the loss.
 *
 * **There is no by-recovery table here.** This app already holds three and
 * `nowCopy.ts` records that *"a fourth is the signal to move it"* to `shared/`.
 * These are not a fourth: they are about *this* act, and the one code that gets its
 * own sentence gets it because the server rejected what she **typed** rather than
 * what the match is doing — which is the only failure on this screen that a
 * recomposed screen could not explain by itself.
 */

import type { AppError } from '@/shared/errors';

/** What the screen is. A noun, because five of its six renderings are not a question. */
export const RESULT_TITLE = 'The score';

/** What the close control does. Nothing is sent by closing, and nothing is lost. */
export const CLOSE_LABEL = 'Close';

/** The hero clock's own label — `ADR-0060` makes the figure beneath it the largest. */
export const SETTLEMENT_LABEL = 'Time left';

/** Who turned up, on a match that has been played. */
export const TURNED_UP_LABEL = 'Turned up';

/** `3 of 4` — the same shape the departure screen counts seats in. */
export function turnedUpOf(turnedUp: number, seats: number): string {
  return `${turnedUp} of ${seats}`;
}

/**
 * What happens if nobody does anything, keyed on how many sides have spoken.
 *
 * `ADR-0060`: *"the remaining time is the largest figure on the screen, next to the
 * sentence that says nobody has to do anything. Silence is what settles this
 * result, so the screen that asks for a tap has to say what happens without one —
 * loudly enough that a player who taps nothing has still been told."*
 *
 * **Keyed on `proposals`, which is a number the server sent**, and this is copy
 * selection rather than a rule the phone applies: nothing branches on it but the
 * words, the clock beside it is the server's, and what actually happens at that
 * moment happens on the server whether this sentence is right or not. The count is
 * capped at two by the contract, so two or more is one sentence — a third would be
 * a sentence for a state the model cannot reach.
 */
export function silenceLine(proposals: number): string {
  if (proposals <= 0) {
    return 'Nobody has entered a score. If nobody does, the evening still counts — the result does not.';
  }
  if (proposals === 1) {
    return 'Nobody has to do anything. If this is not answered, it stands.';
  }
  return 'Two scores are on the table. If neither side accepts the other’s, this match counts for nothing.';
}

/**
 * The quieter clock, drawn only while it runs.
 *
 * Inside it a counter beats a pending acceptance, so the screen must not say
 * *settled* half an hour early — which is the outcome `ADR-0048` built the grace to
 * prevent, inverted.
 */
export function graceLine(countdown: string): string {
  return `Nothing settles for another ${countdown} — until then a different score still beats an acceptance.`;
}

/** The question the opposing side is asked. `ADR-0060`'s second weighty sentence. */
export const ASKED_LINE = 'The other side entered this. Is it right?';

/** What the proposing side sees while it waits. Nothing is asked of her. */
export const WAITING_LINE = 'This is your side’s score. The other side has not answered yet.';

/** The controls. Three acts, and none of them is a bare rejection. */
export const ACCEPT_LABEL = 'That is right';
export const COUNTER_LABEL = 'Propose a modification';
export const CORRECT_LABEL = 'Change your score';
export const SEND_LABEL = 'Send this score';
export const CANCEL_ENTRY_LABEL = 'Leave the score as it is';

/** The pad's own heading, and the one line that says why a send is not offered. */
export const PAD_HEADING = 'What was the score?';
export const PAD_HINT = 'Your side first. Tap a number, then the other side’s.';
export const PAD_CLEAR_LABEL = 'Clear this set';
export const PAD_UNFINISHED = 'One set has only one number in it. Finish it, or clear it.';

/** How a set reads aloud, since a grid of digits has no reading order out loud. */
export function padCellLabel(set: number, side: string, value: number | undefined): string {
  return `Set ${set}, ${side}, ${value === undefined ? 'empty' : value}`;
}

/** A key on the pad. The bare digit is a number with no verb. */
export function padKeyLabel(value: number): string {
  return `Type ${value}`;
}

/**
 * The two **endings** are deliberately not here: a settled result and an unscored
 * evening are resolved *from the situation*, so they live in `mappers/endings.ts`
 * with the table that resolves them — exactly as the thirty-six situation sentences
 * live with theirs.
 */

/** A cold open that did not land. The player can ask again from here. */
export const LOAD_FAILED = 'We could not open this match’s result.';
export const RETRY_LABEL = 'Try again';

/** A write that never reached the server, or one the server could not accept. */
export const WRITE_FAILED = 'That did not go through, and nothing has changed. Try again.';

/**
 * The one refusal that is not a recomposed screen.
 *
 * A score no format of this sport could produce is about what she **typed**, not
 * about what the match is doing — so re-presenting the same table would show her no
 * reason at all. Every other way a write can stop applying comes back as a 200 and
 * redraws.
 */
const IMPOSSIBLE_SCORE = 'match_impossible_score';

const BY_CODE: Readonly<Record<string, string>> = {
  [IMPOSSIBLE_SCORE]: 'That score could not have been played. Check it and send it again.',
};

/**
 * What a failed write says.
 *
 * Keyed on the backend's stable `code` and never on its `message`, which is a
 * diagnostic written for a log. **Own properties only**: indexing a `Record` with an
 * arbitrary string reaches `Object.prototype`, and a code spelled `toString` would
 * otherwise resolve to a function and render whatever that stringifies to.
 */
export function writeFailureLine(error: AppError): string {
  const code = error.code;
  if (code !== undefined && Object.prototype.hasOwnProperty.call(BY_CODE, code)) {
    return BY_CODE[code] ?? WRITE_FAILED;
  }
  return WRITE_FAILED;
}

/**
 * How a countdown reads aloud, here as on Now and on the departure screen.
 *
 * The figure alone — `2 h 14 min` — is a number with no noun, and what the slot
 * means is *this is how long is left*.
 */
export function countdownAccessibilityLabel(countdown: string): string {
  return `${countdown} left`;
}
