import { Redirect, useLocalSearchParams } from 'expo-router';

import { AdministratorYouScreen, parseClubRouteParams } from '@/features/administrator/types';

/** **The You tab** — a placeholder with the account's *Sign out*, until #517 builds it. */
export default function AdministratorYouRoute() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <AdministratorYouScreen clubId={parsed.clubId} />;
}
