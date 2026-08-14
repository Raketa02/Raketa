/**
 * The three auth mutations, as semantic hooks.
 *
 * Each one declares its own retry decision at the call site, because the global default
 * is `retry: false` and overriding it silently is how a mutation gets repeated.
 */

import { useMutation } from "@tanstack/react-query";

import type { AppError } from "@/shared/errors";

import type { Registration, SignInCredentials } from "../domain/AuthenticatedUser";
import { signIn } from "../use-cases/signIn";
import { signOut } from "../use-cases/signOut";
import { signUp } from "../use-cases/signUp";

/**
 * **Not retried.** A failed sign-in is almost always a wrong password, and repeating it
 * walks the account toward whatever lockout policy the backend has. The player retries
 * by tapping the button.
 *
 * No cache write on success: the session status change is what moves the app, and the
 * profile is fetched by `useCurrentUser` once the authenticated tree renders.
 */
export function useSignIn() {
  return useMutation<void, AppError, SignInCredentials>({
    mutationFn: signIn,
    retry: false,
  });
}

/**
 * **Not retried, and this one matters.** Registration creates a record. A silent retry
 * of a request that actually succeeded but whose response was lost would ask the backend
 * to create the same account twice — and the second attempt fails as
 * `email_already_registered`, which the player would read as "that didn't work" about an
 * account that now exists.
 */
export function useSignUp() {
  return useMutation<void, AppError, Registration>({
    mutationFn: signUp,
    retry: false,
  });
}

/**
 * **Not retried.** The use-case already treats the server revoke as best-effort and
 * always tears the local session down, so there is nothing a retry could improve.
 */
export function useSignOut() {
  return useMutation<void, AppError, void>({
    mutationFn: signOut,
    retry: false,
  });
}
