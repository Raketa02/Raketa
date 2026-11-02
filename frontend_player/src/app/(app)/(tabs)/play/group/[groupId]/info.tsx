import { Redirect, useLocalSearchParams } from 'expo-router';

import { GroupInfoScreen, parseGroupRouteParams } from '@/features/groups/types';

/**
 * **Info**, the group's own screen — pushed over the group's page from its header (Q125), so *back*
 * is the page, on the tab the player left.
 *
 * An id that does not survive the schema has no group behind it and goes to Play, as the page's
 * own route sends it.
 */
export default function GroupInfoRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <GroupInfoScreen groupId={parsed.groupId} />;
}
