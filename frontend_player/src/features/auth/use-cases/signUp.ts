/**
 * Create an account and sign in with it.
 *
 * Two requests, one workflow — which is exactly why it is a use-case and not an `api/`
 * function. `POST /api/v1/users` returns the created user, not a token pair, so an app
 * that stopped there would leave a new player looking at a sign-in form and wondering
 * whether their account exists.
 */

import { register } from "../api/authApi";
import type { Registration } from "../domain/AuthenticatedUser";

import { signIn } from "./signIn";

/**
 * The password is sent twice because the backend asks for both halves and checks them
 * server-side. The form checks the match too, so the player is told before a round trip
 * — but the server's copy of the rule is the one that counts.
 *
 * If registration succeeds and the sign-in that follows fails, the account exists and
 * the session does not. That is deliberately not "cleaned up": there is no endpoint to
 * undo a registration, and deleting a just-created account because one request timed out
 * would be far worse than leaving a player to sign in with credentials that now work.
 * The error surfaces on the form, and the sign-in screen is one tap away.
 */
export async function signUp(registration: Registration): Promise<void> {
  await register({
    email: registration.email,
    nickname: registration.nickname,
    password1: registration.password,
    password2: registration.password,
  });

  await signIn({ email: registration.email, password: registration.password });
}
