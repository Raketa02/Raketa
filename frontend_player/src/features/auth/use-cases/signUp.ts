/**
 * Create an account and sign in with it.
 *
 * Two requests, one workflow — which is exactly why it is a use-case and not an `api/`
 * function. `POST /api/v1/users` returns the created user, not a token pair, so an app
 * that stopped there would leave a new player looking at a sign-in form and wondering
 * whether their account exists.
 *
 * **Credentials only.** Nothing about who the player is travels here: the account is created
 * unnamed, and the naming is onboarding's first step
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §2), which the entry gate sends the new session straight into.
 */

import { register } from '../api/authApi';
import type { Registration } from '../domain/AuthenticatedUser';

import { signIn } from './signIn';

/**
 * The password is sent twice because the backend asks for both halves and checks them
 * server-side. The form checks the match too, so the player is told before a round trip
 * — but the server's copy of the rule is the one that counts. The **adult attestation**
 * travels the same way and for the same reason: the box refuses locally, and
 * `adult_attestation_required` is the server refusing a body this app would not have sent
 * ([ADR-0124](../../../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
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
    password1: registration.password,
    password2: registration.password,
    // Sent as the player gave it. Nothing here coerces it to `true`: a caller that could
    // pass `false` and have it corrected would be a second place the attestation is
    // decided, and the whole point is that only the player decides it.
    adult_attested: registration.adultAttested,
  });

  await signIn({ email: registration.email, password: registration.password });
}
