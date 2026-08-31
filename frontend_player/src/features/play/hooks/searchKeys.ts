/**
 * Every query key Play uses, and the one **override of the global defaults** that goes with
 * two of them.
 *
 * ## A ranked list is a record, read by id
 *
 * `POST /searches`, `POST /lineups` and `POST /deck` each mint a `search_id` and record the
 * answer server-side; `GET /searches/{search_id}` reads one back *"in the same shape the
 * `POST` returned it"*. So a search is a **mutation whose response is written into
 * `searchKeys.detail(id)`** — Part 7's *"prefer response-driven updates… don't immediately
 * refetch what you were just handed"* — and every Play screen reads the list **by id** rather
 * than from a store. That is what makes AC-70 arithmetic: an abandoned search wrote its rows
 * under its own id, and nothing reads that entry.
 *
 * ## Nothing in Play background-refetches
 *
 * The app's defaults are `staleTime: 30_000` and `refetchOnWindowFocus: true`, wired to
 * `AppState` through `shared/lib/platform`. Left alone, **foregrounding the app would reorder
 * the pool under the player's finger** — the same harm AC-70 forbids, arriving from focus
 * instead of from an abandoned search. §J6 puts the ranked list under *"may be prepared in
 * advance — for the life of one search"*, and that life ends when another search is run, never
 * on a timer.
 *
 * So: **`staleTime: Infinity` and `refetchOnWindowFocus: false` on every ranked list.** Part 7
 * sanctions this in writing — *"data classes that differ override it in their own feature
 * hook, which is where that decision belongs."* Gate drift is picked up on the next visit's
 * read-back, which is exactly what `GET /searches/{id}`'s **withheld rows** are for: the
 * record is immutable and the gates are live, so a row the product has since agreed not to
 * show keeps its place and says that it is withheld.
 *
 * **What still refetches on the ordinary defaults**, and should: the profile and the week grid
 * behind the working copy (moderate, 30s), the ratings behind the sport chips
 * (`onboardingKeys.ratings()`, reference data), and the **Match me count** on the segment
 * (AC-5) — the one number in this tab that should move while you look at it.
 *
 * ## Re-sorting costs no round trip; only membership does
 *
 * `SearchEnvelope.sorts_available` is *"which re-sorts the client may draw over rows it
 * already holds… re-sorting costs no round trip"*, and a sort that would reorder nothing is
 * not in the list. **A sort is therefore in no key at all** — AC-113's four are client-side
 * orderings of rows already held, and a sort in the key would mint a cache entry per sort and
 * a request behind each one.
 *
 * The forecast is the same rule on the builder. `ForecastResponse` returns *"three
 * arrangements of a four you composed"*, each with its own forecast — so **swapping two seats
 * selects a different arrangement from a response already held**, instantly and with no
 * network. Only a *membership* change — add, replace, remove — is a new call, which is why
 * `forecast` keys on the **set** of players and not on their order.
 */

import type { SeatedPlayerId } from '../domain/lineup';

/**
 * **This file is Play's query-key factory**, in `CONTEXT.md`'s sense of the term — the one
 * place the feature's keys are defined. The exported object is named for the *record* rather
 * than for the feature, because [#228](https://github.com/Raketa02/Raketa/issues/228) named it
 * `searchKeys` and every Play surface reads a search; the keys that are not a search's — the
 * Match me count on the segment — join it here rather than starting a second file.
 */

/**
 * The query options every ranked list in Play is read under.
 *
 * One constant rather than three lines repeated in three hooks: the override is a decision
 * about a data class, and a surface that copied only part of it would background-refetch
 * exactly where the reordering is worst.
 */
export const RANKED_LIST_QUERY_OPTIONS = {
  /** Superseded by running another search, and by nothing else — never by a timer. */
  staleTime: Infinity,
  /** Foregrounding must not reorder the pool under the player's finger. */
  refetchOnWindowFocus: false,
  /**
   * **The record outlives the screens that read it**, which `staleTime` alone does not give.
   *
   * The app-wide `gcTime` is five minutes of not being rendered, and Find a game renders no
   * search — so a player who built four seats, walked back, and thought about it for six
   * minutes would return to a line-up whose origin had been collected. The rows behind it
   * would be gone, and so would the fact the guard reads to know the line-up is worth a
   * confirmation. A record §J6 scopes to *"the life of one search"* cannot have a shorter
   * lifetime than the session holding a reference to it.
   *
   * The cost is bounded and paid for: entries accumulate for one process, and the cache is
   * cleared on sign-out as a privacy control (Part 7, cache isolation), so nothing here
   * survives a session it was not part of.
   */
  gcTime: Infinity,
} as const;

export const searchKeys = {
  all: ['play', 'search'] as const,
  details: () => [...searchKeys.all, 'detail'] as const,
  /**
   * One search's envelope and its rows — the pool, a line-up's shortlist, or a deal.
   *
   * The **only** key a ranked list is held under. Three routes mint one and the shape is
   * identical across them, so a second key per surface would be three cache entries for one
   * kind of record, and a line-up's origin would have nowhere single to be read back from.
   */
  detail: (searchId: string) => [...searchKeys.details(), searchId] as const,
  forecasts: () => [...searchKeys.all, 'forecast'] as const,
  /**
   * What a four you composed would leave on court, keyed by `(search_id, the set of players)`.
   *
   * The ids are **sorted into the key**, so the same four in a different seat order is the same
   * entry: re-arranging is choosing another arrangement out of a response already held, and a
   * key that kept seat order would spend a round trip on a swap that has none.
   *
   * `search_id` is in the key because it is the Origin key of the request: the same four off
   * two different searches are two different questions, and the route refuses the ones that
   * did not appear.
   */
  forecast: (searchId: string, players: readonly SeatedPlayerId[]) =>
    [...searchKeys.forecasts(), searchId, [...players].sort()] as const,
};
