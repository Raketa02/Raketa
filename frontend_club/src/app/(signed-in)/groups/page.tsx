import type { Metadata } from 'next';

import { getClub } from '@/features/club-details/queries';
import { SITE_COPY } from '@/ui/copy';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: SITE_COPY.frame.pages.groups };

/** The club's official groups arrive with #524; until then the page is its title. */
export default async function GroupsPage() {
  await getClub();
  return <PageHeader title={SITE_COPY.frame.pages.groups} />;
}
