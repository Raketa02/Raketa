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

import type {
  Face,
  ItsAGamePaymentAwaited,
  ItsAGamePicture,
  PaymentToConfirm,
} from '../domain/fill';
import type { PaymentWindow, SeatAtStake, YourTime } from '../domain/home';
import { gameDayOf, type GameDay } from '../domain/when';

import {
  clubName,
  gameDayWords,
  LINE_JOIN,
  paymentAwaitedClauses,
  shareWords,
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
 * **The line under the word** while one payment is missing (Q110), Home's own words for the game
 * (A8), drawn with the mocks' dot: *Waiting for one payment · until 14:40 · Nobody pays until it's
 * in*, never whose. Spoken *Waiting for one payment until 14:40. Nobody pays until it's in* —
 * *until 14:40* is no sentence of its own.
 */
export function itsAGameLine(missing: ItsAGamePaymentAwaited): {
  readonly drawn: string;
  readonly spoken: string;
} {
  const [waiting, until, nobodyPays] = paymentAwaitedClauses(missing.until);
  return {
    drawn: [waiting, until, nobodyPays].join(LINE_JOIN),
    spoken: `${waiting} ${until}. ${nobodyPays}`,
  };
}

/**
 * *Confirm your payment by 14:40 to keep your seat* — **the payer's time with the seat it keeps**
 * (Q109): the notice's and the email's words, written as Home writes the time; before the club's
 * cut-off *Fix your card by 14:40 to keep your seat* (Q113), and on a rescue *… to take the seat*
 * (#640). With no seat named — where the status tag says what is at stake — the time alone.
 */
export function seatKeptBy(time: YourTime, seat: SeatAtStake | undefined): string {
  const words = yourPaymentWords(time);
  return seat === undefined ? words : `${words} ${FILL_COPY.confirm.toSeat[seat]}`;
}

/**
 * **The confirmation's note** while the time runs — the seat it keeps, and on a rescue that the seat
 * is theirs until then: *Fix your card by 14:40 to take the seat — it's kept for you until then*.
 */
export function confirmNote(time: YourTime, seat: SeatAtStake): string {
  const kept = seatKeptBy(time, seat);
  return seat === 'aRescue' ? `${kept} — ${FILL_COPY.confirm.keptForYou}` : kept;
}

/**
 * **The toast at a refused card** (the screens A2.4) — *Your card didn't go through — fix it to keep
 * your seat. Nothing is paid now.* before the cut-off, *Your payment didn't go through — confirm it
 * to keep your seat* after it; *to take the seat* on a rescue (#640).
 */
export function refusedToast(window: PaymentWindow, seat: SeatAtStake): string {
  return FILL_COPY.refused[seat][window];
}

/**
 * **A *TO CONFIRM* row's line** — *Confirm your payment by 14:40* while the payer's time runs (Q109,
 * the screens A7.3), or *Fix your card by 14:40* before the cut-off (Q113), the words Home's card
 * says beside it; once it ran out, that the seat is open to others until they confirm.
 */
export function toConfirmRowLine(time: YourTime | undefined): string {
  return time === undefined ? FILL_COPY.toConfirm.open : yourPaymentWords(time);
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
 * 15:00 at Bonarka Arena, 28 zł*, or *Fix your card for …* before the cut-off (Q113), its window the
 * row's own.
 */
export function toConfirmLabel(
  payment: PaymentToConfirm,
  day: GameDay | undefined,
  window: PaymentWindow,
): string {
  const act = FILL_COPY.toConfirm.spoken[window];
  return `${act} ${liveYesTitle(payment, day)} at ${clubName(payment)}, ${shareWords(payment)}`;
}
