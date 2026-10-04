import { Redirect, useLocalSearchParams } from 'expo-router';

import { AdministratorYouScreen, parseClubRouteParams } from '@/features/administrator/types';

/**
 * **The You tab** — the account's name, one row per official group opening its settings, *Start
 * playing* for an account that does not play yet, and *Sign out*. A directory since the settings
 * are pushed over it, under the tab's own segment so the You column stays lit.
 */
export default function AdministratorYouRoute() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <AdministratorYouScreen clubId={parsed.clubId} />;
}
