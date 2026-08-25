/**
 * The signed-in player, as the app talks about them.
 *
 * This layer is **types and nothing else**, deliberately. Authentication has no business
 * rule the client is entitled to enforce: whether a password is right, whether an account
 * may sign in, whether a token is still good — every one of those is the server's answer,
 * and a client-side copy of it would be a second, weaker authority that disagrees the
 * first time the backend's rules change. Backend authorization is the only authorization.
 *
 * ADR-0009's escape hatch covers exactly this case: keep the folder for predictability,
 * do not invent a fake invariant to fill it.
 */

/**
 * A `UserResponse` mapped into the app's vocabulary.
 *
 * The wire's `authority`, `is_admin` and `created_at` are deliberately dropped rather
 * than carried: nothing in the player app may branch on them. A client that renders
 * differently for an admin has invented an authorization decision it cannot enforce.
 *
 * `hasPlayerProfile` is the one field that is kept for the opposite reason — the client is
 * *required* to branch on it, at launch, before any route tree exists.
 */
export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  readonly nickname: string;
  /**
   * Whether onboarding's second part has been committed — the entry gate's fourth branch
   * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
   *
   * It travels on the authenticated player rather than as its own read because it is a
   * fact about that player, and because the gate already asks who they are — a second
   * round trip at launch to answer one boolean is what the field on this response avoids.
   * Whether a *Player profile* exists is a per-player question with a per-player answer,
   * which is why it may be one: it is not the per-player onboarding flag the shared
   * glossary bans, and the glossary's own test — *is this really asking whether a rating
   * exists for this sport?* — answers no.
   */
  readonly hasPlayerProfile: boolean;
}

/** What a player types to sign in. Never logged, never persisted. */
export interface SignInCredentials {
  readonly email: string;
  readonly password: string;
}

/** What a player types to create an account. */
export interface Registration {
  readonly email: string;
  readonly nickname: string;
  readonly password: string;
}
