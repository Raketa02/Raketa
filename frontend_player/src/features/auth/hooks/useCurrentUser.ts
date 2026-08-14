/**
 * The signed-in player's profile — backend data, so TanStack Query owns it and nothing
 * mirrors it. The session machine holds a status and deliberately not this.
 */

import { useQuery } from "@tanstack/react-query";

import { useSessionStatus } from "@/shared/lib/auth";
import type { AppError } from "@/shared/errors";

import { me } from "../api/authApi";
import type { AuthenticatedUser } from "../domain/AuthenticatedUser";
import { toAuthenticatedUser } from "../mappers/authMappers";

import { authKeys } from "./authKeys";

/**
 * `enabled` on the session status, not on a token: an unauthenticated launch must not
 * fire an authenticated request that can only 401, and a 401 fired at launch is exactly
 * what would make the rotation chase a session that never existed.
 *
 * Bootstrap seeds this key when it validated a stored session, so a warm launch renders
 * the profile without a second request.
 */
export function useCurrentUser() {
  const status = useSessionStatus();

  return useQuery<AuthenticatedUser, AppError>({
    queryKey: authKeys.currentUser(),
    queryFn: ({ signal }) => me({ signal }).then(toAuthenticatedUser),
    enabled: status === "authenticated",
  });
}
