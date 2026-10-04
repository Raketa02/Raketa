import { Redirect, useLocalSearchParams } from 'expo-router';

import { GroupSettingsScreen, parseOfficialGroupRouteParams } from '@/features/administrator/types';

/**
 * **An official group's settings** — pushed over the You tab from the group's row, so *back* is
 * the tab. A param that does not survive the schema has no group behind it, and the honest place
 * to say so is where the gate sends the person.
 */
export default function GroupSettingsRoute() {
  const parsed = parseOfficialGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <GroupSettingsScreen clubId={parsed.clubId} groupId={parsed.groupId} />;
}
