/**
 * The eyebrow above onboarding's progress bar: the sport, and where it sits in the pass.
 *
 * **With no position there is no count, only the sport.** The bar and this phrase say the
 * same thing, and they have to disappear together: a filled rectangle is not readable at
 * any font size, which is why the words exist — so a "Rating 1 of 1" left beside no bar
 * would be exactly the invented denominator this slice removed, surviving in text.
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
