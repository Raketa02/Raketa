/**
 * **Every fixed word the moment a game fills says** — the Undo toast, *It's a game!*, a payment
 * that did not go through and the confirmation that keeps the seat
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4, A9; the mechanics
 * §6.5, §11, §12.2).
 *
 * Import-free but for types, as `proposalsCopy.ts` is: the shell mounts the fill for the whole
 * session, so this is read at module load. The sentences composed from a value are
 * `fillPresentation.ts`.
 */

import type { PaymentWindow, SeatAtStake } from '../domain/home';

/** Words that differ by the window the read names (Q113): a `Record` over it, so none goes unsaid. */
type ByWindow = Readonly<Record<PaymentWindow, string>>;

export const FILL_COPY = {
  undo: {
    /** The button. */
    action: 'Undo',
    /** The button, spoken — what it undoes. */
    actionSpoken: 'Undo the booking',
    /** A *Pay 32 zł* button while its yes counts down — on a game's details, and a rescue's. */
    booking: 'Booking…',
    /** A second yes that would move money, while one counts already. */
    oneAtATime: 'One booking at a time — undo this one or let it go through first.',
  },
  itsAGame: {
    /** The one lime word (A2.4) — the yes screen's, for a yes that filled a game. */
    word: 'It’s a game!',
    open: 'Open game',
    later: 'Later',
  },
  /**
   * A game booked with no faces to draw — a confirmation from a *TO CONFIRM* row, or a row's join,
   * whose booking could not be read.
   */
  itsAGameInHome: 'It’s a game! You’ll find it in Home.',
  /**
   * **The toast at a refused card** (the screens A2.4), keyed by the window the read names (Q113):
   * before the club's cut-off nothing is being taken, so it is the card to fix — *written in while
   * recording Q113* — and after it the payment to confirm. On a rescue the seat is kept for them to
   * take, not yet theirs (#640), the notice's own words.
   */
  refused: {
    yours: {
      FIX_THE_CARD: 'Your card didn’t go through — fix it to keep your seat. Nothing is paid now.',
      PAY: 'Your payment didn’t go through — confirm it to keep your seat',
      UNNAMED: 'Your payment didn’t go through — confirm it to keep your seat',
    } satisfies ByWindow,
    aRescue: {
      FIX_THE_CARD: 'Your card didn’t go through — fix it to take the seat. Nothing is paid now.',
      PAY: 'Your payment didn’t go through — confirm it to take the seat',
      UNNAMED: 'Your payment didn’t go through — confirm it to take the seat',
    } satisfies ByWindow,
  } satisfies Readonly<Record<SeatAtStake, ByWindow>>,
  /** A card whose bank moved it to another brand cannot be charged until the terms are accepted. */
  termsAgain: 'Your card needs the terms again — accept them in You › Payments, then say yes.',
  /**
   * **The confirmation** — its words keyed by the window the read names (Q113): before the cut-off
   * the card is fixed and the hold only placed again, never paid; after it the payment is confirmed
   * (#630's words). With no window named — a time run out, or an older server — the words never say
   * *pay*: a seat taken back before the cut-off is held, not paid.
   */
  confirm: {
    title: {
      FIX_THE_CARD: 'Fix your card',
      PAY: 'Confirm your payment',
      UNNAMED: 'Confirm your payment',
    } satisfies ByWindow,
    close: 'Close — your seat stays open until you confirm',
    reading: 'Reading your payment…',
    /** A payment this build cannot draw — a sport it does not know. */
    unreadable: 'This payment can’t be shown here. Update Rakieta to confirm it.',
    /** The card fields wait on Stripe's start; when it cannot start, nothing is drawn in its place. */
    providerNotStarted: 'Card payments couldn’t start on this phone. Try again in a moment.',
    readAgain: 'Try again',
    /** The bank wants the player present. */
    checkLine: {
      FIX_THE_CARD: 'Your bank wants you to confirm the hold on your card yourself.',
      PAY: 'Your bank wants to check this payment once before the club can take it.',
      UNNAMED: 'Your bank wants to check this payment once before the club can take it.',
    } satisfies ByWindow,
    check: 'Confirm with your bank',
    /** The card on file was declined. */
    declinedLine: {
      FIX_THE_CARD: 'Your bank declined the hold on the card on file. Fix it with another card.',
      PAY: 'Your bank declined the card on file. Pay this share with another card.',
      UNNAMED: 'Your bank declined the card on file. Use another card for this share.',
    } satisfies ByWindow,
    withThisCard: {
      FIX_THE_CARD: 'Use this card',
      PAY: 'Pay with this card',
      UNNAMED: 'Use this card',
    } satisfies ByWindow,
    /**
     * Under the time to fix the card — the mechanics §12.2's *nothing is paid now and the hold is only
     * placed again* (Q113), true of a card check run again as of a hold.
     */
    onlyPlacedAgain: 'Nothing is paid now — fixing your card only places the hold again.',
    cardFields: {
      label: 'Card number, expiry date and security code',
      placeholders: { number: '1234 1234 1234 1234', expiry: 'MM/YY', cvc: 'CVC' },
    },
    confirming: 'Confirming…',
    /**
     * After *Confirm your payment by 14:40* — the seat the payer's time keeps (Q109), the notice's and
     * the email's words: their own, or on a rescue the seat kept for them alone to take, until then
     * and never past the start (#640).
     */
    toSeat: {
      yours: 'to keep your seat',
      aRescue: 'to take the seat',
    } satisfies Readonly<Record<SeatAtStake, string>>,
    keptForYou: 'it’s kept for you until then',
    /** The seat is held again but somebody else's share still stands in the way. */
    kept: 'Payment confirmed — you’re In again.',
    /** What the provider said, when it was not *confirmed*. */
    phone: {
      cancelled: 'The check was closed before your bank finished. Try again.',
      declined: 'Your bank declined this card. Try another one.',
      failed: 'We couldn’t hear back from your bank. Try again.',
    },
    /** The yes again, refused — by the route's own code. */
    refused: {
      payment_not_confirmed: 'Your bank hasn’t confirmed it yet. Try again in a moment.',
      proposal_is_full: 'Someone just took your seat, so nothing was charged.',
      proposal_is_over: 'That game is no longer on, so nothing was charged.',
      seat_charge_not_found: 'This payment isn’t yours to confirm.',
      payments_unavailable: 'Payments can’t be reached right now. Try again in a moment.',
    },
  },
  /**
   * *TO CONFIRM*, on Home and You › Payments — the way back to a seat whose share was refused. A row
   * names the payer's time while it runs (`fillPresentation`'s `toConfirmRowLine`, Q109), and says
   * this once it ran out: the seat is open to others, and theirs to take back while it is free.
   */
  toConfirm: {
    title: 'To confirm',
    open: 'Your seat stays open until you confirm — or someone else takes it.',
    /** The row's button, and its name aloud (*Fix your card for Padel · Saturday 15:00 …*). */
    action: { FIX_THE_CARD: 'Fix', PAY: 'Confirm', UNNAMED: 'Confirm' } satisfies ByWindow,
    spoken: {
      FIX_THE_CARD: 'Fix your card for',
      PAY: 'Confirm your payment for',
      UNNAMED: 'Confirm your payment for',
    } satisfies ByWindow,
    /** Under *Fix your card by 14:40* — the screens A7.3's line that nothing is paid now (Q113). */
    nothingPaidNow: 'Nothing is paid now',
  },
} as const;
