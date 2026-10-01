/**
 * **Every fixed word Home's booked cards and a booked game's details say**
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, A8; the mechanics
 * §14.1) — copy is code, keyed by the wire's own status so a status with no words fails to compile.
 *
 * Import-light, as `proposalsCopy.ts` is, because the shell composes Home at module load. Taken
 * from the mocks (details 5–10) and the mechanics' table, their names, prices and dates read as mock
 * data — none of it is here. *We played* is `theActsWords`' one spelling; *Confirm the result* is
 * the Classic card's own word, said again because the act behind it is the same screen.
 */

import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';

import type { HomeStatus } from '../domain/vocabulary';

export const HOME_GAME_COPY = {
  /** The status tag on a card and on the details — the mechanics §14.1's names. */
  status: {
    WAITING_FOR_THE_CLUB: 'Waiting for the club',
    BOOKED: 'Booked',
    SEAT_OPEN: 'Seat open',
    NEEDS_RESULT: 'Needs result',
    CONFIRM_THE_RESULT: 'Confirm the result',
    COUNTED: 'Counted',
    UNCOUNTED: 'Uncounted',
    NEVER_PLAYED: 'Never played',
    CALLED_OFF: 'Called off',
  } satisfies Readonly<Record<HomeStatus, string>>,
  /** A game that filled since the player last looked, until its details are opened. */
  new: 'New',
  newSpoken: 'new',
  openGame: 'Open game',
  /** The card's bubble, spoken — it says the chat is open, and is not a door (A8). */
  chatOpen: 'chat open',
  /** The money line's words (§14.1). */
  money: {
    paid: 'Paid',
    freeToLeaveUntil: 'free to leave until',
    nobodyPaysUntil: 'Nobody pays until',
    confirms: 'confirms',
    theClub: 'the club',
    seatOpen: 'seat open',
    seatsOpen: 'seats open',
    fillsBy: 'fills by',
    orTheGameIsOff: 'or the game is off and everyone is refunded',
    offeredToOthers: 'offered to others · the game goes ahead',
    refunded: 'Refunded',
    nobodyPaid: 'Nobody paid',
  },
  details: {
    back: 'Back',
    /** The top bar's door into the room (details 7). */
    chat: 'Chat',
    where: 'Where',
    day: 'Day',
    time: 'Time',
    /** The money row's label: what was taken, or what will be. */
    paid: 'Paid',
    yourShare: 'Your share',
    refunded: 'Refunded',
    toTheClub: 'your share · to the club',
    nobodyPaid: 'nobody paid',
    showAtTheDesk: 'Show at the desk',
    deskLine: 'Show this at the club’s desk when you arrive — or read them the code.',
    qrSpoken: 'Your check-in code as a QR code',
    codeSpoken: 'Your check-in code',
    wePlayed: WE_PLAYED,
    confirmTheResult: 'Confirm the result',
    reading: 'Reading the game',
    gone: 'This game isn’t one of yours any more.',
    noRoom: 'This game’s chat isn’t open.',
    findingRoom: 'Opening the chat',
  },
} as const;
