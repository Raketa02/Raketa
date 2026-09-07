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
 * moving under a finger, and this is a set of records with no ordering a player is reading. What
 * it cannot take is the thirty-second `staleTime`: the one screen that reads this reads it
 * *after a refusal*, to say somebody's handle out loud, and a second refusal inside that window
 * would name whoever the first one named. The override is at the hook, where the reason is.
 */

export const challengeKeys = {
  all: ['challenges'] as const,
  /** Every challenge you hold a seat in. Not keyed by sport: the pair rule crosses all four. */
  list: () => [...challengeKeys.all, 'list'] as const,
};
