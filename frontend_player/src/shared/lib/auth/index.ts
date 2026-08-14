/**
 * The credentials chokepoint. Everything above it consumes a status; nothing above it
 * sees a token value.
 *
 * `readStoredTokens` and `getRefreshToken` are exported because the auth feature's
 * launch-validation and sign-out use-cases need to know *whether* a session exists and
 * which refresh token to revoke. They are the narrowest surface that works — no other
 * module may call SecureStore, and ESLint enforces that.
 */

import { configureHttp } from '@/shared/lib/http';

import { configureRefresh, refreshSession, type RefreshExchange } from './refreshCoordinator';
import { endSession } from './session';
import { getCredential } from './tokenManager';

export type { SessionStatus, SignOutReason, Tokens } from './auth.types';

export {
  getSessionStatus,
  resetSessionStatus,
  setSessionStatus,
  subscribeToSession,
  useSessionStatus,
} from './authSession';

export { beginSession, endSession } from './session';

export { resetRefresh, type RefreshExchange, type RefreshOutcome } from './refreshCoordinator';

export {
  clear as clearStoredTokens,
  getRefreshToken,
  hasTokens,
  load as readStoredTokens,
} from './tokenManager';

/**
 * Hand the HTTP client its credential adapter.
 *
 * The dependency runs both ways — this subsystem calls the client to sign in, and the
 * client needs this subsystem's access token — so one direction is inverted instead of
 * left as an import cycle. Auth registers itself; the client never imports auth.
 *
 * `exchange` comes from the caller for the same reason the bootstrap sequence takes
 * `restoreSession` from one: the refresh endpoint's path and its generated types live in
 * the auth feature's `api/` layer, and `shared/` may never import a feature. Only the
 * wire call is injected — when to rotate, how to coordinate, and what a failure means all
 * stay in `shared/lib/http` and `refreshCoordinator`.
 *
 * Called by the bootstrap sequence, before any request can be made.
 */
export function wireHttpCredentials(exchange: RefreshExchange): void {
  configureRefresh(exchange);
  configureHttp({
    current: getCredential,
    refresh: refreshSession,
    // The transport only reaches this after a freshly-rotated credential was rejected,
    // which is the same fact a rejected refresh establishes — so it is the same exit.
    abandon: () => endSession('session-invalidated'),
  });
}
