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
};
