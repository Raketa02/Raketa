/**
 * A sport's name and its identity colour — the two things the wire does not carry.
 *
 * `SportResource` describes how a sport is *played and sold* (player count, bookable
 * durations); what it is called in this locale and what colour it wears are presentation,
 * and presentation is the client's.
 *
 * Sport identity deliberately reuses the semantic palette rather than extending it: four
 * more hues would make every screen with a sport dot noisier, and the dot always sits
 * beside the sport's name in text. **A fifth sport forces a real decision** — and until
 * that decision is made, the domain's closed set and the theme's keys are the same four,
 * so a sport that reached one without the other fails `pnpm typecheck`.
 */

import { theme } from '@/shared/ui';

import type { Sport } from '@/shared/vocabulary/sport';

const LABELS: Readonly<Record<Sport, string>> = {
  padel: 'Padel',
  tennis: 'Tennis',
  squash: 'Squash',
  badminton: 'Badminton',
};

export function sportLabel(sport: Sport): string {
  return LABELS[sport];
}

/**
 * *padel* — a sport **inside a sentence**, where its name is an ordinary noun. One rule for every
 * sentence that names one (*This group plays padel*, *Carry on with your padel questions*), here
 * beside the name since its third caller (#730).
 */
export function sportInLine(sport: Sport): string {
  return sportLabel(sport).toLowerCase();
}

/**
 * The three-letter form, for the one place a sport is drawn beside a level in a tag that has
 * to fit three across next to a face and a ring — the You tab's header card (ADR-0179 §1,
 * *Pad 2,71 · Ten 3,10 · Squ 2,30*). Drawn only: the pill is spoken with `sportLabel`.
 */
const SHORT_LABELS: Readonly<Record<Sport, string>> = {
  padel: 'Pad',
  tennis: 'Ten',
  squash: 'Squ',
  badminton: 'Bad',
};

export function sportShortLabel(sport: Sport): string {
  return SHORT_LABELS[sport];
}

export function sportColour(sport: Sport): string {
  return theme.sport[sport];
}
