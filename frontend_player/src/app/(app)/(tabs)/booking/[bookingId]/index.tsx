import { Redirect, useLocalSearchParams } from 'expo-router';

import { useGroupName } from '@/features/groups/types';
import {
  BookedGameScreen,
  parseBookingParams,
  useSeatOpeningGroup,
} from '@/features/proposals/types';

/**
 * **A booked game you're in, in detail** — pushed over the Home tab from a Home card's *Open game*
 * or *It's a game!*'s (#556), so the Home column stays lit and *back* is Home.
 *
 * Under a `booking` segment the shell counts as Home's (`shellTabs`), because Home's root is the
 * shell's own root and has no segment to nest under — `games/[gameId]`'s reason. A param that does
 * not survive the schema has no game behind it, and goes to Home.
 *
 * **The group's name is asked here** (#760): *Open to Ogrody* on an empty seat names the game's
 * group, which is `groups'` read — and `groups` imports `proposals`, so `proposals` cannot import it
 * back. Asked only while the reader may open a seat (`useSeatOpeningGroup`), off the details' own
 * read.
 */
export default function BookedGameRoute() {
  const parsed = parseBookingParams(useLocalSearchParams());
  const groupName = useGroupName(useSeatOpeningGroup(parsed?.bookingId));

  if (parsed === undefined) return <Redirect href="/" />;

  return (
    <BookedGameScreen
      bookingId={parsed.bookingId}
      {...(groupName === undefined ? {} : { groupName })}
    />
  );
}
