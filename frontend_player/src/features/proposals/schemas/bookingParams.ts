/**
 * **A booked game's route params** — the booking's id, and nothing else: the details, the room and
 * the result are all read from it (#556). Validated here, because a route param is never trusted.
 */

import { z } from 'zod';

const BookingParams = z.object({ bookingId: z.string().uuid() });

export interface BookingRoute {
  readonly bookingId: string;
}

/** The booking's id, or `undefined` for params this app cannot read. */
export function parseBookingParams(params: unknown): BookingRoute | undefined {
  const parsed = BookingParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
