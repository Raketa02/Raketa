/**
 * **Every sentence the signed-out pages say**, and the refusals, keyed by code.
 *
 * The words follow the player app's where the two do the same thing (the password rule, a wrong
 * code), so a person who uses both reads one voice. Nothing is imported from it: the apps share
 * no code (ADR-0005), and this copy is this app's own.
 */

import { DETAILS_REFUSALS } from '@/features/club-details/copy';

export const PASSWORD_RULE = 'Use 8 to 128 characters, with at least one letter and one digit.';

export const SIGN_IN_COPY = {
  title: 'Sign in',
  email: 'Club email',
  password: 'Password',
  submit: 'Sign in',
  submitting: 'Signing in…',
  forgot: 'Forgot password?',
  newClub: 'New club?',
  signUp: 'Sign up',
  /** The notice over the form, by `?session=` or `?signed-up=`. */
  notices: {
    ended: "You've been signed out. Sign in again to carry on.",
    unreachable: "We couldn't reach the server to keep you signed in. Try again in a moment.",
    'signed-up': 'Your club is signed up. Sign in with its email and password.',
  },
} as const;

export type SignInNotice = keyof typeof SIGN_IN_COPY.notices;

/** The notice a sign-in page was sent with, if it is one this page says. */
export function signInNotice(session: unknown, signedUp: unknown): SignInNotice | null {
  if (session === 'ended' || session === 'unreachable') return session;
  return signedUp === '1' ? 'signed-up' : null;
}

export const SIGN_UP_COPY = {
  title: 'Sign up your club',
  lead: 'Players find your club by these details. You can change them later in Club details.',
  email: 'Club email',
  emailHint: 'The desk signs in with this email.',
  password: 'Password',
  submit: 'Sign up',
  submitting: 'Signing up…',
  haveAccount: 'Already signed up?',
  signIn: 'Sign in',
} as const;

export const SIGN_OUT_COPY = { submit: 'Sign out' } as const;

export const RESET_COPY = {
  backToSignIn: 'Back to sign in',
  ask: {
    title: 'Forgot password?',
    lead: "Type the club's email. We'll send it a link and an 8-character code.",
    email: 'Club email',
    send: 'Send',
    sending: 'Sending…',
  },
  sent: {
    title: 'Check your email',
    lead: (email: string) =>
      `If a club signs in with ${email}, we've sent it a link and an 8-character code. ` +
      'Both work for one hour, once.',
    enterCode: 'Enter the code',
  },
  code: {
    title: 'Enter the code',
    lead: "Type the club's email and the 8-character code we sent to it.",
    email: 'Club email',
    code: 'Code',
    submit: 'Continue',
    submitting: 'Checking…',
    noEmail: 'No email?',
    askAgain: 'Ask again',
  },
  newPassword: {
    title: 'Set a new password',
    lead: "You'll be signed in here, and signed out in every other browser.",
    password: 'New password',
    submit: 'Set password',
    submitting: 'Setting password…',
    enterCodeAgain: 'Enter the code again',
    linkTrouble: 'Link not working?',
    askAgain: 'Ask again',
  },
  /** On Overview, where setting one lands the club. */
  done: 'New password set. Any other browser signed in as the club is signed out.',
} as const;

/** The refusals any signed-out form can meet under its boxes, or over it. */
export const AUTH_REFUSALS: Readonly<Record<string, string>> = {
  email_required: "Type the club's email.",
  email_invalid: "That doesn't look like an email address.",
  password_required: 'Type the password.',
  password_too_weak: PASSWORD_RULE,
  invalid_credentials: "That email and password don't match. Try again.",
  account_disabled: 'This club account has been switched off.',
  club_email_already_registered: 'Another club already signs in with this email.',
  code_required: 'Type the code from the email.',
  code_wrong_length: 'The code is 8 characters.',
  code_incorrect: "That isn't the code we sent to that email. Check it and type it again.",
};

export const SIGN_UP_REFUSALS: Readonly<Record<string, string>> = {
  ...DETAILS_REFUSALS,
  ...AUTH_REFUSALS,
};

/** How the person reached *Set a new password*: typing the email's code, or tapping its link. */
export type ResetVia = 'code' | 'link';

/**
 * **The recovery's refusals, worded by the way in**: *that code* and *that link* are different
 * things to someone holding one, though the backend spends both together. Expired says to ask
 * again.
 */
export const RESET_REFUSALS: Readonly<Record<ResetVia, Readonly<Record<string, string>>>> = {
  code: {
    ...AUTH_REFUSALS,
    credential_expired: 'That code has expired. Ask again for a new one.',
    credential_used:
      'That code has already been used. Sign in with the new password, or ask again for a new one.',
    credential_locked:
      'Too many wrong codes were typed, so that one is locked. Ask again for a new one.',
    ticket_expired: 'That took too long. Enter the code again.',
    credential_not_found: 'That code has stopped working. Ask again for a new one.',
    ticket_missing: 'Enter the code from the email first.',
  },
  link: {
    ...AUTH_REFUSALS,
    credential_expired: 'That link has expired. Ask again for a new one.',
    credential_used:
      'That link has already been used. Sign in with the new password, or ask again for a new one.',
    credential_locked:
      'Too many wrong codes were typed for that email, so its link is locked too. Ask again for a new one.',
    credential_not_found: "That link isn't one we sent. Ask again for a new one.",
  },
};

/** Refusals that mean the email is spent, its link and its code both: only a new one helps. */
const SPENT: ReadonlySet<string> = new Set([
  'credential_expired',
  'credential_used',
  'credential_locked',
  'credential_not_found',
]);

/**
 * **Where the way out of a refusal goes.** By a code, back to the code while it can still buy a
 * ticket, and *Ask again* once the email is spent. By a link, always *Ask again*.
 */
export function isSpent(code: string | null): boolean {
  return code !== null && SPENT.has(code);
}

export function resetWayOut(via: ResetVia, code: string | null): 'code' | 'ask' {
  return via === 'link' || isSpent(code) ? 'ask' : 'code';
}
