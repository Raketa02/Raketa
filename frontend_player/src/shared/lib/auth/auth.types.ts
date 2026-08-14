/**
 * The vocabulary of the auth subsystem. Deliberately small: everything above this layer
 * consumes a *status*, never a token.
 */

/**
 * Three states, explicitly — see docs/architecture.md Part 3.
 *
 * `bootstrapping` is a state and never `user === undefined`. That ambiguity is what
 * produces the two bugs every mobile app ships once: the login screen flashing while
 * valid credentials are still being read out of the keychain, and the authenticated tree
 * flashing before a redirect.
 */
export type SessionStatus = 'bootstrapping' | 'authenticated' | 'unauthenticated';

/**
 * The token pair, as one value.
 *
 * They are always read and written together. Rotation replaces both at once, and a
 * session holding a new access token beside an old refresh token is a session that
 * cannot recover — so the pair, not either half, is the unit of persistence.
 */
export interface Tokens {
  readonly accessToken: string;
  readonly refreshToken: string;
}

/** Why the session ended. Recorded so a screen can say something true about it. */
export type SignOutReason =
  /** The player asked. */
  | 'requested'
  /** The server rejected our credentials — the session was already over. */
  | 'session-invalidated';
