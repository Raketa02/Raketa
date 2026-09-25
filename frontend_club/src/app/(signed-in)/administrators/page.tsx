import type { Metadata } from 'next';

import { getClub } from '@/features/club-details/queries';
import { SITE_COPY } from '@/ui/copy';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: SITE_COPY.frame.pages.administrators };

/** The club's administrators arrive with #523; until then the page is its title. */
export default async function AdministratorsPage() {
  await getClub();
  return <PageHeader title={SITE_COPY.frame.pages.administrators} />;
}
