/**
 * This feature's query-key factory — the list, and one challenge under its own id.
 *
 * `GET /challenges` is a **query** and not a mutation, which is the opposite reading from every
 * ranked list in Play and for the reason that separates them: a search is *a mutation whose
 * response is written into `searchKeys.detail(id)`*, minted under an id nothing can re-derive,
 * while this list has no id at all — it is *your challenges, right now*, and asking again is
 * asking the same question.
 *
 * **It takes the app-wide defaults, and overrides one of them.** Play's two postures — nothing
 * background-refetches, nothing retries without the player asking — are about a **ranked list**
 * moving under a finger, and this is a set of records with no ordering a player is reading. Its
 * refetch on focus is not a cost here but the point: foregrounding **is** the once-a-day
 * player's case, and it is what makes the tab bar's count current when they open the app.
 *
 * What it cannot take is the thirty-second `staleTime`, and it now has three readers that all
 * say so: the builder reads this *after a refusal*, to say somebody's handle out loud, and a
 * second refusal inside that window would name whoever the first one named; the Chats section
 * and the bar's badge are a list and a count on screen, where thirty seconds of staleness is
 * the number saying something is waiting when it is not. The override is at the hook, where the
 * reason is, and the three share it because they share the key.
 */

export const challengeKeys = {
  all: ['challenges'] as const,
  /** Every challenge you hold a seat in. Not keyed by sport: the pair rule crosses all four. */
  list: () => [...challengeKeys.all, 'list'] as const,
  /**
   * **One challenge, richly** — the screen you answer on.
   *
   * Keyed by the id where the list is keyed by nothing, because this one genuinely has one: a
   * challenge id is a route param and the answer is about that record alone. The two entries are
   * **not** derived from one another and neither invalidates the other by accident — the list is
   * a fold of every challenge against one instant and this is its own fold against its own, so a
   * row patched from a detail read would be a row measuring its clock from a different moment
   * than the rows beside it.
   *
   * It sits under `all`, and an answer deliberately invalidates **`list()` rather than `all`**:
   * `all` is a prefix that matches this entry too, and invalidating a mounted query refetches
   * it — which would send the request the reply's own redraw exists to make unnecessary. The
   * prefix is what a **sign-out** or a wholesale drop would use; a write that already knows the
   * answer names the entry it does not know.
   */
  detail: (challengeId: string) => [...challengeKeys.all, 'detail', challengeId] as const,
};
