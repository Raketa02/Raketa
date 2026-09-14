/**
 * **A stale tap is a re-read, not a toast** — the three things a refused act on the challenge
 * screen costs it, and no new copy for any of them.
 *
 * `sendRefusal`'s shape one context over, and its argument transfers whole: an `AppError` has
 * nowhere typed to put a payload, so what a refusal buys is *which read to make next* rather than
 * a sentence chosen off a code.
 *
 * **It is named for the acts and not for the answers**, because there are five of them now and
 * they refuse in the same three ways: `I'm in`, `Not this time`, `Remove the challenge`, the fill
 * on the builder this screen pushes — and, on the **game** screen, *Leave this game*. What they share is
 * a subject: every one of these codes says *this challenge is not what the screen thought it
 * was*, and the honest answer to that is to read it again. For the departure the read is the
 * games list, because that is what its screen folds from; the fold is the same.
 *
 * | Refusal | What the screen does |
 * | --- | --- |
 * | `answer_window_has_passed` | **Re-read and redraw.** The player lands on *Your day ran out*. |
 * | `seat_already_answered` | **Re-read and redraw.** Answered elsewhere — the two-devices case. |
 * | `not_a_half_built_line_up` | **Re-read and redraw.** The withdraw's own: this court has some other end already. |
 * | `withdraw_is_the_organisers` | **Re-read and redraw.** The control was drawn for a side the reader is not on. |
 * | `somebody_has_joined` | **Re-read and redraw.** *Remove the challenge*'s own (ADR-0165 §4): somebody said yes under the finger, and the arm re-folds to *Leave the game*. |
 * | `fill_is_the_live_members` | **Re-read and redraw.** The reader left this court while they were building on it. |
 * | `challenge_is_over` | **Re-read and redraw.** It ended under the builder, or under the leave. |
 * | `not_a_game_yet` | **Re-read and redraw.** The departure's own: this court was never a game. |
 * | `game_is_history` | **Re-read and redraw.** The game has happened, or never will — an ending. |
 * | `game_moment_has_passed` | **Re-read and redraw.** The agreed moment passed under the finger; the control goes with it. |
 * | `challenge_not_found` | **Leave the screen.** It is gone, or it was never yours — or, on a departure, you hold no accepted seat on it. |
 * | anything else | Say what it says, and read nothing. |
 *
 * **It is a code and never a status.** Two of the re-read arms are `409`, one is `403` and one is
 * `404`-adjacent, and `sendRefusal` states the rule the same way for the same reason: the next
 * refusal added to any of these routes will share a status with one of them
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §2.4).
 *
 * ## The re-reads need no words, and that is the whole reason there are three arms
 *
 * Every sentence they land on is **already written and tested**: *Your day ran out* is §13's
 * `LAPSED` invitee sentence, *You said no* its `DECLINED` one, *You withdrew this* its
 * `WITHDRAWN` one, and the detail read derives whichever is now true. A sentence chosen here
 * would be a second, worse copy of a standing the server folds — and it would be drawn *beside*
 * the standing sentence, saying the same thing twice in two voices. **Four of the six re-read
 * codes are the same mistake from four directions**: the screen offered a control the challenge
 * no longer has, and what corrects that is the fold rather than an apology.
 *
 * `challenge_not_found` is **one code for two cases** on purpose — it does not exist, or you are
 * not on its court — so there is nothing to tell apart and nowhere to stay. The screen leaves.
 *
 * ## Why there is no *retry* arm
 *
 * An answer is not idempotent, deliberately: *yes* after *no* is a different answer and not a
 * repeat of one. Neither is a withdraw, which has no route back, or a fill, which dates a day for
 * everybody it seats. So an arm that re-sent would be the one thing this feature refuses in every
 * other place — an act repeated by the app rather than by the player.
 */

import type { AppError } from '@/shared/errors';

/**
 * What the screen does about a refused act.
 *
 * A discriminated union rather than a pair of booleans: *re-read* and *leave* are different acts,
 * and a screen holding two flags could do both.
 */
export type ActRefusal =
  /**
   * The challenge moved under the finger. **Re-read and redraw** — the standing the read comes
   * back with is the sentence, and it is one that already exists.
   */
  | { readonly kind: 'READ_IT_BACK' }
  /** No challenge of yours has this id. There is nothing behind this screen, so leave it. */
  | { readonly kind: 'LEAVE' }
  /** Everything else — a hold, an outage, a connection that was not there. */
  | { readonly kind: 'SAY_SO'; readonly error: AppError };

/**
 * The codes that mean *this challenge is not what the screen thought it was*.
 *
 * A `Set` over the literal codes rather than a chain of comparisons, because the list is now
 * long enough that a missing `||` would read as deliberate.
 */
const READ_IT_BACK: ReadonlySet<string> = new Set([
  'answer_window_has_passed',
  'seat_already_answered',
  'not_a_half_built_line_up',
  'withdraw_is_the_organisers',
  'somebody_has_joined',
  'fill_is_the_live_members',
  'challenge_is_over',
  'not_a_game_yet',
  'game_is_history',
  'game_moment_has_passed',
]);

export function actRefusal(error: AppError): ActRefusal {
  if (error.code !== undefined && READ_IT_BACK.has(error.code)) return { kind: 'READ_IT_BACK' };
  if (error.code === 'challenge_not_found') return { kind: 'LEAVE' };
  return { kind: 'SAY_SO', error };
}
