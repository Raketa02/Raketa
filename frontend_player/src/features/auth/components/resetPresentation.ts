/**
 * **Every sentence *Forgot password?* says** ([#515](https://github.com/Raketa02/Raketa/issues/515),
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §5) — the five screens' words and the refusals, keyed by the wire's code.
 *
 * **The confirmation is one sentence for everybody.** The server answers `202` whether or not the
 * address has an account, and whether or not the throttle let an email go; this screen says the
 * same thing in every case, so nothing a person reads tells them who uses Rakieta.
 */

import type { AppError } from '@/shared/errors';

import type { ResetVia } from '../domain/passwordReset';

import { authErrorMessage } from './authErrorMessage';

export const RESET_COPY = {
  /** Under the Sign in button, on the one sign-in screen players and administrators share. */
  signInLink: 'Forgot password?',
  backToSignIn: 'Back to sign in',
  ask: {
    title: 'Forgot password?',
    lead: "Type the email you sign in with. We'll send it a link and an 8-character code.",
    send: 'Send',
    sending: 'Sending…',
  },
  sent: {
    title: 'Check your email',
    lead: (email: string) =>
      `If ${email} has a Rakieta account, we've sent it a link and an 8-character code. ` +
      'Both work for one hour, once.',
    enterCode: 'Enter the code',
  },
  code: {
    title: 'Enter the code',
    lead: 'Type the email you asked with and the 8-character code we sent to it.',
    label: 'Code',
    continue: 'Continue',
    checking: 'Checking…',
    noEmail: 'No email?',
    askAgain: 'Ask again',
  },
  newPassword: {
    title: 'Set a new password',
    lead: "You'll be signed in here, and signed out on every other phone.",
    label: 'New password',
    set: 'Set password',
    setting: 'Setting password…',
    /** Back to the code screen, whose boxes still hold what was typed — a claim is not a use. */
    enterCodeAgain: 'Enter the code again',
    linkTrouble: 'Link not working?',
    askAgain: 'Ask again',
  },
  /** The toast over wherever the gate lands a person who has just set one. */
  done: 'New password set. Any other phone is signed out.',
} as const;

/**
 * **The refusals, by how the person got here** — typing the code, or tapping the email's link.
 *
 * Each of expired, used and locked has its own sentence, and **expired says to ask again**. They
 * are worded per way in because *that code* and *that link* are different things to a person
 * holding one, even though the server spends both together. A code the server has never heard of
 * never reaches a person typing one — a wrong code is `code_incorrect`, under the box — so
 * `credential_not_found` is the link's and the ticket's alone.
 */
const REFUSALS: Readonly<Record<ResetVia, Readonly<Record<string, string>>>> = {
  code: {
    credential_expired: 'That code has expired. Ask again for a new one.',
    credential_used:
      'That code has already been used. Sign in with your new password, or ask again for a new one.',
    credential_locked:
      'Too many wrong codes were typed, so that one is locked. Ask again for a new one.',
    // The ticket a right code bought lasts fifteen minutes, and a claim is not a use: the same code
    // buys another.
    ticket_expired: 'That took too long. Enter the code again.',
    credential_not_found: 'That code has stopped working. Ask again for a new one.',
  },
  link: {
    credential_expired: 'That link has expired. Ask again for a new one.',
    credential_used:
      'That link has already been used. Sign in with your new password, or ask again for a new one.',
    credential_locked:
      'Too many wrong codes were typed for that email, so its link is locked too. Ask again for a new one.',
    credential_not_found: "That link isn't one we sent. Ask again for a new one.",
  },
};

/**
 * A refusal on the recovery screens: the way in's own sentence, else the auth-wide table — which
 * holds the two that land under a box, `code_incorrect` and `password_too_weak` — else the
 * recovery category's.
 */
export function resetErrorMessage(via: ResetVia): (error: AppError) => string {
  return (error) => {
    const own = error.code === undefined ? undefined : REFUSALS[via][error.code];
    return own ?? authErrorMessage(error);
  };
}

/**
 * Refusals that mean the email itself is spent — its link and code both — so the only way on is a
 * new one.
 */
const SPENT: ReadonlySet<string> = new Set([
  'credential_expired',
  'credential_used',
  'credential_locked',
  'credential_not_found',
]);

/**
 * **Where the way out of *Set a new password* goes, and it follows the refusal.** By a code, it is
 * back to the code screen while the code can still buy a ticket — nothing has gone wrong yet, or
 * the ticket ran out — and *Ask again* once the email is spent, because going back would only meet
 * the same refusal one screen earlier. By a link, it is always *Ask again*: nothing is under it.
 */
export function resetWayOut(via: ResetVia, error: AppError | null): 'code' | 'ask' {
  if (via === 'link') return 'ask';
  return error?.code !== undefined && SPENT.has(error.code) ? 'ask' : 'code';
}
