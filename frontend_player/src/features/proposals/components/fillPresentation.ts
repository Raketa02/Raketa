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

import type { Face, ItsAGamePicture, PaymentToConfirm, StillMissing } from '../domain/fill';
import type { Deadline } from '../domain/home';
import { gameDayOf, type GameDay } from '../domain/when';

import {
  clubName,
  gameDayWords,
  LINE_JOIN,
  paymentAwaitedClauses,
  shareWords,
  waitingClauses,
  yourPaymentWords,
} from './deckPresentation';
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
 * header, spoken; singles are *You against Kuba Wiśniewski*. The line under the word, when there is
 * one, follows the picture (`itsAGameLine`'s `spoken`).
 */
export function itsAGameSentence(picture: ItsAGamePicture, line?: string): string {
  const [, ...partners] = picture.yours;
  const yours = [playerName({ kind: 'you' }), ...partners.map(spoken)].join(' and ');
  const theirs = picture.theirs.map(spoken).join(' and ');
  const said = `${FILL_COPY.itsAGame.word} ${yours} against ${theirs}`;
  return line === undefined ? said : `${said}. ${line}`;
}

/**
 * **The line under the word**, Home's own words for the game (A8), drawn with the mocks' dot:
 *
 * - at a club that confirms (Q103; the screens A2.4), *Kazimierz Padel answers by 21:15 · Nobody
 *   pays until it confirms* (`waitingWords`) — the hour alone that day, the weekday with it on
 *   another; *Nobody pays until Kazimierz Padel confirms* with no deadline to give. Spoken a
 *   sentence a clause;
 * - while one payment is missing (Q110), *Waiting for one payment · until 14:40 · Nobody pays until
 *   it's in*, never whose. Spoken *Waiting for one payment until 14:40. Nobody pays until it's in* —
 *   *until 14:40* is no sentence of its own.
 */
export function itsAGameLine(missing: StillMissing): {
  readonly drawn: string;
  readonly spoken: string;
} {
  if (missing.of === 'theClub') {
    const clauses = waitingClauses(missing.club, missing.answerBy);
    return { drawn: clauses.join(LINE_JOIN), spoken: clauses.join('. ') };
  }
  const [waiting, until, nobodyPays] = paymentAwaitedClauses(missing.until);
  return {
    drawn: [waiting, until, nobodyPays].join(LINE_JOIN),
    spoken: `${waiting} ${until}. ${nobodyPays}`,
  };
}

/**
 * *Confirm your payment by 14:40 to keep your seat* — **the payer's time on the confirmation**
 * (Q109): the notice's and the email's words, written as Home writes the time.
 */
export function keepYourSeatBy(by: Deadline): string {
  return `${yourPaymentWords(by)} ${FILL_COPY.confirm.toKeepYourSeat}`;
}

/**
 * **A *TO CONFIRM* row's line** — *Confirm your payment by 14:40* while the payer's time runs (Q109,
 * the screens A7.3), the words Home's card says beside it; once it ran out, that the seat is open
 * to others until they confirm.
 */
export function toConfirmRowLine(by: Deadline | undefined): string {
  return by === undefined ? FILL_COPY.toConfirm.open : yourPaymentWords(by);
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
