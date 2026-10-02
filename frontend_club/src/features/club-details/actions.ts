'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import { hasRefusals, placeRefusal, type FormState } from '@/ui/forms';

import { toClub, toDetailsBody, toSportInUse, type Club, type SportInUse } from './mappers';
import { checkDetails, DETAILS_FIELDS, detailsOf, readDetails, type DetailsField } from './schemas';

export interface DetailsFormState extends FormState<DetailsField> {
  /** The details as the backend recorded them, after a save that landed. */
  readonly saved: Club | null;
  /** The court or the group that plays a sport the save unticked, when that is why it was refused. */
  readonly sportInUse: SportInUse | null;
}

/**
 * **Save Club details**: all five, as a full replacement. The frame re-renders afterwards, so the
 * top bar says the new name and place at once. Unticking a sport one of the club's courts or an
 * official group plays is refused under the sports, naming the court or the group.
 */
export async function saveClubDetails(
  _previous: DetailsFormState,
  form: FormData,
): Promise<DetailsFormState> {
  const draft = readDetails(form);
  const refusals = checkDetails(draft);
  if (hasRefusals(refusals) || draft.point === null) {
    return { refusals, formRefusal: null, saved: null, sportInUse: null };
  }

  const details = detailsOf({ ...draft, point: draft.point });
  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/details', { ...auth, body: toDetailsBody(details) }),
  );
  if (!outcome.ok) {
    return {
      ...placeRefusal(outcome.error, DETAILS_FIELDS),
      saved: null,
      sportInUse: toSportInUse(outcome.error),
    };
  }

  revalidatePath('/', 'layout');
  return { refusals: {}, formRefusal: null, saved: toClub(outcome.data), sportInUse: null };
}
