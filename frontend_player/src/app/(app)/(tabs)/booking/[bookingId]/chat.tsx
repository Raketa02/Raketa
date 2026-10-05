import { Redirect, useLocalSearchParams } from 'expo-router';

import { BookedGameChat, parseBookingParams } from '@/features/proposals/types';

/**
 * **A booked game's chat** — pushed over its details, the only way in (the screens A4.4, #556), so
 * the back chevron returns to the details. The bar stands down here, as it does in every room.
 */
export default function BookedGameChatRoute() {
  const parsed = parseBookingParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/" />;

  return <BookedGameChat bookingId={parsed.bookingId} />;
}
