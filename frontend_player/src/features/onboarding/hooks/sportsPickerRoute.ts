/**
 * **The picker, opened from a door** — where *Which sports do you play?* is, and what the route
 * carries for the pass it begins ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §2, §4, §7).
 *
 * A group's tab carries its group and its tab, for the pass to return to — the params the picker's
 * route reads (`groups`' `parseGroupPlace`); Home carries nothing. **A door that offers fewer than
 * every sport carries them too** — *+ Another sport* ([#731](https://github.com/Raketa02/Raketa/issues/731)),
 * over the sports the player is unrated in — and the picker lists only those (`parsePickerOffer`).
 * The door and the Home card offer every sport, and carry none.
 *
 * Every door walks in by `replace`: the questionnaire is a sibling group of the app's tree, and the
 * way back is the pass ending, which the gate reads off the origin.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { DoorOrigin } from '../domain/onboardingPass';
import { offerParam } from '../schemas/routeParams';

export function sportsPickerRoute(from: DoorOrigin, offer?: readonly Sport[]) {
  const offered = offer === undefined ? {} : { offer: offerParam(offer) };
  return from.kind === 'group'
    ? ({
        pathname: '/sports',
        params: { groupId: from.groupId, tab: from.tab, ...offered },
      } as const)
    : ({ pathname: '/sports', params: offered } as const);
}
