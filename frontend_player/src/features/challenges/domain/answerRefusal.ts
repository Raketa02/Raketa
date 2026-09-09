/**
 * **A stale tap is a re-read, not a toast** — the four things a refused answer costs the screen,
 * and no new copy for any of them.
 *
 * `sendRefusal`'s shape one context over, and its argument transfers whole: an `AppError` has
 * nowhere typed to put a payload, so what a refusal buys is *which read to make next* rather than
 * a sentence chosen off a code.
 *
 * | Refusal | What the screen does |
 * | --- | --- |
 * | `answer_window_has_passed` | **Re-read and redraw.** The player lands on *Your day ran out*. |
 * | `seat_already_answered` | **Re-read and redraw.** Answered elsewhere — the two-devices case. |
 * | `challenge_not_found` | **Leave the screen.** It is gone, or it was never yours. |
 * | anything else | Say what it says, and read nothing. |
 *
 * **It is a code and never a status.** Both re-read arms are `409` and so is nothing else here,
 * but the rule is stated the same way `sendRefusal` states it because the next refusal added to
 * this route will share a status with one of them
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §2.4).
 *
 * ## The two re-reads need no words, and that is the whole reason there are two arms
 *
 * Both sides of a closed window are **already written and tested**: *Your day ran out* is §13's
 * `LAPSED` invitee sentence and *You said no* its `DECLINED` one, and the detail read derives
 * whichever is now true. A sentence chosen here would be a second, worse copy of a standing the
 * server folds — and it would be drawn *beside* the standing sentence, saying the same thing
 * twice in two voices.
 *
 * `challenge_not_found` is **one code for two cases** on purpose — it does not exist, or you are
 * not on its court — so there is nothing to tell apart and nowhere to stay. The screen leaves.
 *
 * ## Why there is no *retry* arm
 *
 * An answer is not idempotent, deliberately: *yes* after *no* is a different answer and not a
 * repeat of one. So an arm that re-sent would be the one thing this feature refuses in every
 * other place — an act repeated by the app rather than by the player.
 */

import type { AppError } from '@/shared/errors';

/**
 * What the screen does about a refused answer.
 *
 * A discriminated union rather than a pair of booleans: *re-read* and *leave* are different acts,
 * and a screen holding two flags could do both.
 */
export type AnswerRefusal =
  /**
   * The offer moved under the finger, or another device answered first. **Re-read and redraw** —
   * the standing the read comes back with is the sentence, and it is one that already exists.
   */
  | { readonly kind: 'READ_IT_BACK' }
  /** No challenge of yours has this id. There is nothing behind this screen, so leave it. */
  | { readonly kind: 'LEAVE' }
  /** Everything else — a hold, an outage, a connection that was not there. */
  | { readonly kind: 'SAY_SO'; readonly error: AppError };

export function answerRefusal(error: AppError): AnswerRefusal {
  if (error.code === 'answer_window_has_passed' || error.code === 'seat_already_answered') {
    return { kind: 'READ_IT_BACK' };
  }
  if (error.code === 'challenge_not_found') return { kind: 'LEAVE' };
  return { kind: 'SAY_SO', error };
}
