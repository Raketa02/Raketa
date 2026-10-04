import { Redirect, useLocalSearchParams } from 'expo-router';

import { OfficialGroupScreen, parseOfficialGroupRouteParams } from '@/features/administrator/types';

/**
 * **An official group's page** — pushed over the Groups tab, or replacing New official group once
 * the group exists, so *back* is the list either way. A param that does not survive the schema has
 * no group behind it, and the honest place to say so is where the gate sends the person.
 */
export default function OfficialGroupRoute() {
  const parsed = parseOfficialGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <OfficialGroupScreen clubId={parsed.clubId} groupId={parsed.groupId} />;
}
