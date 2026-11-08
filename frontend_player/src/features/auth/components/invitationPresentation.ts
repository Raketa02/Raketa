/**
 * **Every sentence an invited person's way in says** — *Have an invitation code?* and *Set your
 * password* ([#518](https://github.com/Raketa02/Raketa/issues/518), PRD #500 stories 113–116 and
 * 121, [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §2–§4) — the two screens' words and the refusals, keyed by the wire's code.
 *
 * **Expired, used and locked each have their own sentence, and the expired one says who to ask.**
 * *Forgot password?*'s answer to an expired code is *ask again*, because the person can; an
 * invitation is the club's to send, so it is *ask the club to send a new one* (story 115).
 */

import type { AppError } from '@/shared/errors';

import type { InvitationVia } from '../domain/invitation';
import type { InvitationLinkState } from '../domain/vocabulary';

import { authErrorMessage } from './authErrorMessage';

export const INVITATION_COPY = {
  /**
   * Under the Sign in button's *or* rule, on the one sign-in screen everyone shares — a statement
   * on a button since the stage (#784), where it was a question on a text link. The screen it
   * opens keeps its question for a title.
   */
  signInLink: 'I have an invitation code',
  code: {
    title: 'Have an invitation code?',
    lead: 'Type the email the club invited and the 8-character code from its email.',
    label: 'Code',
    continue: 'Continue',
    checking: 'Checking…',
  },
  password: {
    title: 'Set your password',
    lead: "It's the one you'll sign in with, on this phone and any other.",
    label: 'Password',
    set: 'Set password',
    setting: 'Setting password…',
    /** Back to the code screen, whose boxes still hold what was typed — a claim is not a use. */
    enterCodeAgain: 'Enter the code again',
  },
  backToSignIn: 'Back to sign in',
  /** Under a link that could not be read — the connection, not the link. */
  tryAgain: 'Try again',
} as const;

/** The sentence for an email that is somebody's account already — accepting is done signed in. */
const SIGN_IN_TO_ACCEPT = 'This email already has an account — sign in to accept.';

/**
 * **What a link that no longer works says** — whether the read before anything is set finds it
 * spent, or the set is refused because it is: one sentence per state, whichever read says so.
 */
export const LINK_STATE_MESSAGE: Readonly<Record<Exclude<InvitationLinkState, 'valid'>, string>> = {
  expired: 'That link has expired. Ask the club to send a new one.',
  used: 'That link has already been used. Sign in with the password you set.',
  locked:
    'Too many wrong codes were typed for that invitation, so its link is locked too. Ask the club to send a new one.',
};

/**
 * **The refusals, by how the person got here** — typing the code, or tapping the email's link.
 * *That invitation* and *that link* are different things to a person holding one, though the server
 * spends both together. A wrong code never reaches a link — it is `code_incorrect`, under the code
 * box, in the auth-wide table — and `credential_not_found` is a link's or a ticket's.
 */
const REFUSALS: Readonly<Record<InvitationVia, Readonly<Record<string, string>>>> = {
  code: {
    credential_expired: 'That invitation has expired. Ask the club to send a new one.',
    credential_used: 'That invitation has already been used. Sign in with the password you set.',
    credential_locked:
      'Too many wrong codes were typed, so that invitation is locked. Ask the club to send a new one.',
    sign_in_to_accept: SIGN_IN_TO_ACCEPT,
    // The ticket a right code bought lasts a few minutes, and a claim is not a use: the same code
    // buys another.
    ticket_expired: 'That took too long. Enter the code again.',
    credential_not_found: 'That invitation has stopped working. Ask the club to send a new one.',
  },
  link: {
    credential_expired: LINK_STATE_MESSAGE.expired,
    credential_used: LINK_STATE_MESSAGE.used,
    credential_locked: LINK_STATE_MESSAGE.locked,
    sign_in_to_accept: SIGN_IN_TO_ACCEPT,
    credential_not_found: "That link isn't one we sent. Ask the club to send a new one.",
  },
};

/**
 * A refusal on the invitation's screens: the way in's own sentence, else the auth-wide table — which
 * holds the two that land under a box, `code_incorrect` and `password_too_weak` — else the
 * recovery category's.
 */
export function invitationErrorMessage(via: InvitationVia): (error: AppError) => string {
  return (error) => {
    const own = error.code === undefined ? undefined : REFUSALS[via][error.code];
    return own ?? authErrorMessage(error);
  };
}

/** Refusals that mean the invitation itself is spent, or is not the way in — so the code is no help. */
const SPENT: ReadonlySet<string> = new Set([
  'credential_expired',
  'credential_used',
  'credential_locked',
  'credential_not_found',
  'sign_in_to_accept',
]);

/**
 * **Where the way out of *Set your password* goes, and it follows the refusal** — `resetWayOut`'s
 * rule. By a code, back to the code screen while the code can still buy a ticket; by a link, or once
 * a refusal says the invitation is spent, back to sign in — where an account that already exists
 * accepts, and whoever asks the club for a new invitation comes back.
 */
export function invitationWayOut(via: InvitationVia, error: AppError | null): 'code' | 'sign-in' {
  if (via === 'link') return 'sign-in';
  return error?.code !== undefined && SPENT.has(error.code) ? 'sign-in' : 'code';
}
