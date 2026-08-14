/**
 * The credentials chokepoint. Everything above it consumes a status; nothing above it
 * sees a token value.
 *
 * `readStoredTokens` and `getRefreshToken` are exported because the auth feature's
 * launch-validation and sign-out use-cases need to know *whether* a session exists and
 * which refresh token to revoke. They are the narrowest surface that works — no other
 * module may call SecureStore, and ESLint enforces that.
 */

import { configureHttp } from "@/shared/lib/http";

import { getAccessToken } from "./tokenManager";

export type { SessionStatus, SignOutReason, Tokens } from "./auth.types";

export {
  getSessionStatus,
  resetSessionStatus,
  setSessionStatus,
  subscribeToSession,
  useSessionStatus,
} from "./authSession";

export { beginSession, endSession } from "./session";

export {
  clear as clearStoredTokens,
  getRefreshToken,
  hasTokens,
  load as readStoredTokens,
} from "./tokenManager";

/**
 * Hand the HTTP client its credential adapter.
 *
 * The dependency runs both ways — this subsystem calls the client to sign in, and the
 * client needs this subsystem's access token — so one direction is inverted instead of
 * left as an import cycle. Auth registers itself; the client never imports auth.
 *
 * Called by the bootstrap sequence, before any request can be made.
 */
export function wireHttpCredentials(): void {
  configureHttp({ getAccessToken });
}
