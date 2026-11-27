/** **Every sentence the Administrators page says** (club mocks 2–4 and 14). */

import { sentenceAbout, type RefusalAbout } from '@/ui/forms';

export const ADMINISTRATORS_COPY = {
  caption: 'People who run your groups in the app',
  add: '+ Add administrator',
  form: {
    name: 'Name',
    namePlaceholder: 'Full name',
    email: 'Email',
    emailPlaceholder: 'name@example.com',
    cancel: 'Cancel',
    send: 'Send invitation',
    sending: 'Sending…',
    explain:
      'Rakieta emails them. They set their own password in the app; if the email already has a ' +
      'Rakieta account, they just accept.',
  },
  sent: {
    // No line under the name: the email says what to do, and which email went out — a password
    // and a code, or an accept in the app — is the backend's to decide (#529 I2).
    invitation: {
      kicker: 'Invitation sent · valid 72 hours',
    },
    reset: {
      kicker: 'Password reset · new invitation valid 72 hours',
      lead:
        "Their password is cleared and they're signed out everywhere. Rakieta emailed them a " +
        'button that opens the app, and a code that works in the app if the button does not. ' +
        'They set a new password there.',
    },
    done: 'Done',
  },
  columns: {
    name: 'Administrator',
    email: 'Email',
    groups: 'Groups',
    status: 'Status',
    actions: 'Actions',
  },
  noGroups: 'none yet',
  groupCount: (count: number) => (count === 1 ? '1 group' : `${count} groups`),
  status: { active: 'active', invited: 'invited', expired: 'expired' },
  expiresIn: (days: number) => `expires in ${days} d`,
  expiredAgo: (days: number) => `${days} d ago`,
  resetPassword: 'Reset password',
  resend: 'Resend invitation',
  remove: 'Remove',
  confirmRemove: {
    title: (name: string) => `Remove ${name}?`,
    lead:
      'They stop being one of your administrators at once, and an invitation they have not ' +
      'taken up stops working. Rakieta emails them to say so. Their groups stay, marked needs ' +
      'an administrator, until you hand them over. If they also play, nothing changes for ' +
      'their player profile.',
    cancel: 'Cancel',
    remove: 'Remove',
  },
} as const;

/** The refusals an invitation can meet, by the backend's codes and the website's own. */
export const INVITE_REFUSALS: Readonly<Record<string, string>> = {
  administrator_name_invalid: 'A name is 2 to 64 characters.',
  email_required: 'Type their email.',
  email_invalid: "That doesn't look like an email address.",
  administrator_already_invited:
    'They already have an invitation from your club. Resend it from the table instead.',
  administrator_already_active: 'They are already one of your administrators.',
};

/** The refusals an act on a row can meet, said about the person it was on. */
const ACT_REFUSALS: Readonly<Record<string, (name: string) => string>> = {
  administrator_not_found: (name) => `${name} isn't one of your administrators any more.`,
  administrator_already_active: (name) =>
    `${name} has already accepted, so there is no invitation to send again.`,
  administrator_also_plays: (name) =>
    `${name} also plays on Rakieta, so only they can reset their password, with Forgot ` +
    'password? in the app.',
  administrator_has_no_account: (name) =>
    `${name} hasn't set a password yet, so there is none to reset. Resend the invitation instead.`,
};

/** The sentence for an act's refusal: about the person, or one every form can meet. */
export function actRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, ACT_REFUSALS);
}

/**
 * **When the administrator profile was last used**, as the desk reads it: *today*, *this week*,
 * then weeks, months, and a year. The backend keeps it to the hour (ADR-0184 §1), so nothing
 * finer is said.
 */
export function lastUsed(idleDays: number): string {
  if (idleDays < 1) return 'today';
  if (idleDays < 7) return 'this week';
  if (idleDays < 35) {
    const weeks = Math.floor(idleDays / 7);
    return weeks === 1 ? 'a week ago' : `${weeks} weeks ago`;
  }
  if (idleDays < 365) {
    const months = Math.floor(idleDays / 30);
    return months === 1 ? 'a month ago' : `${months} months ago`;
  }
  return 'over a year ago';
}
