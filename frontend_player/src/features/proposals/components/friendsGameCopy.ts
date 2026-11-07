/**
 * **A friends game's fixed words** — the send sheet, *FRIENDS GAME · n* on Home, the sender's game in
 * Your games and the details' seats — the words
 * [§29.7–§29.10](../../../../../docs/specs/matchmaking/the-words.md#297-sending)
 * ([#759](https://github.com/Raketa02/Raketa/issues/759)). The sentences built from a value are
 * `friendsGamePresentation.ts`'s; a refusal the deck already words is `proposalsCopy`'s, cited.
 *
 * ## Calls, for the product owner to overrule
 *
 * §29 gives every word here but these, written in by #759:
 *
 * - **The send sheet's title and its close**: *How to pay*, and *Close — nothing is sent*; each
 *   choice card names what its button charges (*25 zł*, *100 zł*) on its right.
 * - **The cover line without a cut-off** (a card read from an older server): *We hold 100 zł on your
 *   card until the club's cut-off. …*
 * - **Sent**: the toast *Game sent — the court is booked. It's in Your games on Home.*
 * - **A court no longer for sale at send**: *That court isn't for sale any more, so nothing was
 *   charged. Here's another.* — the card then proposes one, as it does on its own.
 * - **Accepted, the game not yet whole**: the toast *You're in — it's in Your games.*
 * - **An invitation that no longer waits**: *That invitation has ended.*
 * - **The details' seats**: the eyebrow *SEATS* over one row per seat, *You* for the reader.
 * - **Call it off's confirmation**: *Call it off?*, §29.10's line, **Call it off for everyone** and
 *   **Keep the game**; done, the toast *Called off — nobody paid.*; refused after the cut-off, *The
 *   club's cut-off has passed, so it can't be called off for free.*
 */

export const FRIENDS_GAME_COPY = {
  send: {
    title: 'How to pay',
    close: 'Close — nothing is sent',
    split: 'Split the cost',
    whole: 'Pay the whole court',
    sending: 'Sending…',
    sent: 'Game sent — the court is booked. It’s in Your games on Home.',
    theClubsCutOff: 'the club’s cut-off',
    refused: {
      courtGone: 'That court isn’t for sale any more, so nothing was charged. Here’s another.',
    },
  },
  invitation: {
    notThisTime: 'Not this time',
    accept: 'Accept',
    accepting: 'Accepting…',
    accepted: 'You’re in — it’s in Your games.',
    you: 'You',
    refused: {
      invitation_not_waiting: 'That invitation has ended.',
    },
  },
  seats: {
    heading: 'Seats',
    you: 'You',
    split: 'Split',
    state: {
      IN: 'In',
      CANT_MAKE_IT: 'can’t make it',
      DIDNT_ANSWER: 'didn’t answer',
      EMPTY: 'empty',
    },
  },
  callOff: {
    action: 'Call it off',
    title: 'Call it off?',
    confirm: 'Call it off for everyone',
    keep: 'Keep the game',
    close: 'Close — the game stays on',
    calling: 'Calling it off…',
    done: 'Called off — nobody paid.',
    refused: {
      cut_off_has_passed: 'The club’s cut-off has passed, so it can’t be called off for free.',
      booking_is_called_off: 'It’s already called off.',
    },
  },
} as const;
