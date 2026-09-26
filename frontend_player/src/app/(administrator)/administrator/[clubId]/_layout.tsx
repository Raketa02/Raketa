import { Redirect, useLocalSearchParams } from 'expo-router';

import { AdministratorArea, parseClubRouteParams } from '@/features/administrator/types';

/**
 * **One club's administrator area** — its stack and its **Groups · You** bar, drawn by the feature
 * (`AdministratorArea`), which also decides whether this account may be here.
 *
 * A club id that does not survive the schema has no area behind it, and `/` is where the entry
 * gate decides where the person belongs instead.
 */
export default function AdministratorAreaLayout() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <AdministratorArea clubId={parsed.clubId} />;
}
