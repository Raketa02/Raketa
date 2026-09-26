/**
 * **The club's details as a form holds them, and the checks a save makes before it leaves.**
 *
 * The checks restate the backend's rules (ADR-0187's accepted cost of independent apps) and
 * refuse with **the backend's own codes**, so one sentence table serves a refusal from either
 * side. One code is the website's alone: `club_point_missing`, for a form with no pin yet, which
 * the backend never sees.
 */

import { formText, type Refusals } from '@/ui/forms';

import { isSport, SPORTS, type Club, type MapPoint, type Sport } from './mappers';

export const DETAILS_FIELDS = ['name', 'district', 'city', 'sports', 'point'] as const;

export type DetailsField = (typeof DETAILS_FIELDS)[number];

/** What the form holds while the desk types: a pin may not have been dropped yet. */
export interface DetailsDraft {
  readonly name: string;
  readonly district: string;
  readonly city: string;
  readonly sports: readonly Sport[];
  readonly point: MapPoint | null;
}

export const EMPTY_DRAFT: DetailsDraft = {
  name: '',
  district: '',
  city: '',
  sports: [],
  point: null,
};

export function draftOf(club: Club): DetailsDraft {
  return { ...club };
}

/** Trimmed, with runs of whitespace collapsed: what the backend records a name as. */
export function tidy(text: string): string {
  return text.trim().replace(/\s+/g, ' ');
}

function coordinate(form: FormData, name: string): number | null {
  const raw = formText(form, name).trim();
  if (raw === '') return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

export function readDetails(form: FormData): DetailsDraft {
  const chosen = new Set(form.getAll('sports').filter(isSport));
  const latitude = coordinate(form, 'latitude');
  const longitude = coordinate(form, 'longitude');
  return {
    name: formText(form, 'name'),
    district: formText(form, 'district'),
    city: formText(form, 'city'),
    sports: SPORTS.filter((sport) => chosen.has(sport)),
    point: latitude === null || longitude === null ? null : { latitude, longitude },
  };
}

/** Whether a name is `min` to `max` characters once tidied, counted as the backend counts them. */
export function between(value: string, min: number, max: number): boolean {
  const length = [...tidy(value)].length;
  return length >= min && length <= max;
}

export function checkDetails(draft: DetailsDraft): Refusals<DetailsField> {
  const refusals: Refusals<DetailsField> = {};
  if (!between(draft.name, 2, 80)) refusals.name = 'club_name_invalid';
  if (!between(draft.district, 2, 64)) refusals.district = 'club_district_invalid';
  if (!between(draft.city, 2, 64)) refusals.city = 'club_city_invalid';
  if (draft.sports.length === 0) refusals.sports = 'club_sports_required';
  if (draft.point === null) refusals.point = 'club_point_missing';
  else if (Math.abs(draft.point.latitude) > 90 || Math.abs(draft.point.longitude) > 180) {
    refusals.point = 'club_point_invalid';
  }
  return refusals;
}

/** A draft that passed {@link checkDetails}, as the details a save sends. */
export function detailsOf(draft: DetailsDraft & { readonly point: MapPoint }): Club {
  return {
    name: tidy(draft.name),
    district: tidy(draft.district),
    city: tidy(draft.city),
    sports: draft.sports,
    point: draft.point,
  };
}
