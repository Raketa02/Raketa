/**
 * **A retry belongs to the act that failed, never to the screen it failed on.**
 *
 * Play runs two acts against the same record and they are not interchangeable: `POST /searches`
 * **mints** one, `GET /searches/{id}` **re-reads** it. So *Try again* is ambiguous exactly once
 * — on the pool, which is reached after a search has already run — and the ambiguity is
 * expensive. Re-running the search mints a new id and **orphans the line-up bound to the old
 * one**; `POST /forecasts` answers that with `404 search_not_found`, which is deliberately one
 * code for four cases, so a client that did this to itself could not even diagnose it.
 *
 * The rule is one line: **no record id, re-fire the `POST`; a record id exists, re-read.**
 * Running a fresh search stays an explicit act the player chooses, which is also what keeps it
 * inside the origin guard instead of arriving as a fourth trigger that guard never sees.
 *
 * ## Where the control is
 *
 * Placement follows from the rule rather than being chosen per screen: the retry is the failed
 * act's **own control**. Three of the four sites are a button the screen already has — Find a
 * game's *Search*, the court's ⚡ fill, and the pool's re-read — and only the **forecast** gains
 * one, because a player who has stopped changing seats would otherwise sit with no number and
 * no way to ask again. Those four controls arrive with the screens that draw them; what is here
 * is the decision they all read.
 *
 * ## Why there is no timeout to give up on
 *
 * `TIMEOUT_MS.request` stays at 15s against a specification that asked for eight, because a
 * search is a **recording** write on a route documented *"deliberately not idempotent — two
 * taps are two searches"*: giving up at 8s on an answer arriving at 9s leaves a recorded search
 * nobody read, and its retry records a second. The wait is bounded by this file's other half
 * instead — **nothing in Play retries without the player asking**
 * ([`searchKeys.ts`](../hooks/searchKeys.ts)) — so the worst case is one timeout rather than a
 * chain of them.
 */

/** The act a *Try again* re-runs. Two acts, two ids, and never the wrong one. */
export type RetryTarget =
  /** Nothing was recorded, so there is nothing to re-read. This mints a record. */
  | { readonly kind: 'the-search' }
  /** A record exists. Re-reading it costs nobody a row and orphans nothing. */
  | { readonly kind: 'the-record'; readonly searchId: string };

/**
 * @param mintedSearchId the id this wait already recorded, or `undefined` when the search
 *   itself is what failed.
 */
export function retryTarget(mintedSearchId: string | undefined): RetryTarget {
  if (mintedSearchId === undefined) return { kind: 'the-search' };
  return { kind: 'the-record', searchId: mintedSearchId };
}
