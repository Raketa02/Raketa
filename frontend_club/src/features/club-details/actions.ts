'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import { geocode } from '@/server/geocoder';
import { hasRefusals, placeRefusal, type FormState } from '@/ui/forms';

import {
  toClub,
  toDetailsBody,
  toSportInUse,
  type Club,
  type MapPoint,
  type SportInUse,
} from './mappers';
import {
  addressQuery,
  checkDetails,
  DETAILS_FIELDS,
  detailsOf,
  readDetails,
  type DetailsField,
} from './schemas';

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

/** What the address search answers the map with: the place, or the code the box says. */
export type AddressSearch =
  | { readonly found: true; readonly point: MapPoint; readonly name: string }
  | {
      readonly found: false;
      readonly code: 'place_query_invalid' | 'place_not_found' | 'geocoder_unreachable';
    };

/**
 * **Find the club by its address**: the best match for what the desk typed over the map, for the
 * map to put the pin on. Sign-up and Club details both ask, so it needs no session, and it sends
 * nothing to the backend: the pin is still only saved with the form. The query is checked again
 * here, because an action is a public endpoint whatever the form in front of it checked.
 */
export async function findAddress(raw: string): Promise<AddressSearch> {
  const query = typeof raw === 'string' ? addressQuery(raw) : null;
  if (query === null) return { found: false, code: 'place_query_invalid' };
  const outcome = await geocode(query);
  return outcome.ok
    ? { found: true, point: outcome.place.point, name: outcome.place.name }
    : { found: false, code: outcome.code };
}
