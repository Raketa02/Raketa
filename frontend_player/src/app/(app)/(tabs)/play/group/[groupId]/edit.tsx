import { Redirect, useLocalSearchParams } from 'expo-router';

import { EditGroupScreen, parseGroupRouteParams } from '@/features/groups/types';

/**
 * **Edit group** — pushed over the group's page from Info's Edit group row, so *back* is the page.
 *
 * An id that does not survive the schema has no group behind it and goes to Play, as the page's
 * own route sends it.
 */
export default function GroupEditRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <EditGroupScreen groupId={parsed.groupId} />;
}
