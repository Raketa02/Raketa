/** **Every sentence the club's details say**, on Club details and inside the sign-up form. */

import { sportName, type SportInUse } from './mappers';

export const DETAILS_COPY = {
  caption: 'How players find your club',
  title: 'Club details',
  name: 'Club name',
  district: 'District',
  city: 'City',
  sports: 'Sports offered',
  pin: 'Where the club is',
  pinHint: 'Click or tap the map where the club is. Drag the pin to move it.',
  pinCentre: 'Put the pin in the middle of the map',
  pinNone: 'No pin yet.',
  pinAt: 'Pin at',
  map: 'Map of where the club is',
  address: 'Address',
  addressHint: 'Type the street and number, then press Enter. You can still move the pin.',
  find: 'Find',
  finding: 'Finding…',
  found: 'Found:',
  save: 'Save',
  saving: 'Saving…',
  saved: 'Club details saved.',
} as const;

/** The refusals, by the backend's codes and the one the website adds (`club_point_missing`). */
export const DETAILS_REFUSALS: Readonly<Record<string, string>> = {
  club_name_invalid: 'A club name is 2 to 80 characters.',
  club_district_invalid: 'A district is 2 to 64 characters.',
  club_city_invalid: 'A city is 2 to 64 characters.',
  club_sports_required: 'Pick at least one sport the club offers.',
  club_point_missing: 'Drop a pin on the map where the club is.',
  club_point_invalid: "That pin isn't on the map. Drop it again where the club is.",
  // Said with the group's name when the backend gave it (sportInUseRefusal).
  club_sport_declared_by_group: 'One of your official groups plays a sport you unticked.',
};

/** The address search's refusals, by the codes `findAddress` answers with. */
export const ADDRESS_REFUSALS: Readonly<Record<string, string>> = {
  place_query_invalid: 'Type at least 3 characters of the address.',
  place_not_found: 'Nothing found for that address. Try adding the city.',
  geocoder_unreachable: "The address search isn't answering. Drop the pin on the map instead.",
};

/**
 * *Ogrody 33 Club plays padel.* (ADR-0182 §5), and the way out that always works. Taking the
 * sport off the group is its administrator's, in the app, and not always possible: a group
 * declares at least one sport, and one that needs an administrator has nobody to do it.
 */
export function sportInUseRefusal({ sport, group }: SportInUse): string {
  const name = sportName(sport).toLowerCase();
  return `${group} plays ${name}. Tick ${name} again to save the rest.`;
}
