import { Redirect, useLocalSearchParams } from 'expo-router';

import { MembersScreen, parseGroupRouteParams } from '@/features/groups/types';

/**
 * **Members** of one group — pushed over Info from its members row, so *back* is Info. No sport
 * in the route: it shares the page's filter.
 *
 * An id that does not survive the schema has no group behind it and goes to Play, as the page's
 * own route sends it.
 */
export default function GroupMembersRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <MembersScreen groupId={parsed.groupId} />;
}
