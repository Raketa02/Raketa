/**
 * **What a refused send costs the screen next** — three outcomes, and two of them are a read.
 *
 * *"A refused send is followed by a re-read, never by a payload"*
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §11.9).
 * The refusal states the class of problem and names nobody: `AppError.details` is
 * `Dict[str, Any]`, invisible to the backend's own response fence and ungeneratable against
 * ADR-0006, so a client that rendered a name straight off a refusal *"has found a shape this
 * contract does not have"*.
 *
 * This turns the code into the **act the screen owes**, which is the thing the two refusals
 * actually differ in:
 *
 * | | |
 * | --- | --- |
 * | `line_up_no_longer_sendable` | Read the **origin search** back. Its withheld rows mark the seats. |
 * | `open_challenge_stands` | Read **your own challenges**. One of them names the pair. |
 * | anything else | Say what it says, and read nothing. |
 *
 * **It is a code and never a status.** Both refusals are `409`, and so is
 * `court_origin_not_found`, which is neither of them — branching on the status would send an
 * orphaned line-up off to re-read a search that is gone.
 *
 * ## Why re-running the search is not one of the arms
 *
 * A line-up is bound to one `search_id` and `POST /forecasts` refuses anybody who did not
 * appear in it, so a re-run mints an id the whole line-up must adopt — and its untouched seats
 * are only *probably* in the new answer, since a re-rank or the twenty-row cap can drop a seat
 * nobody touched. That is H-18's harm arriving through the remedy rather than through the
 * fault, and it is why this type has a *re-read* arm and no *re-run* one at all.
 */

import type { AppError } from '@/shared/errors';

/**
 * What the court does about a refusal.
 *
 * A discriminated union rather than a boolean pair: the two reads are different acts against
 * different sources, and a screen holding two flags could start both.
 */
export type SendRefusal =
  /** The four fail-closed gates, indistinguishably. Re-read the origin search. */
  | { readonly kind: 'READ_THE_ORIGIN_BACK' }
  /** #221's pair rule, in any sport. Re-read the player's own challenges. */
  | { readonly kind: 'READ_YOUR_CHALLENGES' }
  /** Everything else — an orphaned origin, a hold, an outage, a caller's bug. */
  | { readonly kind: 'SAY_SO'; readonly error: AppError };

export function sendRefusal(error: AppError): SendRefusal {
  if (error.code === 'line_up_no_longer_sendable') return { kind: 'READ_THE_ORIGIN_BACK' };
  if (error.code === 'open_challenge_stands') return { kind: 'READ_YOUR_CHALLENGES' };
  return { kind: 'SAY_SO', error };
}
