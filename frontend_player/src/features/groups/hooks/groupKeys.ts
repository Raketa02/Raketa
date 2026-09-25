/**
 * This feature's query-key factory — **every key it uses, with every parameter that changes the
 * answer.**
 *
 * The two searches are keyed by **the text**, trimmed, because each keystroke is a new question
 * and a key per text is what lets the answer to `ogr` stay on screen while `ogro` is being asked
 * (`placeholderData`). The page is the infinite query's own cursor rather than part of the key:
 * the pages of one text are one answer, read twenty clubs at a time.
 *
 * Everything sits under one root, so a sign-out's `queryClient.clear()` takes it all and a join
 * can reach every cached search at once (`searches()`).
 */

export const groupKeys = {
  all: ['groups'] as const,
  /** The reader's Groups list, newest joined first. */
  mine: () => [...groupKeys.all, 'mine'] as const,
  /** One group, as its page reads it. */
  detail: (groupId: string) => [...groupKeys.all, 'detail', groupId] as const,
  /** Every cached search — the root a join rewrites. */
  searches: () => [...groupKeys.all, 'search'] as const,
  /** New group's home-club search, for one text. */
  homeClubs: (text: string) => [...groupKeys.searches(), 'home-clubs', text] as const,
  /** Join a group's search, for one text. */
  toJoin: (text: string) => [...groupKeys.searches(), 'join', text] as const,
};
