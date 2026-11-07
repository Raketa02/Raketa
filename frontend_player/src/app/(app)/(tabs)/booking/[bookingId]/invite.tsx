import { Redirect, useLocalSearchParams } from 'expo-router';

import { parseSeatInviteParams } from '@/features/proposals/types';
import { InviteAFriendScreen } from '@/features/shell/types';

/**
 * ***Invite a friend*** into an empty seat of a booked friends game (#760) — the picker with one
 * seat, pushed over the game's details, so *back* is the game. Under the `booking` segment the
 * shell counts as Home's, so the Home column stays lit. Params that do not survive the schema name
 * no seat, and go to Home.
 */
export default function SeatInviteRoute() {
  const parsed = parseSeatInviteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <InviteAFriendScreen bookingId={parsed.bookingId} seatOf={parsed.seatOf} />;
}
