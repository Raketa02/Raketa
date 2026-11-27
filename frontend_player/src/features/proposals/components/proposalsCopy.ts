/**
 * **Every fixed word a group's Games deck and a game's details say** — copy is code, and nothing
 * is inlined in a component ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens
 * A2, A4.2).
 *
 * Import-free but for a type, so a screen can read it at module load; the sentences composed from a value are
 * `deckPresentation.ts`, which re-exports this. Taken from the mocks (player 1–10, details 5–10),
 * with their names, prices and dates read as mock data — none of it is here.
 */

import type { RescueGoneReason } from '../domain/deck';
import type { PaymentWindow } from '../domain/home';
import type { ProposalStatus } from '../domain/vocabulary';

export const PROPOSALS_COPY = {
  ribbon: {
    pickedForYou: 'Picked for you',
    groupChallenged: 'The group challenged you',
    seatOpen: 'Seat open · court booked',
  },
  /** The court block's one tag (the screens A2.3). */
  courtTag: {
    available: 'Court available',
    bookItNow: 'Book it now',
    booked: 'Booked',
  },
  noFreeCancellation: 'no free cancellation',
  grade: {
    HIGH: 'High overlap',
    GOOD: 'Good overlap',
    SLIM: 'Slim overlap',
  },
  range: {
    MORNING: 'morning',
    AFTERNOON: 'afternoon',
    EVENING: 'evening',
  },
  /** The grid's column heads, Monday first — letters, as the mocks draw them. */
  dayLetters: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
  today: 'Today',
  tomorrow: 'Tomorrow',
  you: 'You',
  youCompleteIt: 'You complete it',
  /** A rescue's open seat while another is open too (A2.3). */
  youQuestion: 'You?',
  /** Under *You complete it* on a rescue's seat — the share, and that the court is already booked. */
  courtBooked: 'court booked',
  /**
   * A rescue's *Pay 27 zł*, aloud (Q113, Q124; the screens A3.1, A4.3, A5.3) — and the deck's *I'm
   * in* on a *Seat open* card: what the share does — held until the club's cut-off before it, as
   * every seat's is, and taken at once after it.
   */
  heldUntilTheCutOff: 'held until the cut-off',
  paidNow: 'paid now',
  in: 'IN',
  inSpoken: 'In',
  /**
   * **The reader's own friend** — the deck's tile tag in volt (#753; Q68, applying since Q128; the
   * words §29.1), and *friend* where it is spoken and on a Fill in square.
   */
  friend: 'FRIEND',
  friendSpoken: 'friend',
  /** A booked game's seat whose share was taken — beside the Level (details 8, #556). */
  paid: 'paid',
  versus: 'vs',
  /**
   * The two answers, as the stamps and the buttons say them — *I'm in* on a vote and on the deck's
   * ball whatever the card.
   */
  yes: 'I’m in',
  no: 'Not this time',
  /**
   * **A yes that moves money** (Q124) — the stamp's *PAY · 32 zł* on a yes that books at once or
   * takes a seat, and every button that does: *Pay 27 zł*.
   */
  pay: 'Pay',
  details: 'Game details',
  kind: {
    competitive: 'Competitive',
    forFun: 'For fun',
  },
  reading: 'Reading the games',
  readAgain: 'Try again',
  /** A card the server holds no name for — the tile draws the unknown player's mark. */
  unnamed: '?',
  /** The club the card was at, when the read no longer names it. */
  unknownClub: 'A club',
  game: {
    back: 'Back',
    filling: 'Filling',
    where: 'Where',
    day: 'Day',
    time: 'Time',
    share: 'Your share',
    until: 'until',
    nextWeek: 'next week',
    ifItFills: 'if it fills',
    bookBy: 'book by',
    overlap: 'Who is free',
    /** The header's title when nobody else is on the card — said, not left blank. */
    onlyYou: 'Only you',
    withdraw: 'Withdraw',
    gone: 'This game isn’t dealt to you any more.',
    /**
     * **Where a game still filling stands** (#542, #557) — its details' status tag. *Filling* carries
     * its count (`fillingStatus`); the rest are a payment awaited, booked, and the three ways it
     * ended unfilled.
     */
    status: {
      FILLING: 'Filling',
      WAITING_FOR_A_PAYMENT: 'Waiting for one payment',
      FILLED: 'Booked',
      EXPIRED: 'Didn’t fill in time',
      WITHDRAWN: 'Taken back',
      COURT_HOUR_LOST: 'No court left at that hour',
    } satisfies Readonly<Record<ProposalStatus, string>>,
    /**
     * *Waiting for one payment · until 14:40 · Nobody pays until it's in* (Q110, Q111) — one player's
     * share was refused and their time to pay runs, never whose: Home's line, the details' and *It's a
     * game!*'s. *until* is `until`, TIME's own word.
     */
    waitingForOnePayment: 'Waiting for one payment',
    nobodyPaysUntilItsIn: 'Nobody pays until it’s in',
    /**
     * *Confirm your payment by 14:40* — the payer's own time to pay (Q109, Q111); before the club's
     * cut-off, where nothing is taken, *Fix your card by 14:40* (Q113). Keyed by the window the read
     * names; with none named, *confirm*.
     */
    yourTimeBy: {
      FIX_THE_CARD: 'Fix your card by',
      PAY: 'Confirm your payment by',
      UNNAMED: 'Confirm your payment by',
    } satisfies Readonly<Record<PaymentWindow, string>>,
  },
  /**
   * **What a refused answer says** (the screens A2.4) — a toast, and the card springs back or
   * leaves by `refusalOutcome`. Keyed by the route's own code; a code with no words here falls
   * back to the recovery sentence every screen shares.
   */
  refused: {
    payment_method_required: 'A yes needs a saved way to pay first.',
    proposal_is_over: 'That game is no longer on.',
    proposal_already_answered: 'You already answered that game.',
    proposal_is_full: 'That game just filled.',
    no_longer_fits: 'That game changed, and isn’t dealt to you any more.',
    proposal_not_found: 'That game is no longer on.',
    block_state_unavailable: 'That didn’t go through — try again in a moment.',
    /** #541: two cards at one hour raced for the club's last court, twice. Nothing was charged. */
    court_just_taken:
      'That court was just booked by another game. Nothing was charged — try again.',
    payments_unavailable: 'Payments can’t be reached right now, so nothing was booked. Try again.',
    /** #545: the first join wins — said to the second, who paid nothing (A3.1). */
    seat_just_taken: 'Someone just took it.',
    booking_is_called_off: 'That game is off now, so nothing was charged.',
    game_has_started: 'That game has started, so nothing was charged.',
    rescue_not_offered: 'That seat isn’t offered to you any more.',
    booking_not_found: 'That game is no longer on.',
    /** #546: joining a post from *Post a game*'s sheet that dealing would not deal them now. */
    post_not_open_to_you: 'That game isn’t open to you now — nothing was recorded.',
  },
  /** A rescue refused because its booking, or its seat, went while the player reached for it. */
  rescueGone: {
    title: 'This game isn’t available',
    /**
     * Keyed by the reason; the club's cancel is a sentence of its own (`rescueGoneLine`), with the
     * club's reason after it.
     */
    lines: {
      SHORT_AT_THE_CUT_OFF:
        'A seat was still empty at the club’s cut-off, so this game was called off. Nothing was charged.',
      CALLED_OFF: 'This game was called off, so nothing was charged.',
      BOOKING_GONE: 'This game is no longer on, so nothing was charged.',
      SEAT_TAKEN: 'Someone just took this seat, so nothing was charged.',
      GAME_STARTED: 'This game has already started, so nothing was charged.',
      NOT_OFFERED: 'This seat isn’t offered to you any more, so nothing was charged.',
    } satisfies Readonly<Record<Exclude<RescueGoneReason, 'CANCELLED_BY_THE_CLUB'>, string>>,
    /** *The club cancelled this game because of the weather, so nothing was charged.* */
    clubCancelled: {
      opening: 'The club cancelled this game',
      closing: 'so nothing was charged.',
    },
    close: 'Got it',
  },
} as const;
