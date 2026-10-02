/**
 * **Whether an element scrolls with the page** — the scroller it sits in, or `undefined` for one
 * pinned outside every scroller.
 *
 * **In `test-support/` because both You tabs ask it** (#529): *Sign out* is pinned under the page
 * on the player's and the administrator's, so it is in the same place however many rows are over
 * it, and what a suite can observe of that is that the button is in no scroller while the rows
 * are in one.
 */

import { ScrollView } from 'react-native';

/** A test instance as any RNTL query returns it — only its way up is read. */
interface Placed {
  readonly type: unknown;
  readonly parent: Placed | null;
}

/** The nearest `ScrollView` over the element, or `undefined` when none is. */
export function scrollerOf(element: Placed): Placed | undefined {
  for (let at = element.parent; at !== null; at = at.parent) {
    if (at.type === ScrollView) return at;
  }
  return undefined;
}
