/**
 * **The friends card's and *Find a court*'s fixed words** — the words
 * [§29.6](../../../../../docs/specs/matchmaking/the-words.md#296-the-friends-tab)
 * ([#757](https://github.com/Raketa02/Raketa/issues/757)). The sentences built from a value are
 * `friendsCardPresentation.ts`'s; the deck card's own words — the *vs* line, the balance, the
 * overlap's grade — are `proposalsCopy`'s, cited, because the friends card is the deck's card
 * without its tiles.
 *
 * ## Calls, for the product owner to overrule
 *
 * §29.6 gives every drawn word here but these, written in by #757:
 *
 * - **`no_level` and `not_a_friend` in the card's place** (the mechanics §7.5 gives each its own
 *   line and §29 none): *Somebody here has no padel level yet. Swap someone.* and *Somebody here
 *   isn't your friend any more. Seat someone else.* — names nobody, as the blocked pair's does.
 * - **The card while it is read** (the screens §7.2, *designed, no mock*): *Finding the evenest
 *   sides and a court…*, quiet, in the card's frame, the button hidden.
 * - **The spoken names**: *Close Find a court* for the sheet's close, and *picked* on the row the card
 *   shows.
 */

export const FRIENDS_CARD_COPY = {
  /** The court panel's tag — the deck's *Court available*, on a court the send books at once. */
  courtAvailable: 'Court available',
  pickACourt: 'Pick a different court',
  pickACourtHint: 'Opens every court the four of you could take',
  building: 'Finding the evenest sides and a court…',
  noCourt: 'No court is free in the next 14 days.',
  refused: {
    blockedDoubles: 'These four can’t all play together. Swap someone.',
    blockedSingles: 'These two can’t play together. Swap someone.',
    notAFriend: 'Somebody here isn’t your friend any more. Seat someone else.',
  },
  findACourt: {
    title: 'Find a court',
    close: 'Close Find a court',
    reading: 'Reading every court…',
    everybodyFree: 'Everybody free',
    youAreBusy: 'You’re busy',
    picked: 'picked',
    rowHint: 'Puts this court on the card',
  },
} as const;
