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
   * question the gate asks is about the player, not about a sport, and how many requests
   * answering it costs is `findRunInProgress`' business rather than the cache's. It cost
   * four and now costs one, and this key did not move.
   */
  runInProgress: () => [...onboardingKeys.all, 'run-in-progress'] as const,
  /**
   * **Every unfinished run**, for the door that carries one sport's on — a friend's ask for a level
   * on Home (#765). **Under `runInProgress`**, so whatever marks that stale or removes it — a start,
   * an answer that ends a run, a completion, an abandonment — reaches this too, by prefix.
   */
  runsInProgress: () => [...onboardingKeys.runInProgress(), 'every'] as const,
  /** The sports the platform serves. Reference data. */
  sports: () => [...onboardingKeys.all, 'sports'] as const,
  assessment: (assessmentId: string) =>
    [...onboardingKeys.all, 'assessment', assessmentId] as const,
};
