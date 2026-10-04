import { useLocalSearchParams } from 'expo-router';

import { JoinGroupScreen, parseJoinRouteParams } from '@/features/groups/types';
import { appLinkTo } from '@/shared/config/appLinks';
import { getEnv } from '@/shared/config/env';

/**
 * *Join a group* — pushed over Play › Groups; `features/groups`' own screen. Opened by a group link
 * (#520) it carries the link's code, checked here and spelled back as the group's link at the address
 * the app's links live on — the scheme's while no domain is set — which the screen opens with in its
 * field. A code that cannot be one is Join a group opened from Play.
 */
export default function JoinGroupRoute() {
  const parsed = parseJoinRouteParams(useLocalSearchParams());
  const link =
    parsed === undefined ? undefined : appLinkTo('join', parsed.code, getEnv().linkDomain);

  return <JoinGroupScreen link={link} />;
}
