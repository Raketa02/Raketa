/**
 * Every query key this feature uses, in one factory.
 *
 * Inline string keys are how two call sites end up caching the same read under two keys —
 * and how a mutation invalidates one of them. Every parameter that changes the response
 * is part of the key.
 */

export const onboardingKeys = {
  all: ['onboarding'] as const,
  /** The player's ratings, one per rated sport. */
  ratings: () => [...onboardingKeys.all, 'ratings'] as const,
  /**
   * "Is any assessment unfinished?" — deliberately **not** parameterised by sport. The
   * question the gate asks is about the player, not about a sport; the four per-sport
   * requests behind it are an implementation detail of `findRunInProgress`.
   */
  runInProgress: () => [...onboardingKeys.all, 'run-in-progress'] as const,
  /** The sports the platform serves. Reference data. */
  sports: () => [...onboardingKeys.all, 'sports'] as const,
  assessment: (assessmentId: string) =>
    [...onboardingKeys.all, 'assessment', assessmentId] as const,
};
