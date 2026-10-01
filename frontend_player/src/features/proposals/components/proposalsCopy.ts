/**
 * **Every fixed word a group's Games deck and a game's details say** — copy is code, and nothing
 * is inlined in a component ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens
 * A2, A4.2).
 *
 * Import-free but for a type, so a screen can read it at module load; the sentences composed from a value are
 * `deckPresentation.ts`, which re-exports this. Taken from the mocks (player 1–10, details 5–10),
 * with their names, prices and dates read as mock data — none of it is here.
 */

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
  in: 'IN',
  inSpoken: 'In',
  /** A booked game's seat whose share was taken — beside the Level (details 8, #556). */
  paid: 'paid',
  versus: 'vs',
  /** The two answers, as the stamps and the buttons say them. */
  yes: 'I’m in',
  no: 'Not this time',
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
    forecast: 'Balance forecast',
    overlap: 'Who is free',
    whatAYesMeans:
      'Your yes costs nothing until everybody is in. When the last yes lands, everyone’s share is charged together and the court is booked.',
    withdraw: 'Withdraw',
    gone: 'This game isn’t dealt to you any more.',
    /**
     * **Where a game still filling stands** (#542, #557) — its details' status tag. *Filling* carries
     * its count (`fillingStatus`); the rest are the four ways it ended unfilled, booked, and the
     * club's turn.
     */
    status: {
      FILLING: 'Filling',
      WAITING_FOR_THE_CLUB: 'Waiting for the club',
      FILLED: 'Booked',
      EXPIRED: 'Didn’t fill in time',
      WITHDRAWN: 'Taken back',
      COURT_HOUR_LOST: 'No court left at that hour',
      TURNED_DOWN: 'The club couldn’t take it',
    } satisfies Readonly<Record<ProposalStatus, string>>,
    /** The same, mid-line — the header's second line, *Padel · filling*. */
    statusInLine: {
      FILLING: 'filling',
      WAITING_FOR_THE_CLUB: 'waiting for the club',
      FILLED: 'booked',
      EXPIRED: 'didn’t fill',
      WITHDRAWN: 'taken back',
      COURT_HOUR_LOST: 'no court left',
      TURNED_DOWN: 'turned down',
    } satisfies Readonly<Record<ProposalStatus, string>>,
    /** The money row's aside while an On request club decides (A4.2). */
    nobodyPaysUntil: 'nobody pays until',
    confirms: 'confirms',
    theClub: 'the club',
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
  },
} as const;
