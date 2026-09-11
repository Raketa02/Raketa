/**
 * This feature's query-key factory — **one query key, because one route is read** — and the one
 * mutation key its writes share.
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
  /**
   * **The key every plan write is made under** — a *mutation* key, `conversationKeys.sending`'s
   * shape one feature over.
   *
   * It is what `useMutationState` filters on to find the refusals the room folds *held* from: a
   * hold is a fact about the **account**, so the room needs every write on its screen and four of
   * the five are this feature's. **Not keyed per game**, deliberately — a hold met on one plan is
   * true in every room, and the one thing read off this key is the account's standing.
   */
  writing: () => [...planKeys.all, 'writing'] as const,
};
