/** **Every sentence the club's details say**, on Club details and inside the sign-up form. */

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
};
