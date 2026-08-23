/**
 * The screen's own sentences — the ones about *the screen* rather than about an
 * outcome.
 *
 * An outcome's three renderings come off `mappers/outcomes.ts`, and the match's
 * own sentence comes off Now's situation table. These are the title, the
 * headings, the three reasons printed beside the quote, and the two failures.
 *
 * **The title is the prototype's own.** `ADR-0086` quotes it while arguing about a
 * different control — *"the prototype's own screen title is `I can't make it`, not
 * `Cancel my position`"* — and it is the right title for the same reason it was
 * quoted: this screen is not an administrative act, it is a person saying she
 * cannot come, and the screen's job is to tell her what that costs before she
 * says it.
 *
 * **There is no by-recovery table here, and that is deliberate.** This app already
 * holds three, and `nowCopy.ts` records that *"a fourth is the signal to move it"*
 * to `shared/`. These two sentences are not a fourth: they are about *this* act —
 * one screen that could not be composed, and one write that never reached the
 * server — and neither varies by recovery category. The one category that would
 * have earned a branch, a session that has ended, is handled above every feature
 * by the redirect in `(app)/_layout.tsx`.
 */

/** What the screen is. The player's own words, not the platform's. */
export const DEPARTURE_TITLE = "I can't make it";

/** What the close control does, named by its consequence rather than by its glyph. */
export const CLOSE_LABEL = 'Close, and keep your seat';

/** The four outcomes, headed so the table reads as a timeline rather than a menu. */
export const OUTCOMES_HEADING = 'What you have passed, and what is ahead';

/** The three reasons behind the quote, drawn beside it. */
export const REASON_LABEL = {
  /** Absent on a private court — the court was bought at booking, so there is none. */
  commitment: 'Commitment deadline',
  seat: 'Your seat',
  paid: 'Seats paid',
  /** Only when there are any: a held seat is a name with no money behind it. */
  held: 'Seats held',
} as const;

/** `2 of 4` — how full the match is, counted by money. */
export function paidOfSeats(paid: number, seats: number): string {
  return `${paid} of ${seats}`;
}

/**
 * What the screen says when the quote fell between the tap and the apply — or when
 * any of the other four refusals fired.
 *
 * **One sentence for all five**, because it is the only one true of all of them: a
 * quote that fell, a match that started, a match that was cancelled, the
 * private-court lock, and a second tap by somebody who has already left. Saying
 * *you still hold your seat* would be false on the last of those, and the screen
 * she is looking at already says which one it was — that is the whole point of
 * answering a refusal with what a success returns.
 */
export const REFUSED_TITLE = 'This has moved on';
export const REFUSED_LINE = 'Nothing was applied. What you are looking at is what is true now.';

/** What the screen says once the departure is made, above the way back. */
export const LEFT_TITLE = 'You have left';

/** The one control on a screen that has nothing left to ask. */
export const DONE_LABEL = 'Back to your matches';

/** A cold open that did not land. The player can ask again from here. */
export const LOAD_FAILED = 'We could not work out what leaving this match is worth.';
export const RETRY_LABEL = 'Try again';

/**
 * A write that never reached the server.
 *
 * It says *nothing has changed* because nothing has: a request that failed in
 * transport applied nothing, and pressing again re-sends the **same** key, so a
 * request that in fact did land is answered with what it did rather than applied
 * twice.
 */
export const WRITE_FAILED = 'That did not go through, and nothing has changed. Try again.';

/**
 * How a countdown reads aloud, here as on Now.
 *
 * The figure alone — `2 h 14 min` — is a number with no noun, and what the slot
 * means is *this is how long is left*.
 */
export function countdownAccessibilityLabel(countdown: string): string {
  return `${countdown} left`;
}
