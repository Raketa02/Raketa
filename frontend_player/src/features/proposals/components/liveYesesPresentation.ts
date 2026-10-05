/**
 * **Every sentence You › Payments' LIVE YESES composes** — the head, the cap under it, and a row
 * ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.3; mock 48).
 *
 * A row names its game the way the deck's court block does — *Today*, *Tomorrow*, *Saturday*, or a
 * weekday with its date from a week out (`gameDayWords`) — so the same game is the same words on
 * both surfaces; the club and the share are the card's too (`clubName`, `shareWords`).
 */

import { sportLabel } from '@/features/onboarding/types';
import { platformClock } from '@/shared/date/platformZone';

import type { LiveYes } from '../domain/liveYes';
import type { GameDay } from '../domain/when';

import { LINE_JOIN, clubName, gameDayWords, shareWords } from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

/** The section's name — alone over a read that failed, where there is nothing to count. */
export const LIVE_YESES_TITLE = 'Live yeses';

/** *Live yeses · 3* — every live yes, across sports; the eyebrow's style uppercases it. */
export function liveYesesHeader(count: number): string {
  return `${LIVE_YESES_TITLE}${LINE_JOIN}${count}`;
}

/** *up to 10 per sport* — under the head, the cap the count runs against. */
export function liveYesesCapLine(capPerSport: number): string {
  return `up to ${capPerSport} per sport`;
}

/** *Padel · Saturday 15:00* — the row's title. */
export function liveYesTitle(yes: LiveYes, day: GameDay | undefined): string {
  const when = [day === undefined ? undefined : gameDayWords(day), platformClock(yes.startsAt)]
    .filter((part): part is string => part !== undefined)
    .join(' ');
  return `${sportLabel(yes.sport)}${LINE_JOIN}${when}`;
}

/** The row, spoken: *Padel · Saturday 15:00, Bonarka Arena, 28 zł if it fills*. */
export function liveYesLabel(yes: LiveYes, day: GameDay | undefined): string {
  return [
    liveYesTitle(yes, day),
    clubName(yes),
    `${shareWords(yes)} ${PROPOSALS_COPY.game.ifItFills}`,
  ].join(', ');
}

/** Where a row's press goes. */
export const LIVE_YES_HINT = 'Opens the game’s details';
