import type { Metadata } from 'next';

import { getClub } from '@/features/club-details/queries';
import { Overview } from '@/features/overview/components/Overview';
import { getSetup, wasToldLive } from '@/features/overview/queries';
import { SITE_COPY } from '@/ui/copy';

export const metadata: Metadata = { title: SITE_COPY.frame.pages.overview };

export default async function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ notice }, club, setup, toldLive] = await Promise.all([
    searchParams,
    getClub(),
    getSetup(),
    wasToldLive(),
  ]);
  return (
    <Overview
      club={club}
      setup={setup}
      toldLive={toldLive}
      passwordSet={notice === 'password-set'}
    />
  );
}
