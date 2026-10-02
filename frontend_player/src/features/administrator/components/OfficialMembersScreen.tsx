/**
 * **Members of an official group, for its Administrator** — pushed over the group's page from the
 * members card (#529). It is the member's own screen (`groups`' `AdministeredMembersScreen`): the
 * same header, rows and record sheet, the pill listing the sports the group declares. They are this
 * area's read of the group, already in hand from the page it was opened from.
 */

import { AdministeredMembersScreen } from '@/features/groups/types';

import { useOfficialGroup } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';

export interface OfficialMembersScreenProps {
  readonly clubId: string;
  readonly groupId: string;
}

export function OfficialMembersScreen({ clubId, groupId }: OfficialMembersScreenProps) {
  const group = useOfficialGroup(clubId, groupId).data;
  return (
    <AdministeredMembersScreen
      groupId={groupId}
      sports={group?.sports}
      refused={ADMINISTRATOR_COPY.group.membersRefused}
    />
  );
}
