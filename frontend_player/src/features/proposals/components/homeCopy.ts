/**
 * **Every fixed word Home's booked cards and a booked game's details say**
 * ([#556](https://github.com/Rakieta02/Rakieta/issues/556); the screens A4.1, A8; the mechanics
 * §14.1) — copy is code, keyed by the wire's own status so a status with no words fails to compile.
 *
 * Import-light, as `proposalsCopy.ts` is, because the shell composes Home at module load. Taken
 * from the mocks (details 5–10) and the mechanics' table, their names, prices and dates read as mock
 * data — none of it is here. *We played* is `theActsWords`' one spelling; *Confirm the result* is
 * the Classic card's own word, said again because the act behind it is the same screen.
 */

import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';

import type { ResultAct, ShownStatus } from '../domain/home';
import type { CalledOffReason, ClubCancelReason } from '../domain/vocabulary';

export const HOME_GAME_COPY = {
  /** The heading over Home's rail, before its count — `homePresentation.gamesHeading`. */
  heading: 'Your games',
  /**
   * The status tag on a card and on the details — the mechanics §14.1's names, *Played · no score*
   * in *Never played*'s place (#655), and *Played* for a For fun game after its hour (#656).
   */
  status: {
    WAITING_FOR_A_PAYMENT: 'Waiting for one payment',
    BOOKED: 'Booked',
    SEAT_OPEN: 'Seat open',
    NEEDS_RESULT: 'Needs result',
    CONFIRM_THE_RESULT: 'Confirm the result',
    COUNTED: 'Counted',
    UNCOUNTED: 'Uncounted',
    PLAYED_NO_SCORE: 'Played · no score',
    PLAYED: 'Played',
    CALLED_OFF: 'Called off',
  } satisfies Readonly<Record<ShownStatus, string>>,
  /** The same words mid-line — the details' second line, *Padel · booked*, and the room's. */
  statusInLine: {
    WAITING_FOR_A_PAYMENT: 'waiting for one payment',
    BOOKED: 'booked',
    SEAT_OPEN: 'seat open',
    NEEDS_RESULT: 'needs result',
    CONFIRM_THE_RESULT: 'confirm the result',
    COUNTED: 'counted',
    UNCOUNTED: 'uncounted',
    PLAYED_NO_SCORE: 'played · no score',
    PLAYED: 'played',
    CALLED_OFF: 'called off',
  } satisfies Readonly<Record<ShownStatus, string>>,
  /** A game that filled since the player last looked, until its details are opened. */
  new: 'New',
  newSpoken: 'new',
  openGame: 'Open game',
  /** A called-off game's card, removed from this phone's Home (the bug report's P2). */
  removeGame: 'Remove from Home',
  /** The money line's words (§14.1). */
  money: {
    paid: 'Paid',
    /** *30 zł · free to leave until Fri 16:00* — the club's cut-off, before which nothing is taken (Q113). */
    freeToLeaveUntil: 'free to leave until',
    seatOpen: 'seat open',
    seatsOpen: 'seats open',
    fillsBy: 'fills by',
    orTheGameIsOff: 'or the game is off and nothing is taken',
    offeredToOthers: 'offered to others',
    goesAhead: 'the game goes ahead',
    /** A full game gone back to filling (Q106): *1 seat open · books when it's full · nobody paid*. */
    booksWhenFull: 'books when it’s full',
    /** The same words mid-line, closing that one. */
    nobodyPaidInLine: 'nobody paid',
    refunded: 'Refunded',
    nobodyPaid: 'Nobody paid',
    /** The shares were held and let go — short at the cut-off, or the club's cancel before it (Q113). */
    nothingWasTaken: 'Nothing was taken',
    /**
     * Why a game is off (§14.1, #544, #624, #625) — the club's cancel read with its name before it
     * (`homePresentation`'s `SAID_OF`), and a friends game's sender with theirs; the rest said of the game. A payment not in time is
     * the notice's and the email's words. Keyed by the wire's reason, so a reason with no words
     * fails here.
     */
    calledOff: {
      SHORT_AT_THE_CUT_OFF: 'A seat was still empty at the cut-off',
      CANCELLED_BY_THE_CLUB: 'cancelled it',
      BOOK_BY_PASSED: 'A seat was open past its last moment to book',
      COURT_HOUR_LOST: 'Its court went to another game before it filled again',
      PAYMENT_NOT_IN_TIME: 'A payment didn’t go through in time',
      /** A friends game its sender called off (#759) — said of the sender, named before it. */
      BY_THE_SENDER: 'called it off',
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
    /**
     * *Uncounted* because somebody didn't come (#658) — and, while a late *I was there* waits on the
     * reader, theirs to say or somebody else's to confirm, what to do about it.
     */
    somebodyDidNotCome: 'Somebody didn’t come',
    sayWhoWasThere: 'say who was there',
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
    /**
     * When the share is held and when it is taken (Q113; the screens A4.1): *28 zł* over *Held on
     * your card · taken Sat 10:00 · free to leave until then*, or for a share only checked, *Held
     * from Tue 10:00 · taken Sat 10:00*. The times are `homePresentation`'s.
     */
    heldOnYourCard: 'Held on your card',
    heldFrom: 'Held from',
    taken: 'taken',
    freeToLeaveUntilThen: 'free to leave until then',
    nobodyPaid: 'nobody paid',
    nothingWasTaken: 'nothing was taken',
    /** Today's result act, once the hour has come — the button under the game card. */
    resultAct: {
      /** The first half hour's door (#658): who isn't here yet, and *I'm here*. */
      'whos-here': 'Who’s here',
      'we-played': WE_PLAYED,
      /** A For fun game's door (#656): a score may be added, and nobody is asked for one. */
      'add-score': 'Add the score',
      confirm: 'Confirm the result',
      /**
       * The late claim's door (#658), named for what both its readers go there to do — the absent
       * player to say *I was there*, a courtmate to confirm it.
       */
      'who-was-there': 'Say who was there',
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
   * sheet's words (today's *Before you leave* sheet, `LeaveSheet`), the toast once it is done, and
   * the route's three refusals. Before the cut-off nothing is taken (Q113); after it, the exact
   * refund the read quotes, or no figure and no clause while it quotes none — never an estimate (#644).
   */
  leave: {
    /**
     * The sheet's clause after the cut-off, with the read's figure: *If someone takes it, you get
     * 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*. It opens after the seat offered,
     * and closes *; if nobody does, you won't.*
     */
    ifSomeoneTakesIt: 'If someone takes it, you get',
    back: 'back',
    lessThe: 'less the',
    keptOnYourPayment: 'kept on your payment',
    ifNobodyDoes: 'if nobody does, you won’t.',
    nobodyPaidYet: 'Nobody has paid yet',
    /** The sheet's first line before the cut-off, while the share is held on the card. */
    holdLetGo: 'Nothing is taken: the hold on your card is let go.',
    /** …while it is only checked, which holds nothing until its holding time. */
    nothingTaken: 'Nothing is taken.',
    /** The sheet's, and the line's after the cut-off while the read quotes no figure — no clause. */
    offered: 'Your seat is offered to others',
    onRecordIfCalledOff: 'On your record only if the game is then called off.',
    onRecordIfNobody: 'On your record if nobody takes it.',
    withdrawsYourYes: 'Leaving withdraws your yes.',
    left: 'You left the game.',
    nothingWasTaken: 'Nothing was taken.',
    yesWithdrawn: 'Your yes is withdrawn.',
    refused: {
      game_has_started: 'The game has started, so there’s nothing to leave now.',
      booking_is_called_off: 'This game is off, so there’s nothing to leave.',
      booking_not_found: 'You don’t hold a seat on this game any more.',
    },
  },
} as const;
