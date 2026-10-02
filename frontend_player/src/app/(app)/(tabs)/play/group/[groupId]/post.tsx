import { Redirect, useLocalSearchParams } from 'expo-router';

import { PostAGamePage, parseGroupRouteParams } from '@/features/groups/types';

/**
 * ***Post a game*** — pushed over a group's page from Fill in's floating button or *Nothing picked
 * right now*, under Play so the column stays lit, and *back* is the page, on Fill in (#558).
 *
 * An id that does not survive the schema has no group behind it and goes to Play, as the page's
 * own route sends it.
 */
export default function PostAGameRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <PostAGamePage groupId={parsed.groupId} />;
}
