/**
 * This feature's query-key factory — one key, because one route is read.
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
};
