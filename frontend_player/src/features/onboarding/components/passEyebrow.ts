/**
 * The eyebrow: the sport, and where it sits in the pass.
 *
 * **This is the only place which sport of how many is said.** A bar under the header used
 * to say it too; it measured sports, which meant it did not move for the eight questions a
 * player spends the longest on, and onboarding's indicator now measures the run instead
 * (ADR-0020). The words are the half that survived, because they are the half readable at
 * any font size — and having one carrier rather than two is what stops a sport denominator
 * being restored to a bar that no longer counts sports.
 *
 * **With no position there is no count, only the sport.** An invented denominator in text
 * would be exactly the one this app refuses to draw.
 *
 * Shared by the question and result screens because both draw the same chrome for the same
 * sport, and two copies of one sentence is how they would come to disagree.
 */

import type { RatingPosition } from '../domain/onboardingPass';
import type { Sport } from '../domain/Sport';

import { sportLabel } from './sportPresentation';

export function passEyebrow(sport: Sport, position: RatingPosition | undefined): string {
  if (position === undefined) return sportLabel(sport);
  return `${sportLabel(sport)} · Rating ${position.index} of ${position.total}`;
}
