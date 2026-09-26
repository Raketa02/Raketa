import { Redirect, useLocalSearchParams } from 'expo-router';

import { NewOfficialGroupScreen, parseClubRouteParams } from '@/features/administrator/types';

/**
 * **New official group** — pushed over the Groups tab, full screen, **empty every time**: the form
 * is the screen's own state and goes with it, so the back arrow discards it.
 */
export default function NewOfficialGroupRoute() {
  const parsed = parseClubRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <NewOfficialGroupScreen clubId={parsed.clubId} />;
}
