/**
 * The wire boundary: generated DTO -> the app's own objects.
 *
 * Its job is to stop transport naming leaking upward. `access_token` and `is_admin` are
 * FastAPI's spelling of things; above this line the app says `accessToken`, and says
 * nothing at all about `is_admin` because it must not branch on it.
 */

import type { components } from '@/generated/schema';
import type { Tokens } from '@/shared/lib/auth';

import type { AuthenticatedUser, Naming } from '../domain/AuthenticatedUser';

type TokenResponse = components['schemas']['TokenResponse'];
type UserResponse = components['schemas']['UserResponse'];
type NamingResponse = components['schemas']['NamingResponse'];

/**
 * `expires_in` is deliberately dropped. Expiry is discovered from the server's 401, not
 * predicted from a clock: a phone's clock is user-settable and routinely wrong, and a
 * client that pre-emptively refreshed on its own arithmetic would rotate tokens against
 * a server that never asked it to.
 */
export function toTokens(wire: TokenResponse): Tokens {
  return {
    accessToken: wire.access_token,
    refreshToken: wire.refresh_token,
  };
}

export function toAuthenticatedUser(wire: UserResponse): AuthenticatedUser {
  // `null` on the wire is *not yet named* — the one read where it may be (ADR-0171 §2) — and
  // it is carried as absence, which is how every other shape in this app spells a name it
  // does not have. The entry gate reads the absence.
  const name = wire.name ?? undefined;
  const nickname = wire.nickname ?? undefined;
  return {
    id: wire.id,
    email: wire.email,
    ...(name === undefined ? {} : { name }),
    ...(nickname === undefined ? {} : { nickname }),
    // Kept where `is_admin` is dropped, because the app must branch on it: the entry gate
    // reads it to decide whether onboarding's second part is still owed. It defaults to
    // false on the wire for responses that are not about the authenticated player — such
    // as the one registration returns — and a brand-new account has no profile anyway.
    hasPlayerProfile: wire.has_player_profile,
    // Kept where `is_admin` is dropped for the opposite reason to theirs: it grants nothing.
    // Its one reader is flag evaluation, which decides which build of a screen is drawn and
    // never what anybody may do (ADR-0180 §9).
    isTester: wire.is_tester,
  };
}

/** What the naming recorded: the name as normalised by the server, and the handle. */
export function toNaming(wire: NamingResponse): Naming {
  return { name: wire.name, nickname: wire.nickname };
}
