import type { Metadata } from 'next';

import { CourtsSection } from '@/features/courts/components/CourtsSection';
import { ExceptionsSection } from '@/features/courts/components/ExceptionsSection';
import { HoursSection } from '@/features/courts/components/HoursSection';
import { PricesSection } from '@/features/courts/components/PricesSection';
import { COURTS_COPY } from '@/features/courts/copy';
import { getCourtsAndPrices } from '@/features/courts/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: COURTS_COPY.title };

/** **Courts & prices** (the screens B3): the courts, their weekly hours, exceptions and prices. */
export default async function CourtsPage() {
  const { courts, exceptions, prices, sports, today } = await getCourtsAndPrices();
  return (
    <>
      <PageHeader caption={COURTS_COPY.caption} title={COURTS_COPY.title} />
      <CourtsSection courts={courts} sports={sports} />
      <HoursSection courts={courts} />
      <ExceptionsSection courts={courts} exceptions={exceptions} today={today} />
      <PricesSection prices={prices} />
    </>
  );
}
