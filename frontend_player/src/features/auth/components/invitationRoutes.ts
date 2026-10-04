/**
 * **Where an invited person's way in lives**, spelled once — `RESET_ROUTES`' reason. The route files
 * under `src/app/(auth)/` make them routes; this is what the screens push to, and what the links
 * ticket ([#520](https://github.com/Raketa02/Raketa/issues/520)) reads to open *Set your password*
 * from an email's `invite/<token>`.
 *
 * Under `(auth)`, beside sign-in and *Forgot password?*, because they are for somebody who is not
 * signed in: the group's guard hands the session *Set your password* begins to the entry gate.
 */
export const INVITATION_ROUTES = {
  /** *Have an invitation code?* — the email and the code. */
  code: '/invitation',
  /** *Set your password* by the ticket a right code bought. */
  password: '/invitation/password',
  /** *Set your password* by the email's link — the path its button names. */
  link: '/invite/[token]',
} as const;

/** The code form, opened with the address already typed under Sign in. */
export function invitationCodeHref(email: string) {
  return { pathname: INVITATION_ROUTES.code, params: { email: email.trim() } } as const;
}
