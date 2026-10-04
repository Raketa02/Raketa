/**
 * **Where the recovery screens live**, spelled once. The route files under `src/app/(auth)/` are
 * what make them routes; this is what the screens push to, and what the links ticket (#520)
 * reads to open *Set a new password* from an email's `reset/<token>`.
 *
 * Under `(auth)`, beside sign-in, because they are for somebody who is not signed in: the group's
 * guard sends a session that has begun — the one *Set a new password* begins — to the entry gate.
 */
export const RESET_ROUTES = {
  ask: '/forgot-password',
  sent: '/forgot-password/sent',
  code: '/forgot-password/code',
  newPassword: '/forgot-password/new-password',
  link: '/reset/[token]',
} as const;

/**
 * The email form, opened with an address already in its box — from under the Sign in button, and
 * from every *Ask again*. Trimmed, because a stray space is a typo and not part of an address.
 */
export function askForResetHref(email: string) {
  return { pathname: RESET_ROUTES.ask, params: { email: email.trim() } } as const;
}
