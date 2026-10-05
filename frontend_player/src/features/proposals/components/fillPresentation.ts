/**
 * **Every sentence the moment a game fills composes from a value** — the toast's count, *It's a
 * game!* as a listener hears it, and the facts of a payment to confirm
 * ([#555](https://github.com/Raketa02/Raketa/issues/555)). The fixed words are `fillCopy.ts`.
 *
 * **The announcement is built from whole Names**, the yes screen's own rule (ADR-0167 §3, ADR-0171):
 * the tiles draw initials over a poster, and those never reach a sentence.
 */

import { sportLabel } from '@/features/onboarding/types';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { playerName } from '@/shared/formatting/playerName';
import { platformClock } from '@/shared/date/platformZone';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Face, ItsAGamePicture, PaymentToConfirm } from '../domain/fill';
import { gameDayOf, type GameDay } from '../domain/when';

import { clubName, gameDayWords, LINE_JOIN, shareWords } from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { liveYesTitle } from './liveYesesPresentation';

/** *Booking in 7 s* — the toast's words, the count rounded up. */
export function bookingIn(seconds: number): string {
  return `Booking in ${seconds} s`;
}

/** Said once, as the toast arrives — the count in words, and that it can be undone. */
export function bookingAnnouncement(seconds: number): string {
  return `Booking in ${seconds} seconds. You can undo it.`;
}

function spoken(face: Face): string {
  return playerName(
    face.name === undefined ? { kind: 'unknown' } : { kind: 'player', name: face.name },
  );
}

/**
 * *It's a game! You and Zofia Bielecka against Ania Kowalska and Ewa Majewska* — the screen's
 * header, spoken; singles are *You against Kuba Wiśniewski*.
 */
export function itsAGameSentence(picture: ItsAGamePicture): string {
  const [, ...partners] = picture.yours;
  const yours = [playerName({ kind: 'you' }), ...partners.map(spoken)].join(' and ');
  const theirs = picture.theirs.map(spoken).join(' and ');
  return `${FILL_COPY.itsAGame.word} ${yours} against ${theirs}`;
}

/**
 * *Waiting for Kazimierz Padel to confirm — nobody pays until it does.* — the toast when a yes filled
 * a game an On request club confirms (#543); *the club* when the card no longer names it.
 */
export function sentToTheClub(club: string | undefined): string {
  return `Waiting for ${club ?? 'the club'} to confirm — nobody pays until it does.`;
}

/** The share to confirm and the seller: *32 zł to Bonarka Arena*. */
export function chargeLine(amountGrosze: number, clubName: string | undefined): string {
  return `${formatZloty(amountGrosze)} to ${clubName ?? 'the club'}`;
}

/** The game it is for: *Padel · Saturday · 16:00*, the court block's day words. */
export function chargeGameLine(sport: Sport, startsAt: string, now: number): string {
  const day = gameDayOf(startsAt, now);
  return [
    sportLabel(sport),
    day === undefined ? undefined : gameDayWords(day),
    platformClock(startsAt),
  ]
    .filter((part): part is string => part !== undefined)
    .join(LINE_JOIN);
}

/**
 * A *TO CONFIRM* row's button, spoken — what it confirms: *Confirm your payment for Padel · Saturday
 * 15:00 at Bonarka Arena, 28 zł*.
 */
export function toConfirmLabel(payment: PaymentToConfirm, day: GameDay | undefined): string {
  return `Confirm your payment for ${liveYesTitle(payment, day)} at ${clubName(payment)}, ${shareWords(payment)}`;
}
