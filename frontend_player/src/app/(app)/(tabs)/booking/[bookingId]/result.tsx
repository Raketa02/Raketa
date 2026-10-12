import { Redirect, useLocalSearchParams } from 'expo-router';

import { BookedGameResult, parseBookingParams } from '@/features/proposals/types';

/**
 * **A booked game's result** — today's game screen at the Game the booking opened, pushed over the
 * details by *We played* or *Confirm the result* (#556), so *back* is the details — or over wherever
 * the player is by a notice of a step at the court (#664), so *back* is where they were.
 */
export default function BookedGameResultRoute() {
  const parsed = parseBookingParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <BookedGameResult bookingId={parsed.bookingId} />;
}
