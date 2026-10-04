import { Redirect, useLocalSearchParams } from 'expo-router';

import { AdministratorGroupsScreen, parseClubRouteParams } from '@/features/administrator/types';

/**
 * **The Groups tab** — the area's root, and where the entry gate lands an account that only runs a
 * club's groups. `features/administrator`'s own screen.
 */
export default function AdministratorGroupsRoute() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <AdministratorGroupsScreen clubId={parsed.clubId} />;
}
