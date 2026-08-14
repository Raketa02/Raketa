/**
 * The wire boundary: generated DTO -> the app's own objects.
 *
 * Its job is to stop transport naming leaking upward. `access_token` and `is_admin` are
 * FastAPI's spelling of things; above this line the app says `accessToken`, and says
 * nothing at all about `is_admin` because it must not branch on it.
 */

import type { components } from '@/generated/schema';
import type { Tokens } from '@/shared/lib/auth';

import type { AuthenticatedUser } from '../domain/AuthenticatedUser';

type TokenResponse = components['schemas']['TokenResponse'];
type UserResponse = components['schemas']['UserResponse'];

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
  return {
    id: wire.id,
    email: wire.email,
    nickname: wire.nickname,
  };
}
