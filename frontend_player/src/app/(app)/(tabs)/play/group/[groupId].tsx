import { Redirect, useLocalSearchParams } from 'expo-router';

import { GroupScreen, parseGroupRouteParams } from '@/features/groups/types';

/**
 * A group's page — **pushed over Play › Groups**, under Play so the column stays lit.
 *
 * A param that does not survive the schema has no group behind it, and the honest place to say so
 * is the list rather than a page about nothing — `Redirect`, as the game route does, because a
 * link this app cannot read was never a place the player came from.
 */
export default function GroupRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <GroupScreen groupId={parsed.groupId} />;
}
