import { Redirect, useLocalSearchParams } from 'expo-router';

import { useScreenInView } from '@/features/auth/types';
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
 *
 * **Whether the page is the screen in view** is read here and handed in (`useScreenInView`'s rule):
 * a game's details, Info or *Post a game* pushed over it leave it mounted and out of view, and what
 * its tabs draw is seen only while it is in view (#849).
 */
export default function GroupRoute() {
  const parsed = parseGroupRouteParams(useLocalSearchParams());
  const inView = useScreenInView();

  if (parsed === undefined) return <Redirect href="/play" />;

  return (
    <GroupScreen
      groupId={parsed.groupId}
      inView={inView}
      {...(parsed.arrival === undefined ? {} : { arrival: parsed.arrival })}
      {...(parsed.returning === undefined ? {} : { returning: parsed.returning })}
    />
  );
}
