/**
 * Every query key this feature uses, in one factory.
 *
 * Inline string keys are how two call sites end up caching the same read under two keys —
 * and how a mutation invalidates one of them.
 */

export const playerProfileKeys = {
  all: ['player-profile'] as const,
  /**
   * The tag vocabulary and the bounds, under **one** key.
   *
   * They arrive in one response because they are needed by the same part of onboarding at
   * the same moment, and splitting the key would turn one round trip into two while
   * pretending they can disagree.
   */
  options: () => [...playerProfileKeys.all, 'options'] as const,
  /**
   * The three facts `GET /players/me/profile` carries: the week, the radius, the declaration.
   *
   * **One key for the three**, because they arrive in one response and are invalidated by the
   * same acts — the radius write and the declaration write each change one of them, and a key
   * per fact would mean three cache entries a single response has to be split across.
   *
   * It is on the **ordinary defaults** and refetches, unlike anything in Play holding a ranked
   * list: `searchKeys.ts` names *"the profile and the week grid behind the working copy"* among
   * the reads that should move while you look at them.
   */
  surface: () => [...playerProfileKeys.all, 'surface'] as const,
};
