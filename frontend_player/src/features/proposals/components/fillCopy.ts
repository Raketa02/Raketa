/**
 * **Every fixed word the moment a game fills says** — the Undo toast, *It's a game!*, a payment
 * that did not go through and the confirmation that keeps the seat
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4, A9; the mechanics
 * §6.5, §11, §12.2).
 *
 * Import-free, as `proposalsCopy.ts` is: the shell mounts the fill for the whole session, so this is
 * read at module load. The sentences composed from a value are `fillPresentation.ts`.
 */

export const FILL_COPY = {
  undo: {
    /** The button. */
    action: 'Undo',
    /** The button, spoken — what it undoes. */
    actionSpoken: 'Undo the booking',
    /** *I'm in* on a game's details while its yes counts down. */
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
   * A game booked with no faces to draw — a confirmation from You › Payments, which holds no card, or
   * a row's join whose booking could not be read.
   */
  itsAGameInHome: 'It’s a game! You’ll find it in Home.',
  /** The toast at the fill, and the notice of the same name (A9). */
  paymentFailed: 'Your payment didn’t go through — confirm it to keep your seat',
  /** A card whose bank moved it to another brand cannot be charged until the terms are accepted. */
  termsAgain: 'Your card needs the terms again — accept them in You › Payments, then say yes.',
  confirm: {
    title: 'Confirm your payment',
    close: 'Close — your seat stays open until you confirm',
    reading: 'Reading your payment…',
    /** A payment this build cannot draw — a sport it does not know. */
    unreadable: 'This payment can’t be shown here. Update Raketa to confirm it.',
    readAgain: 'Try again',
    /** The bank wants the player present. */
    checkLine: 'Your bank wants to check this payment once before the club can take it.',
    check: 'Confirm with your bank',
    /** The card on file was declined. */
    declinedLine: 'Your bank declined the card on file. Pay this share with another card.',
    payWithCard: 'Pay with this card',
    cardFields: {
      label: 'Card number, expiry date and security code',
      placeholders: { number: '1234 1234 1234 1234', expiry: 'MM/YY', cvc: 'CVC' },
    },
    confirming: 'Confirming…',
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
  /** You › Payments' *TO CONFIRM* — the way back to a seat whose share was refused. */
  toConfirm: {
    title: 'To confirm',
    line: 'Your seat stays open until you confirm — or someone else takes it.',
    action: 'Confirm',
  },
} as const;
