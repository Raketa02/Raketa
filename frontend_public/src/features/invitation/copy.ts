import type { PasswordFormWords } from '@/features/set-password/copy';
import type { LinkState } from '@/features/set-password/mappers';

/**
 * **The invitation page's words.** They follow the app's *Set your password* where the two say the
 * same thing, by copying it (`frontend_player`'s `invitationPresentation.ts`), and send the person
 * to *the app* where the web can't do what is needed. **Rakieta is named only in the two
 * sentences ADR-0187 names it in** (§4's *after you install, open Rakieta and enter this code*,
 * and §8's *Open Rakieta and sign in with your email and password*, which ADR-0211 respells
 * *Rakieta*); everywhere else the copy rule stands.
 */

export const INVITATION_COPY = {
  title: 'Your invitation',
  /** The code the email carries, set out for typing into the app. */
  code: 'Your code',
  next: 'After you install, open Rakieta and enter this code',
  /** Once the password is set here (#500 story 112). */
  done: 'Password set. Open Rakieta and sign in with your email and password.',
} as const;

export const INVITATION_FORM: PasswordFormWords = {
  title: 'Set your password here',
  lead: "It's the one you'll sign in with, on any phone.",
  password: 'Password',
  repeat: 'Repeat password',
  submit: 'Set password',
  submitting: 'Setting password…',
};

/**
 * **What a link that no longer works says**, one sentence per state, and the expired one says who
 * to ask: an invitation is the club's to send (#500 story 115).
 */
export const INVITATION_STATES: Readonly<Record<Exclude<LinkState, 'valid'>, string>> = {
  expired: 'That link has expired. Ask the club to send a new one.',
  used: 'That link has already been used. Sign in to the app with the password you set.',
  locked:
    'Too many wrong codes were typed for that invitation, so its link is locked too. Ask the club to send a new one.',
};

/** The form's own refusal, beside the password rule's. */
export const INVITATION_REFUSALS: Readonly<Record<string, string>> = {
  sign_in_to_accept:
    'This email already has an account. Sign in to the app with it, and accept the invitation there.',
  credential_not_found: "That link isn't one we sent. Ask the club to send a new one.",
};

/**
 * *Hi Marta Wójcik — Ogrody 33 wants you as an administrator*: **the whole name** the club typed,
 * since nothing invents a first name (ADR-0171 §4).
 */
export function greeting(name: string, club: string): string {
  return `Hi ${name} — ${club} wants you as an administrator`;
}
