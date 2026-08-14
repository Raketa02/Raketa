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
 */
export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  readonly nickname: string;
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
