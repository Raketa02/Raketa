import type { Metadata } from 'next';

import { getClub } from '@/features/club-details/queries';
import { Groups } from '@/features/groups/components/Groups';
import { getGroups } from '@/features/groups/queries';
import { getWayAndSettings } from '@/features/raketa-settings/queries';
import { SITE_COPY } from '@/ui/copy';

export const metadata: Metadata = { title: SITE_COPY.frame.pages.groups };

export default async function GroupsPage() {
  const [club, groups, settings] = await Promise.all([getClub(), getGroups(), getWayAndSettings()]);
  return <Groups club={club.name} groups={groups} otherClubs={settings.otherClubs} />;
}
