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

import type { ResultAct } from '../domain/home';
import type { CalledOffReason, ClubCancelReason, HomeStatus } from '../domain/vocabulary';

export const HOME_GAME_COPY = {
  /** The heading over Home's rail, before its count — `homePresentation.gamesHeading`. */
  heading: 'Your games',
  /** The status tag on a card and on the details — the mechanics §14.1's names. */
  status: {
    WAITING_FOR_THE_CLUB: 'Waiting for the club',
    WAITING_FOR_A_PAYMENT: 'Waiting for one payment',
    BOOKED: 'Booked',
    SEAT_OPEN: 'Seat open',
    NEEDS_RESULT: 'Needs result',
    CONFIRM_THE_RESULT: 'Confirm the result',
    COUNTED: 'Counted',
    UNCOUNTED: 'Uncounted',
    NEVER_PLAYED: 'Never played',
    CALLED_OFF: 'Called off',
  } satisfies Readonly<Record<HomeStatus, string>>,
  /** The same words mid-line — the details' second line, *Padel · booked*, and the room's. */
  statusInLine: {
    WAITING_FOR_THE_CLUB: 'waiting for the club',
    WAITING_FOR_A_PAYMENT: 'waiting for one payment',
    BOOKED: 'booked',
    SEAT_OPEN: 'seat open',
    NEEDS_RESULT: 'needs result',
    CONFIRM_THE_RESULT: 'confirm the result',
    COUNTED: 'counted',
    UNCOUNTED: 'uncounted',
    NEVER_PLAYED: 'never played',
    CALLED_OFF: 'called off',
  } satisfies Readonly<Record<HomeStatus, string>>,
  /** A game that filled since the player last looked, until its details are opened. */
  new: 'New',
  newSpoken: 'new',
  openGame: 'Open game',
  /** The money line's words (§14.1). */
  money: {
    paid: 'Paid',
    /** *27,18 zł back if you leave by Fri 16:00* — after the sum the read gives (Q99). */
    backIfYouLeaveBy: 'back if you leave by',
    nobodyPaysUntil: 'Nobody pays until',
    confirms: 'confirms',
    theClub: 'the club',
    /** After *Bonarka answers by 20:45 ·* — the club named once already (Q98). */
    nobodyPaysUntilItConfirms: 'Nobody pays until it confirms',
    seatOpen: 'seat open',
    seatsOpen: 'seats open',
    fillsBy: 'fills by',
    orTheGameIsOff: 'or the game is off and everyone is refunded',
    offeredToOthers: 'offered to others',
    goesAhead: 'the game goes ahead',
    /**
     * A full game gone back to filling (Q106): *1 seat open · Kazimierz Padel is asked again when
     * it's full · nobody paid*, or *books when it's full* at a club that books at once.
     */
    askedAgain: 'is asked again when it’s full',
    booksWhenFull: 'books when it’s full',
    /** The same words mid-line, closing that one. */
    nobodyPaidInLine: 'nobody paid',
    refunded: 'Refunded',
    nobodyPaid: 'Nobody paid',
    /** After the club's no or its silence (Q105): the notice's and the email's words. */
    nobodyPaidNewCardFirst: 'Nobody paid — you’ll get a new card first',
    /**
     * Why a game is off (§14.1, #543, #544, #624, #625) — the club's three read with its name before
     * them (`homePresentation`'s `SAID_OF_THE_CLUB`); the rest said of the game. The club's no and its
     * silence, and a payment not in time, are the notice's and the email's words (Q105). Keyed by the
     * wire's reason, so a reason with no words fails here.
     */
    calledOff: {
      SHORT_AT_THE_CUT_OFF: 'A seat was still empty at the cut-off',
      REFUSED: 'said no',
      NO_ANSWER: 'didn’t answer in time',
      CANCELLED_BY_THE_CLUB: 'cancelled it',
      BOOK_BY_PASSED: 'A seat was open past its last moment to book',
      COURT_HOUR_LOST: 'Its court went to another game before it filled again',
      PAYMENT_NOT_IN_TIME: 'A payment didn’t go through in time',
    } satisfies Readonly<Record<CalledOffReason, string>>,
    /**
     * Why the club cancelled (#547; the mechanics §16.9) — the clause after *cancelled it*. *Other*
     * is no reason given, and nothing is said in its place.
     */
    clubCancelled: {
      WEATHER: 'because of the weather',
      REPAIR: 'for a court repair',
      DOUBLE_BOOKING: 'after a double booking',
      OTHER: undefined,
    } satisfies Readonly<Record<ClubCancelReason, string | undefined>>,
    /** *The club* at the head of a sentence, for a club the read no longer names. */
    theClubLead: 'The club',
    /** *Uncounted · a seat was empty* (§14.1): no Level moved, and nobody who stayed is marked. */
    seatEmpty: 'A seat was empty',
    noLevelMoved: 'no Level moved',
    /** *Uncounted* because somebody didn't come (#560) — to the player marked, and to the rest. */
    youWereMarked: 'You were marked as not coming',
    sayIfYouWere: 'say so if you were there',
    somebodyDidNotCome: 'Somebody didn’t come',
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
    nobodyPaid: 'nobody paid',
    nobodyPaidNewCardFirst: 'nobody paid — you’ll get a new card first',
    showAtTheDesk: 'Show at the desk',
    deskLine: 'Show this at the club’s desk when you arrive — or read them the code.',
    qrSpoken: 'Your check-in code as a QR code',
    codeSpoken: 'Your check-in code',
    /** Today's result act, once the hour has come — the button under the game card. */
    resultAct: {
      'we-played': WE_PLAYED,
      confirm: 'Confirm the result',
      /** The marked player's door to their dispute (#560), named for what they go there to do. */
      dispute: 'Say you were there',
    } satisfies Readonly<Record<ResultAct, string>>,
    reading: 'Reading the game',
    gone: 'This game isn’t one of yours any more.',
    /** A rescue opened from a card or a row, whose seat has gone — taken, or off (#557). */
    seatGone: 'This seat isn’t offered to you any more.',
    noRoom: 'This game’s chat isn’t open.',
    findingRoom: 'Opening the chat',
  },
  /**
   * ***Leave the game*** (the mechanics §13; #557) — the line under the button for the moment, the
   * sheet's words (today's *Before you leave* sheet, `LeaveSheet`), the toast once it
   * is done, and the route's three refusals. The sentences carrying a sum are `homePresentation.ts`.
   */
  leave: {
    nobodyPaidYet: 'Nobody has paid yet',
    offered: 'Your seat is offered to others.',
    onRecordIfCalledOff: 'On your record only if the game is then called off.',
    onRecordIfNobody: 'On your record if nobody takes it.',
    withdrawsYourYes: 'Leaving withdraws your yes.',
    left: 'You left the game.',
    refundTakes: 'BLIK within hours, cards up to two weeks.',
    yesWithdrawn: 'Your yes is withdrawn.',
    refused: {
      game_has_started: 'The game has started, so there’s nothing to leave now.',
      booking_is_called_off: 'This game is off, so there’s nothing to leave.',
      booking_not_found: 'You don’t hold a seat on this game any more.',
    },
  },
} as const;
