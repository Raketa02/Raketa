/**
 * **Every sentence Check in says** (the screens B6; the mechanics §15.1 and §16.10): the camera,
 * the box, the player checked in, and why a code checked nobody in.
 */

import { BOOKINGS_COPY, shortDay } from '@/features/bookings/copy';
import { sportName } from '@/features/club-details/mappers';
import { COMMON_REFUSALS, FALLBACK_REFUSAL } from '@/ui/copy';

import type { CheckedIn, CheckInRefusal } from './mappers';

export const CHECK_IN_COPY = {
  caption: 'At the desk',
  /** The page's name, and Bookings' button to it. */
  title: 'Check in',
  camera: {
    title: 'Scan the player’s code',
    /** The viewfinder, as a screen reader names it. */
    label: 'Camera',
    opening: 'Opening the camera…',
    reading: 'Hold the player’s QR code up to the camera.',
    trouble: {
      unsupported: 'This browser can’t use the camera here. Type the short code below instead.',
      blocked:
        'The camera is blocked for this site. Allow it in the browser’s settings and try again, ' +
        'or type the short code below.',
      missing: 'This device has no camera to use. Type the short code below instead.',
      failed: 'The camera didn’t open. Try again, or type the short code below.',
      stopped: 'The camera stopped. Try again, or type the short code below.',
    },
    retry: 'Try the camera again',
  },
  typed: {
    title: 'Type the short code',
    lead: 'The six characters under the player’s QR code, when the camera won’t read it.',
    label: 'Short code',
    submit: 'Check in',
    submitting: 'Checking in…',
  },
  /** The answer, while a code is being asked about. */
  checking: 'Checking the code…',
  /** A refusal nobody's code caused: the same code can be asked about again. */
  retry: 'Try again',
  off: {
    title: 'You don’t check players in',
    lead:
      'Switch on “We check players in” in Raketa settings, and this page scans the QR code on a ' +
      'player’s phone, or takes the short code under it. Money never depends on it: you’re paid ' +
      'whether people come or not.',
    settings: 'Open Raketa settings',
  },
} as const;

/** *19:00 · Court 2 · Padel*. */
export function checkedInGame(checkedIn: CheckedIn): string {
  return `${checkedIn.hour.from} · ${checkedIn.court} · ${sportName(checkedIn.sport)}`;
}

/** *Piotr Sikora — checked in ✓*. */
export function checkedInPlayer(checkedIn: CheckedIn): string {
  return `${checkedIn.player ?? BOOKINGS_COPY.nameless} — ${BOOKINGS_COPY.checkedIn}`;
}

/** What can be refused about a typed code, said under the box. */
export const TYPED_REFUSALS: Readonly<Record<string, string>> = {
  check_in_code_required: 'Type the six characters under the player’s QR code.',
  code_wrong_length: 'A short code is six characters.',
};

const REFUSALS: Readonly<Record<string, (refusal: CheckInRefusal) => string>> = {
  check_in_code_unknown: () =>
    'No seat on a booked game has this code. Check it against the player’s phone.',
  check_in_code_for_another_day: ({ game }) =>
    game === null
      ? 'This code is for another day.'
      : `This code is for another day: the game is on ${shortDay(game.day)} at ${game.from}.`,
  check_in_code_for_another_club: () => 'This code is for a game at another club.',
  already_checked_in: ({ checkedInAt }) =>
    checkedInAt === null ? 'Already scanned.' : `Already scanned: checked in at ${checkedInAt}.`,
  booking_is_called_off: () => 'This game is called off, so there’s nobody to check in.',
  check_in_is_off: () =>
    'You don’t check players in any more. Switch it on in Raketa settings to scan codes.',
  check_in_code_not_raketa: () => 'That QR code isn’t a Raketa check-in code.',
};

/** **Why a code checked nobody in**, as the desk reads it. */
export function checkInRefusal(refusal: CheckInRefusal): string {
  return REFUSALS[refusal.code]?.(refusal) ?? COMMON_REFUSALS[refusal.code] ?? FALLBACK_REFUSAL;
}
