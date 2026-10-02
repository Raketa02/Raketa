import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  OfficialMembersScreen,
  parseOfficialGroupRouteParams,
} from '@/features/administrator/types';

/**
 * **Members of an official group, for the Administrator who runs it** — pushed over the group's
 * page from its players card (#529), so *back* is the page. A param that does not survive the
 * schema has no group behind it, and goes where the page's own route sends it.
 */
export default function OfficialGroupMembersRoute() {
  const parsed = parseOfficialGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <OfficialMembersScreen clubId={parsed.clubId} groupId={parsed.groupId} />;
}
