/**
 * **An invitation as the form holds it, and the checks it makes before it leaves.** They restate
 * the backend's rules and refuse with its codes (ADR-0187's accepted cost of independent apps),
 * so *Send invitation* stays disabled exactly while the backend would refuse, and one sentence
 * table serves a refusal from either side. The website adds `email_required`.
 */

import { between, tidy } from '@/features/club-details/schemas';
import { checkEmail } from '@/features/sign-in/schemas';
import { formText, type Refusals } from '@/ui/forms';

export const INVITE_FIELDS = ['name', 'email'] as const;

export type InviteField = (typeof INVITE_FIELDS)[number];

export interface Invitation {
  readonly name: string;
  readonly email: string;
}

export const EMPTY_INVITATION: Invitation = { name: '', email: '' };

export function readInvitation(form: FormData): Invitation {
  return { name: formText(form, 'name'), email: formText(form, 'email') };
}

export function checkInvitation(draft: Invitation): Refusals<InviteField> {
  const refusals: Refusals<InviteField> = {};
  if (!between(draft.name, 2, 64)) refusals.name = 'administrator_name_invalid';
  const emailRefusal = checkEmail(draft.email);
  if (emailRefusal !== null) refusals.email = emailRefusal;
  return refusals;
}

/** A draft that passed {@link checkInvitation}, as the invitation sends it. */
export function invitationOf(draft: Invitation): Invitation {
  return { name: tidy(draft.name), email: draft.email.trim() };
}

/** What the club does to a row: *Resend invitation*, *Reset password*, a confirmed *Remove*. */
export const ACTS = ['resend', 'reset', 'remove'] as const;

export type Act = (typeof ACTS)[number];

export function isAct(value: string): value is Act {
  return (ACTS as readonly string[]).includes(value);
}
