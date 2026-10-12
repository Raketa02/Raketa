import type { Metadata } from 'next';

import { Bookings } from '@/features/bookings/components/Bookings';
import { BOOKINGS_COPY } from '@/features/bookings/copy';
import { getBookingsDay } from '@/features/bookings/queries';
import { readDayQuery } from '@/features/bookings/schemas';

export const metadata: Metadata = { title: BOOKINGS_COPY.title };

/**
 * **Bookings** (the screens B4): the day, the filter and the booking a link points at, from the
 * address.
 */
export default async function BookingsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = readDayQuery(await searchParams);
  const day = await getBookingsDay(query);
  return <Bookings day={day} pointedAt={query.booking} />;
}
