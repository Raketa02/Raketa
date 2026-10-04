/**
 * **When a scrolled page is near its end** — New group's and Join a group's, the two scrollers
 * that ask a search for its next twenty clubs. Within half a screen of the end, so the next page
 * is on its way before the player reaches it.
 */

import type { NativeScrollEvent } from 'react-native';

/** How often a scroller reports its position while it moves — once a frame. */
export const SCROLL_EVENT_EVERY_MS = 16;

export function nearTheEnd({
  layoutMeasurement,
  contentOffset,
  contentSize,
}: NativeScrollEvent): boolean {
  return layoutMeasurement.height * 1.5 + contentOffset.y >= contentSize.height;
}
