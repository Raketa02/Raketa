/**
 * This feature's query-key factory — **one key, because one route is read.**
 *
 * `GET /sportsmanship` is *what is still waiting for your stars, right now*: there is no id to
 * mint one under and asking again is asking the same question, which is what makes it a query
 * where every ranked list in Play is a mutation-minted record. A card is looked up **inside**
 * that answer, exactly as a game is inside its own list — there is no route that serves one.
 *
 * It takes the app-wide defaults whole, `gameKeys`' reasoning applied to the list drawn beside
 * it: Play's two postures are about a **ranked list moving under a finger**, and this is a set
 * of chores in an order nobody reads against. The refetch on focus is what makes a card
 * answered on another device stop standing here.
 */

export const cardKeys = {
  all: ['sportsmanship'] as const,
  /** Every card waiting for you. Not keyed by sport or by game: one list and not several. */
  open: () => [...cardKeys.all, 'open'] as const,
};
