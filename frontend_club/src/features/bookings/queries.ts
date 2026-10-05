import 'server-only';

import { cache } from 'react';

import { clubDay } from '@/features/courts/mappers';
import { readAsClub } from '@/server/club';

import { toBookingsDay, toRequests, type BookingsDay, type WaitingRequest } from './mappers';
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

/** The requests waiting for the club's answer, read once per request: the frame and Overview both ask. */
const readRequests = cache(() =>
  readAsClub((api, auth) => api.GET('/api/v1/club/bookings/waiting', auth)),
);

/** **What is waiting for the club's answer**, the one due first, first. */
export async function getRequests(): Promise<readonly WaitingRequest[]> {
  const outcome = await readRequests();
  if (!outcome.ok) {
    throw new Error(`The requests waiting for an answer could not be read: ${outcome.error.code}`);
  }
  return toRequests(outcome.data);
}

/**
 * **How many requests wait**, for the top bar's badge: `0` when the backend could not say. The
 * frame is drawn on every page, so a list it could not read leaves the badge off rather than the
 * page; Bookings and Overview read the list themselves, and say when they cannot.
 */
export async function getRequestCount(): Promise<number> {
  const outcome = await readRequests();
  return outcome.ok ? outcome.data.bookings.length : 0;
}
