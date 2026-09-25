'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import { hasRefusals, placeRefusal, type FormState } from '@/ui/forms';

import { toClub, toDetailsBody, type Club } from './mappers';
import { checkDetails, DETAILS_FIELDS, detailsOf, readDetails, type DetailsField } from './schemas';

export interface DetailsFormState extends FormState<DetailsField> {
  /** The details as the backend recorded them, after a save that landed. */
  readonly saved: Club | null;
}

/**
 * **Save Club details**: all five, as a full replacement. The frame re-renders afterwards, so the
 * top bar says the new name and place at once.
 */
export async function saveClubDetails(
  _previous: DetailsFormState,
  form: FormData,
): Promise<DetailsFormState> {
  const draft = readDetails(form);
  const refusals = checkDetails(draft);
  if (hasRefusals(refusals) || draft.point === null) {
    return { refusals, formRefusal: null, saved: null };
  }

  const details = detailsOf({ ...draft, point: draft.point });
  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/details', { ...auth, body: toDetailsBody(details) }),
  );
  if (!outcome.ok) return { ...placeRefusal(outcome.error, DETAILS_FIELDS), saved: null };

  revalidatePath('/', 'layout');
  return { refusals: {}, formRefusal: null, saved: toClub(outcome.data) };
}
