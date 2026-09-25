import type { Metadata } from 'next';

import { ClubDetailsForm } from '@/features/club-details/components/ClubDetailsForm';
import { DETAILS_COPY } from '@/features/club-details/copy';
import { getClub, mapSettings } from '@/features/club-details/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: DETAILS_COPY.title };

export default async function ClubDetailsPage() {
  const club = await getClub();
  return (
    <>
      <PageHeader caption={DETAILS_COPY.caption} title={DETAILS_COPY.title} />
      <ClubDetailsForm club={club} map={mapSettings()} />
    </>
  );
}
