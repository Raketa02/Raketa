'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import type { Outcome } from '@/server/outcome';
import {
  formId,
  formText,
  hasRefusals,
  placeRefusal,
  type FormState,
  type RefusalAbout,
} from '@/ui/forms';

import { toInvitationBody, toSent, type Sent } from './mappers';
import {
  checkInvitation,
  INVITE_FIELDS,
  invitationOf,
  isAct,
  readInvitation,
  type InviteField,
} from './schemas';

const PAGE = '/administrators';

export interface InviteState extends FormState<InviteField> {
  /** Who the invitation went to, once it went. */
  readonly sent: Sent | null;
}

/**
 * **Send an invitation**: a name and an email, and nothing else (ADR-0184 §2). Somebody already
 * invited or active here is refused under the email, as the backend refuses them.
 */
export async function inviteAdministrator(
  _previous: InviteState,
  form: FormData,
): Promise<InviteState> {
  const draft = readInvitation(form);
  const refusals = checkInvitation(draft);
  if (hasRefusals(refusals)) return { refusals, formRefusal: null, sent: null };

  const outcome = await writeAsClub((api, auth) =>
    api.POST('/api/v1/club/administrators', {
      ...auth,
      body: toInvitationBody(invitationOf(draft)),
    }),
  );
  if (!outcome.ok) {
    // Somebody already here whom the table does not show: it is out of date.
    if (outcome.error.status === 409) revalidatePath(PAGE);
    return { ...placeRefusal(outcome.error, INVITE_FIELDS), sent: null };
  }

  revalidatePath(PAGE);
  return { refusals: {}, formRefusal: null, sent: toSent(outcome.data, 'invitation') };
}

// --- What the club does to a row ----------------------------------------------

export interface ActState {
  /** Who an email just went to, after *Resend invitation* or *Reset password*. */
  readonly sent: Sent | null;
  /** What the backend refused, and about whom. */
  readonly refusal: RefusalAbout | null;
}

/**
 * The table says what the backend holds now. A 404 or a 409 means the row the desk pressed on was
 * out of date (removed, or accepted, elsewhere), so the page is drawn again with the truth; a
 * backend that did not answer leaves the page as it was.
 */
function settleAct<T>(outcome: Outcome<T>, name: string, sent: (data: T) => Sent | null): ActState {
  if (outcome.ok) {
    revalidatePath(PAGE);
    return { sent: sent(outcome.data), refusal: null };
  }
  if (outcome.error.status === 404 || outcome.error.status === 409) revalidatePath(PAGE);
  return { sent: null, refusal: { code: outcome.error.code, name } };
}

/**
 * **Resend invitation**, **Reset password** or a confirmed **Remove**, for one row: which one is
 * the hidden `act`. The form names the row by its id, and by the name the desk saw on it, which a
 * refusal is said about.
 */
export async function actOnAdministrator(_previous: ActState, form: FormData): Promise<ActState> {
  const act = formText(form, 'act');
  const id = formId(form, 'id');
  const name = formText(form, 'name');
  if (!isAct(act)) return { sent: null, refusal: { code: 'request_invalid', name } };
  if (id === null) {
    return { sent: null, refusal: { code: 'administrator_not_found', name } };
  }
  const path = { params: { path: { administrator_id: id } } };

  switch (act) {
    case 'resend':
      return settleAct(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/administrators/{administrator_id}/invitation', {
            ...auth,
            ...path,
          }),
        ),
        name,
        (data) => toSent(data, 'invitation'),
      );
    case 'reset':
      return settleAct(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/administrators/{administrator_id}/password-reset', {
            ...auth,
            ...path,
          }),
        ),
        name,
        (data) => toSent(data, 'reset'),
      );
    case 'remove':
      return settleAct(
        await writeAsClub((api, auth) =>
          api.DELETE('/api/v1/club/administrators/{administrator_id}', { ...auth, ...path }),
        ),
        name,
        () => null,
      );
  }
}
