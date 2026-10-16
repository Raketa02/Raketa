/**
 * **Every sentence a group's Fill in tab composes from a value** — the sections' heads, a row's
 * title and subtitle, and each row spoken ([#557](https://github.com/Raketa02/Raketa/issues/557);
 * the screens A3; mocks 11–13). The fixed words are `fillInCopy.ts`.
 *
 * A row names its game as the court block does — *Saturday*, *Tomorrow*, a weekday with its date a
 * week out (`gameDayWords`) — and a moment as the money line does, *Fri 16:00*: every day and hour is
 * the club's (`shared/date/platformZone`).
 */

import { sportLabel } from '@/features/onboarding/types';
import { counted } from '@/shared/formatting/counted';
import { platformClock } from '@/shared/date/platformZone';

import type { SeatToFill } from '../domain/fillIn';
import type { RescueOffer } from '../domain/home';
import type { LiveYes } from '../domain/liveYes';
import type { GameDay } from '../domain/when';

import { LINE_JOIN, clubName, gameDayWords, shortMoment } from './deckPresentation';
import { FILL_IN_COPY } from './fillInCopy';

const COPY = FILL_IN_COPY;

/** A drawn line's parts aloud: the mocks' dots are commas to a listener. */
const SPOKEN_JOIN = ', ';

/** *Seats to fill · 1* */
export function seatsToFillHeader(count: number): string {
  return `${COPY.seatsToFill}${LINE_JOIN}${count}`;
}

/** *You're In · 1* */
export function youreInHeader(count: number): string {
  return `${COPY.youreIn}${LINE_JOIN}${count}`;
}

/** *Padel · Saturday 16:00*, and *· friendly* after a For fun game's. */
export function rowTitle(
  game: Pick<SeatToFill, 'sport' | 'kind' | 'startsAt'>,
  day: GameDay | undefined,
): string {
  const when = [day === undefined ? undefined : gameDayWords(day), platformClock(game.startsAt)]
    .filter((part): part is string => part !== undefined)
    .join(' ');
  return [sportLabel(game.sport), when, ...(game.kind === 'forFun' ? [COPY.friendly] : [])].join(
    LINE_JOIN,
  );
}

/**
 * *fills by Fri 16:00* · *offered until the start* — how long a rescue's seat is offered: the bold
 * half of a row's subtitle, and the money row's aside on its details seen from outside.
 */
export function seatWhen(offer: RescueOffer): string {
  return offer.fillsByTheCutOff
    ? `${COPY.fillsBy} ${shortMoment(offer.deadline)}`
    : COPY.offeredUntilTheStart;
}

/** *book by Sat 13:00* — the bold half of a yes's subtitle. */
export function yesWhen(yes: Pick<LiveYes, 'deadline'>): string {
  return `${COPY.bookBy} ${shortMoment(yes.deadline)}`;
}

/**
 * **A rescue row's door, spoken** — *Padel · Saturday 16:00, Ogrody 33, Court 6, fills by Fri 16:00,
 * 1 seat open*. Its *I'm in* and its posters are elements of their own.
 */
export function seatRowLabel(row: SeatToFill, day: GameDay | undefined): string {
  return [
    rowTitle(row, day),
    clubName(row),
    row.courtName,
    seatWhen(row),
    counted(row.openSeats, 'seat open', 'seats open'),
  ].join(SPOKEN_JOIN);
}

/** **A You're In row's door, spoken** — *Padel · Saturday 15:00, Bonarka Arena, book by Sat 13:00*. */
export function yesRowLabel(yes: LiveYes, day: GameDay | undefined): string {
  return [rowTitle(yes, day), clubName(yes), yesWhen(yes)].join(SPOKEN_JOIN);
}
