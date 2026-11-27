/**
 * **The words sign-in and sign-up say, and the ones their pieces share** — the eyebrow over every
 * auth screen's title, and the labels of the boxes more than one form draws.
 *
 * They were literals in the two screens' JSX until [#515](https://github.com/Raketa02/Raketa/issues/515)
 * took the screens apart into pieces the recovery screens share; a label a piece draws on six
 * screens is copy with six readers, and copy is code. The recovery flow's own words are
 * `resetPresentation`'s.
 */

/**
 * Over the title of every auth screen that keeps today's frame (`AuthFrame`). Uppercased by the
 * eyebrow's style, never by the copy. Sign-in has none: the stage's wordmark replaces it.
 */
export const AUTH_EYEBROW = 'Rakieta';

/**
 * **The stage's wordmark** — the volt dot, then this, in the hero's top-left corner (#784): the
 * mocks' *Rakieta*, read as written (ADR-0211).
 */
export const STAGE_WORDMARK = 'Rakieta';

/** What the stage's email box holds while it is empty — it opens empty, for the keychain's autofill. */
export const EMAIL_PLACEHOLDER = 'you@example.com';

/**
 * **What sign-up's two password boxes hold while they are empty** (#785, mocks 4 and 6). A hint and
 * never the rule: the rule is written under the first box all the time (`PASSWORD_RULE`), and a
 * placeholder goes the moment somebody types.
 */
export const PASSWORD_PLACEHOLDER = 'At least 8 characters';
export const REPEAT_PASSWORD_PLACEHOLDER = 'Once more';

export const EMAIL_LABEL = 'Email';
export const PASSWORD_LABEL = 'Password';
export const REPEAT_PASSWORD_LABEL = 'Repeat password';

export const SIGN_IN_COPY = {
  /** The hero's line, under the deck (#786): it names the gesture the deck is about to show. */
  headline: 'Your next game is only one swipe away.',
  title: 'Sign in',
  submit: 'Sign in',
  submitting: 'Signing in…',
  /** The thin rule between signing in and the other way in. */
  or: 'or',
  newHere: 'New to Rakieta?',
  createAccount: 'Create an account',
} as const;

export const SIGN_UP_COPY = {
  /** The hero's line, under the podium (#788): what the ranking is for, with the newcomer in it. */
  headline: 'Play ranked. The competition starts with you.',
  title: 'Create an account',
  submit: 'Create account',
  submitting: 'Creating account…',
  haveAccount: 'Already have an account?',
  signIn: 'Sign in',
} as const;
