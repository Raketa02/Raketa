/**
 * **The words sign-in and sign-up say, and the ones their pieces share** — the eyebrow over every
 * auth screen's title, and the labels of the boxes more than one form draws.
 *
 * They were literals in the two screens' JSX until [#515](https://github.com/Raketa02/Raketa/issues/515)
 * took the screens apart into pieces the recovery screens share; a label a piece draws on six
 * screens is copy with six readers, and copy is code. The recovery flow's own words are
 * `resetPresentation`'s.
 */

/** Over every auth screen's title. Uppercased by the eyebrow's style, never by the copy. */
export const AUTH_EYEBROW = 'Raketa';

export const EMAIL_LABEL = 'Email';
export const PASSWORD_LABEL = 'Password';
export const REPEAT_PASSWORD_LABEL = 'Repeat password';

export const SIGN_IN_COPY = {
  title: 'Sign in',
  submit: 'Sign in',
  submitting: 'Signing in…',
  newHere: 'New to Raketa?',
  createAccount: 'Create an account',
} as const;

export const SIGN_UP_COPY = {
  title: 'Create an account',
  submit: 'Create account',
  submitting: 'Creating account…',
  haveAccount: 'Already have an account?',
  signIn: 'Sign in',
} as const;
