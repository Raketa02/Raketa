import { Redirect, useLocalSearchParams } from 'expo-router';

import { FriendsScreen, parseFriendsRouteParams } from '@/features/groups/types';

/**
 * **Friends**, for one sport of one group — pushed over the group's page from an empty seat on its
 * court or from *+ Friends*, so *back* is the court.
 *
 * Params that do not survive the schema are a screen about nothing — no group, or a sport with no
 * court to count — and go to Play, as the page's own route sends them.
 */
export default function GroupFriendsRoute() {
  const parsed = parseFriendsRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <FriendsScreen groupId={parsed.groupId} sport={parsed.sport} />;
}
