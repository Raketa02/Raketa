import { Redirect, useLocalSearchParams } from 'expo-router';

import { BookedGameScreen, parseRescueParams } from '@/features/proposals/types';

/**
 * **A rescue seen from outside** — a booked game's open seat, opened from a *Seat open* card or a
 * *Seats to fill* row (#557, the screens A4.3), pushed over the group's page under Play, so the
 * column stays lit and *back* is the group. The booked game's own details, drawn for a reader not
 * in it; taking the seat puts the game on Home.
 *
 * Params that do not survive the schema go to Play, as the group page's own route sends them.
 */
export default function RescueRoute() {
  const parsed = parseRescueParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return <BookedGameScreen bookingId={parsed.bookingId} offer />;
}
