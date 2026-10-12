import 'server-only';

import { clubDay } from '@/features/courts/mappers';
import { readAsClub } from '@/server/club';

import { toBookingsDay, type BookingsDay } from './mappers';
import type { DayQuery } from './schemas';

/** **One day of the club's bookings**, under one filter; today when the query names no day. */
export async function getBookingsDay(query: DayQuery): Promise<BookingsDay> {
  const outcome = await readAsClub((api, auth) =>
    api.GET('/api/v1/club/bookings', {
      ...auth,
      params: {
        query:
          query.date === null
            ? { filter: query.filter }
            : { date: query.date, filter: query.filter },
      },
    }),
  );
  if (!outcome.ok) throw new Error(`The club's bookings could not be read: ${outcome.error.code}`);
  // Asked for no day, the backend read today: its day, not this server's clock, says which.
  return toBookingsDay(outcome.data, query.date === null ? outcome.data.day : clubDay(Date.now()));
}
