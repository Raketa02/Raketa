import { Redirect, useLocalSearchParams } from 'expo-router';

import { BookedGameScreen, parseBookingParams } from '@/features/proposals/types';

/**
 * **A booked game you're in, in detail** — pushed over the Home tab from a Home card's *Open game*
 * or *It's a game!*'s (#556), so the Home column stays lit and *back* is Home.
 *
 * Under a `booking` segment the shell counts as Home's (`shellTabs`), because Home's root is the
 * shell's own root and has no segment to nest under — `games/[gameId]`'s reason. A param that does
 * not survive the schema has no game behind it, and goes to Home.
 */
export default function BookedGameRoute() {
  const parsed = parseBookingParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <BookedGameScreen bookingId={parsed.bookingId} />;
}
