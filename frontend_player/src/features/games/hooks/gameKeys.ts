/**
 * This feature's query-key factory — **one key, because one route is read.**
 *
 * `GET /games` is *your games, right now*: there is no id to mint one under and asking again is
 * asking the same question, which is what makes it a query where every ranked list in Play is a
 * mutation-minted record. A game is looked up **inside** that answer rather than under a key of
 * its own — there is no `GET /games/{id}`, so a per-game entry would be a cache key nothing
 * could ever fill.
 *
 * It takes the app-wide defaults whole. Play's two postures — nothing background-refetches,
 * nothing retries without the player asking — are about a **ranked list moving under a finger**,
 * and this is a set of records with an order the player is not reading against. The thirty-second
 * `staleTime` is right here for a reason the countdown makes concrete: every duration on screen
 * is measured from the list's own `read_at`, so a list served from cache is **internally
 * consistent** rather than merely recent, and a refetch on focus is what makes it current.
 */

export const gameKeys = {
  all: ['games'] as const,
  /** Every game you were on the court of. Not keyed by sport: one list and not several. */
  list: () => [...gameKeys.all, 'list'] as const,
};
