/**
 * Sign in: credentials -> a live session.
 *
 * The whole workflow, in one function, so that "what does signing in actually do" has a
 * single answer that a test can drive without a renderer.
 */

import { beginSession } from '@/shared/lib/auth';

import { login } from '../api/authApi';
import type { SignInCredentials } from '../domain/AuthenticatedUser';
import { toTokens } from '../mappers/authMappers';

/**
 * The order is load-bearing. `beginSession` persists the pair *before* flipping the
 * status, so the authenticated tree never renders against a token manager that has not
 * been told about the credentials yet — and runs `readAccount` between the two, so the
 * account is read while the form and its busy button are still on screen, and the entry
 * gate finds it cached rather than drawing nothing while it asks
 * (`docs/specs/busy-indicator/decisions.md` §3.1). The read is handed in: it is the cache's,
 * and a use-case knows no query client.
 *
 * Nothing is caught here. A wrong password arrives as an `AppError` whose recovery is
 * `requires-user-correction`, and the screen renders it against the form — swallowing it
 * into a boolean would throw away the only thing that distinguishes it from a server
 * being down.
 */
export async function signIn(
  credentials: SignInCredentials,
  readAccount: () => Promise<unknown>,
): Promise<void> {
  const wire = await login({
    email: credentials.email,
    password: credentials.password,
  });

  await beginSession(toTokens(wire), readAccount);
}
