/**
 * The sports picker's route.
 *
 * **Where the pass begins is read off the params** (#729, #730, ADR-0200 §2, §5): a group and one
 * of its tabs is the picker opened from that tab's door, and the pass it begins returns to it.
 * Anything else is the picker opened from Home. The params are untrusted input, so the group's are
 * checked by the feature whose words a tab is, and a link that does not survive that is Home's
 * picker rather than a pass returning somewhere nobody began it.
 */

import { useLocalSearchParams } from 'expo-router';

import { parseGroupPlace } from '@/features/groups/types';
import { FROM_HOME, SportsPickerScreen, fromAGroup } from '@/features/onboarding/types';

export default function SportsRoute() {
  const place = parseGroupPlace(useLocalSearchParams());

  return (
    <SportsPickerScreen
      origin={place === undefined ? FROM_HOME : fromAGroup(place.groupId, place.tab)}
    />
  );
}
