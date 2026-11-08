/**
 * ***Your rating*'s ways on** — the words on the controls under a result.
 *
 * Mid-pass there are two: the next sport the player chose, and stopping. On the last sport there
 * is one, and it names where it goes — read off where the pass began
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §5): **back to
 * the group** for a pass begun on one, **back to Home** for one begun there, and *See your
 * ratings* for the Skill passport's, which *is* your ratings.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { PassDestination } from '../domain/onboardingPass';

import { sportLabel } from './sportPresentation';

export const DONE_FOR_NOW = 'Done for now';

/** *Rate Tennis* — the next sport the player chose. */
export function rateNextLabel(sport: Sport): string {
  return `Rate ${sportLabel(sport)}`;
}

export function rateNextHint(sport: Sport): string {
  return `Starts the ${sportLabel(sport)} questions`;
}

export function doneForNowHint(next: Sport): string {
  return `Keeps the ratings you have and skips ${sportLabel(next)}`;
}

/**
 * The last sport's one control.
 *
 * `groupName` is the group's as the server last said it — `undefined` while it is still being
 * read, which only a long questionnaire after the group left the cache can make happen. The way
 * back is then *Back to the group*: the same place, unnamed for a moment, rather than a control
 * that waits.
 */
export function lastControlLabel(destination: PassDestination, groupName?: string): string {
  switch (destination.kind) {
    case 'group':
      return groupName === undefined ? 'Back to the group' : `Back to ${groupName}`;
    case 'passport':
      return 'See your ratings';
    case 'home':
      return 'Back to Home';
    case 'rankings':
      return 'Back to Rankings';
    case 'rate':
      // Never the last sport's: there is a sport after it. Named as the control that rates it.
      return rateNextLabel(destination.sport);
  }
}
