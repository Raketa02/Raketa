/**
 * Every query key this feature uses, in one factory.
 *
 * Inline string keys are how two call sites end up caching the same read under two keys —
 * and how a mutation invalidates one of them.
 */

export const playerProfileKeys = {
  all: ['player-profile'] as const,
  /**
   * The tag vocabulary and its bounds, under **one** key.
   *
   * They arrive in one response because they are needed by the same part of onboarding at
   * the same moment, and splitting the key would turn one round trip into two while
   * pretending they can disagree.
   */
  options: () => [...playerProfileKeys.all, 'options'] as const,
  /**
   * Every fact `GET /players/me/profile` carries: the week, the declarations, and what You
   * draws beside them.
   *
   * **One key for all of them**, because they arrive in one response and are changed by the
   * same acts — the week write and the declaration write each change one of them, and a key
   * per fact would mean cache entries a single response has to be split across.
   *
   * It is on the **ordinary defaults** and refetches, unlike anything in Play holding a ranked
   * list: `searchKeys.ts` names *"the profile and the week grid behind the working copy"* among
   * the reads that should move while you look at them.
   */
  surface: () => [...playerProfileKeys.all, 'surface'] as const,
  /**
   * The signed address of one of the player's own photographs — what a tile on the You tab
   * draws a held photo from. Its own entry per id, so a row of three is three reads that
   * each say their own standing, and a re-arrangement re-reads nothing.
   */
  photo: (photoId: string) => [...playerProfileKeys.all, 'photo', photoId] as const,
};
