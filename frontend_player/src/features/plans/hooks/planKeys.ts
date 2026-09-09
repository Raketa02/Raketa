/**
 * This feature's query-key factory — **one key, because one route is read.**
 *
 * `GET /plans` is *your plans, right now*: there is no id to mint one under and asking again is
 * asking the same question, which is `gameKeys`' own reasoning one feature over. A plan is looked
 * up **inside** that answer rather than under a key of its own — there is no `GET /plans/{id}`, so
 * a per-game entry would be a cache key nothing could ever fill.
 *
 * It takes the app-wide defaults whole, and the reason is stronger here than for the games beside
 * it: **nothing on a plan is folded against a clock**. Its day and hour are wall-clock facts drawn
 * literally, so a list served from cache is not merely recent — it is exactly as true as one
 * fetched this second. What makes it current is the app's own focus refetch, and, inside a room,
 * the nudge that invalidates the stream a slot change writes a line into.
 */

export const planKeys = {
  all: ['plans'] as const,
  /** Every plan for a game you are on the court of. Not keyed by game: one list, not several. */
  list: () => [...planKeys.all, 'list'] as const,
};
