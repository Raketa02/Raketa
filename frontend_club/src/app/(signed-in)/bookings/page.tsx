import type { Metadata } from 'next';

import { Bookings } from '@/features/bookings/components/Bookings';
import { BOOKINGS_COPY } from '@/features/bookings/copy';
import { getBookingsDay } from '@/features/bookings/queries';
import { readDayQuery } from '@/features/bookings/schemas';
import { getClub } from '@/features/club-details/queries';
import { getChecksIn } from '@/features/raketa-settings/queries';

export const metadata: Metadata = { title: BOOKINGS_COPY.title };

/**
 * **Bookings** (the screens B4): the day, the filter and the booking a link points at, from the
 * address; *Check in*, when the club's settings say it checks players in; and the club's name,
 * which the players read when it refuses a request or leaves one unanswered.
 */
export default async function BookingsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = readDayQuery(await searchParams);
  const [day, checksIn, club] = await Promise.all([
    getBookingsDay(query),
    getChecksIn(),
    getClub(),
  ]);
  return <Bookings day={day} clubName={club.name} pointedAt={query.booking} checksIn={checksIn} />;
}
