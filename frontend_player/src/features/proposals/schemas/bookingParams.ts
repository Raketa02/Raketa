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

const RescueParams = z.object({ groupId: z.string().uuid(), bookingId: z.string().uuid() });

export interface RescueRoute {
  readonly groupId: string;
  readonly bookingId: string;
}

/**
 * **A rescue's route params** (#557) — the group it is offered in, and the booking. The group only
 * places the screen under its page; the details are read from the booking.
 */
export function parseRescueParams(params: unknown): RescueRoute | undefined {
  const parsed = RescueParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
