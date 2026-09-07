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
 * ## …except the deal, which is held by the **question** it answers
 *
 * The deck is the one ranked list nothing reads back by id, and the one whose second copy
 * costs something: `POST /deck` excludes everybody already dealt to this player within the
 * server's `DEALT_MEMORY` — one day — so **a second deal is a different ten people**. That is
 * what makes *a spent deal deals again* work, and it is what makes an accidental deal
 * expensive: it spends the pool rather than repeating it.
 *
 * A record held only under the id it minted is a record that cannot be *found again*, and a
 * mutation's response is not held at all — it dies with the screen. Both leave the same hole:
 * every remount of Match me, and every return to a chip already dealt, mints another deal, so
 * a player toggling between Padel and Tennis empties their own deck without answering a card.
 * `deck` below closes it by keying the deal on the **ask** — the sport and the week it was
 * asked on — which is the one key under which *this question has already been answered* is a
 * fact the cache can state.
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
 * (`onboardingKeys.ratings()`, reference data), and the **outstanding-yes count** the deck's
 * ending sentence is written from (AC-5) — the one number in this tab that should move while
 * you look at it.
 *
 * ## Nothing in Play retries without the player asking
 *
 * The tab's second posture, and the twin of the first. Nearly every act here is a mutation and
 * mutations ship `retry: false`; the read-back was the one exception, and giving the default
 * up too is what makes the rule statable rather than nearly true. See `retry` below — and note
 * that the deal, read as a query over a route that **records**, needs that same line for a
 * stronger reason than the read-back does: a retry there is a second recorded deal.
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

import type { Sport } from '@/shared/vocabulary/sport';

import type { SeatedPlayerId } from '../domain/lineup';
import type { PlayIntent } from '../domain/vocabulary';
import { weekIdentity, type WorkingWeek } from '../domain/workingWeek';

/**
 * **What a deal is run under that the request does not carry.**
 *
 * `POST /deck` sends a sport and — where the player improvised one — a week, and that is the
 * whole body. The answer also turns on two facts the server resolves from the player's own
 * profile: the **radius** it searches inside, and the **declaration** it scores under, because
 * the deck has no mode. Neither is a request field, both change the answer, and so both are in
 * the key — which is `query-and-errors.md`'s rule read literally: *every parameter that changes
 * the response is in the key*.
 *
 * Leaving them out is not a small imprecision, it is the deck contradicting its own advice.
 * *Widen in You* is the one piece of advice this surface gives, and a deal held on the sport
 * alone would answer a widened radius with the deal that ran before it: the player does exactly
 * what the empty state asked, and the screen says the same thing back for as long as the
 * process lives.
 */
export interface DealtUnder {
  /** The profile's search radius, in kilometres — the number *Widen in You* points at. */
  readonly radiusKm: number;
  /** The declared Play intent for this sport: the deck reads it where a search reads a mode. */
  readonly intent: PlayIntent;
}

/**
 * **This file is Play's query-key factory**, in `CONTEXT.md`'s sense of the term — the one
 * place the feature's keys are defined. The exported object is named for the *record* rather
 * than for the feature, because [#228](https://github.com/Raketa02/Raketa/issues/228) named it
 * `searchKeys` and every Play surface reads a search; the keys that are not a search's — the
 * outstanding-yes count — join it here rather than starting a second file.
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
   * **Nothing in Play retries without the player asking**, and this is the one line that makes
   * the rule whole.
   *
   * Every other act in this tab is a mutation, and mutations already ship `retry: false`. The
   * read-back of a search is a `GET`, so it inherits the app-wide predicate and would be
   * attempted twice more on a transient failure — which puts the *Try again* the player can
   * see roughly **31 seconds** away (15s of timeout, a second of backoff, another 15s). An
   * automatic retry the player cannot see is a manual retry they cannot reach.
   *
   * For the read-back this is not the phantom-search argument that keeps `TIMEOUT_MS.request`
   * at 15s: a `GET` records nothing, and re-reading a record costs nobody a row. It is purely
   * about the affordance, and it stands beside `refetchOnWindowFocus: false` as the second half
   * of one posture — nothing in this tab moves except when the player asks.
   *
   * **For the deal it is the phantom-search argument itself.** `POST /deck` records before it
   * answers and spends the pool doing it, so an automatic retry there is a second recorded deal
   * and ten more people gone. One line, and the weaker of its two reasons is the one written
   * above it.
   */
  retry: false,
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
   * One search's envelope and its rows — the pool, or a line-up's shortlist.
   *
   * The only key a ranked list **read back by id** is held under. Both routes that mint one
   * and read it again have the identical shape, so a second key per surface would be two cache
   * entries for one kind of record, and a line-up's origin would have nowhere single to be read
   * back from.
   *
   * A deal is the exception and is held under `deck` instead, because nothing reads one back by
   * id and dealing a second time is not free — see the section above.
   */
  detail: (searchId: string) => [...searchKeys.details(), searchId] as const,
  decks: () => [...searchKeys.all, 'deck'] as const,
  /**
   * **The deal on Match me, held by the question it answers**: the sport, and the week it was
   * dealt on.
   *
   * The key is the *ask* rather than the answer, which is what lets the screen tell *I have
   * already asked this* from *I have not asked yet* — the one distinction a mutation cannot
   * make, since its response dies with the component holding it. Coming back to a chip, and
   * coming back to the screen, are then the same fact about the cache and neither one mints a
   * deal.
   *
   * **The week is in it, and travels as a set.** A grid improvised on Find a game is a
   * different question and must deal a different deck — otherwise the player's edit is
   * silently answered by the deal that ran before it. It is `weekIdentity`'s sorted spelling
   * rather than the list itself, because ticks are kept in press order and a cell ticked and
   * unticked leaves the same week in a different order (`domain/workingWeek`).
   *
   * **And the radius and the declaration are in it too**, though neither is on the request:
   * `DealtUnder` above carries that argument. What the key holds is everything that changes the
   * answer, which is a superset of what travels in the body.
   *
   * **The `search_id` is deliberately not in it.** It is minted *by* the answer, so a key
   * carrying it could never be built before the request that produces it — which is the whole
   * of what has to happen here.
   */
  deck: (
    sport: Sport | undefined,
    sentWeek: WorkingWeek | undefined,
    under: DealtUnder | undefined,
  ) =>
    [
      ...searchKeys.decks(),
      sport,
      sentWeek === undefined ? null : weekIdentity(sentWeek),
      under ?? null,
    ] as const,
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
   *
   * **The sport and the mode ride on the request and are deliberately not in the key**, and
   * that is safe rather than lucky: both are **functionally dependent on `search_id`**. A
   * search is per sport and its envelope carries the mode it was priced under, so a forecast
   * citing that id could not be asked under another of either without being refused — and
   * changing either one on the screen orphans the line-up rather than re-keying it
   * (`domain/lineup`'s origin guard). Adding them would mint a second entry for one question.
   */
  forecast: (searchId: string, players: readonly SeatedPlayerId[]) =>
    [...searchKeys.forecasts(), searchId, [...players].sort()] as const,
  /**
   * **Your outstanding yeses, per sport** — the figure the deck's ending sentence counts.
   *
   * The one key here that is not a search's, and it joins this factory rather than starting a
   * second file for the reason stated above: `searchKeys` is named for the record because
   * every Play surface reads a search, and one count is not a second feature's worth of keys.
   *
   * It fed the segment's `Match me · 3` as well until that number was struck for reading as a
   * count of waiting cards; what is left is one reader, on the deck, and the read stays exactly
   * as it was — a yes moves it, and the sentence it is printed in is what makes it answerable.
   *
   * **It is deliberately not under `RANKED_LIST_QUERY_OPTIONS`.** It is a number rather than
   * an ordering, so nothing reorders under a finger when it moves — and it is the one figure
   * in this tab that *should* move while somebody is looking at it, which is exactly what the
   * app-wide defaults give it. It is also **not keyed by sport**: one read answers for all
   * four, the deck filters what it draws, and a key per sport would be four requests for one
   * response.
   */
  interest: () => [...searchKeys.all, 'interest'] as const,
};
