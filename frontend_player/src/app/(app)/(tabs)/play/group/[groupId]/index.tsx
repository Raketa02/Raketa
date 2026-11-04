import { Redirect, useLocalSearchParams } from 'expo-router';

import { GroupScreen, parseGroupRouteParams } from '@/features/groups/types';

/**
 * A group's page — **pushed over Play › Groups**, under Play so the column stays lit.
 *
 * A param that does not survive the schema has no group behind it, and the honest place to say so
 * is the list rather than a page about nothing — `Redirect`, as the game route does, because a
 * link this app cannot read was never a place the player came from.
 *
 * **A notice opens it at a card** (#559): the card's sport, kind and id ride with the group's, and the
 * page opens on that deck with the card on top — checked with the group's id, and dropped whole if
 * any of the three is not one this build can read. **A rating pass begun on the page returns to it**
 * (#729) with the tab it began on and the sport it rated last, checked the same way.
 */
export default function GroupRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return (
    <GroupScreen
      groupId={parsed.groupId}
      {...(parsed.arrival === undefined ? {} : { arrival: parsed.arrival })}
      {...(parsed.returning === undefined ? {} : { returning: parsed.returning })}
    />
  );
}
