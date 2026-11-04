/**
 * **The door's words** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §2, §5, [#730](https://github.com/Raketa02/Raketa/issues/730)) — *Get your level — pick the
 * sports you play, a few questions each*, or, with a run left halfway, *Carry on with your padel
 * questions — you're on question 5*.
 *
 * Each sentence is the card's two lines, split at its dash: the headline names what the door
 * does, the line under it says what it costs or where it stands, and the one button is the door.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { PICKER_TITLE } from './pickerPresentation';
import { sportInLine } from './sportPresentation';

export const LEVEL_DOOR_COPY = {
  headline: 'Get your level',
  line: 'Pick the sports you play, a few questions each.',
  start: 'Pick your sports',
  startHint: `Opens ${PICKER_TITLE}`,
  carryOn: 'Carry on',
} as const;

/** *Carry on with your padel questions* — the run left halfway, by its sport. */
export function carryOnHeadline(sport: Sport): string {
  return `Carry on with your ${sportInLine(sport)} questions`;
}

/** *You're on question 5.* — the one she is on, counted as the run counts it. */
export function carryOnLine(question: number): string {
  return `You're on question ${question}.`;
}

export function carryOnHint(sport: Sport): string {
  return `Opens your ${sportInLine(sport)} questions where you left them`;
}
