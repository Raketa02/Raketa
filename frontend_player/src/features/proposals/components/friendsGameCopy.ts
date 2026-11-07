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
 * - **The sender's own Whole-court pay mode**: *You paid the court* (§29.8 gives the nickname's).
 * - **The seats line with both waiting and empty seats**: *1 of 3 friends in · waiting for ania.k ·
 *   1 seat empty* — §29.8 gives each half alone.
 * - **A friend's Whole-court Home line**: *tomek.k paid the court · free to leave until Fri 10:00*.
 * - **Calling it off's outcomes**: done, the toast *Called off — nobody paid.*; refused after the
 *   cut-off, *The club's cut-off has passed, so it can't be called off for free.* #759's own
 *   confirmation, *Call it off?* · **Keep the game**, went with its button: calling it off is the
 *   sender's leave sheet's (2026-11-07, below).
 *
 * And these, written in by [#760](https://github.com/Raketa02/Raketa/issues/760):
 *
 * - **A friend invited into an empty seat**, under it: *piotr.s invited · 20 h 00 left* — the
 *   read's own example; *A friend invited · …* for one it cannot name.
 * - **Each action aloud names its seat**: *Invite a friend, bartek.l's seat* — the details may hold
 *   two empty seats.
 * - **Opening's close and its outcomes**: *Close — the seat stays as it is*; done, *Seat open —
 *   anyone in Ogrody who fits can take it.*; refused at the cut-off, *The cut-off has passed, so
 *   the seat opened to the group on its own.*; *Open to the group* for a group the app cannot name.
 * - **The one-seat picker's order**: *Invite piotr.s* once a friend is picked, *Invite a friend*
 *   greyed before; done, *Invitation sent to piotr.s.*; each refusal names the friend picked and
 *   never who blocked whom (*piotr.s can't play with everyone on this game. Pick someone else.*).
 *   **Everybody already on the game is left out of it** — the server would refuse each
 *   `already_on_the_game` — and with nobody left, *Nobody else to invite. Add friends from your
 *   groups, or send your link.*
 * - **The sender's leave sheet**: its two choices are the sheet's answers with their lines as
 *   glosses, its close *Stay in*, as the ordinary sheet's; done, *You left — the others play on,
 *   and you pay nothing.* (Split) or *You left — the others play on. You still pay the court.*
 *   (Whole court). **The Split line is #760's acceptance criterion**, *You pay nothing. Your
 *   friends keep the court; a seat still empty on Fri 10:00 calls the game off and nobody pays.*,
 *   where §29.10 says *Your card stops covering the game. …* — the ticket's, the later of the two.
 *
 * And one ruled by the product owner on 2026-11-07, after #760:
 *
 * - **The sender's door before the cut-off reads *Leave or call it off*** — the one way to either,
 *   the separate *Call it off* beside it removed — and *Leave the game* again from the cut-off on,
 *   when only the ordinary late leave is left. The sheet's title stays *Before you leave*, and
 *   neither choice asks again: the sheet is the deliberate step.
 */

import type { PayMode } from '../domain/vocabulary';

/** *Someone took that seat first.* — §29.8's *seat taken*, said where an invitation or opening finds it gone. */
const SEAT_TAKEN = 'Someone took that seat first.';

export const FRIENDS_GAME_COPY = {
  /** A seat the court can no longer name, in a sentence — never drawn blank. */
  somebody: 'Somebody',
  /** A sender the read can no longer name, at a sentence's head (*The sender called it off*). */
  theSender: 'The sender',
  you: 'You',
  send: {
    title: 'How to pay',
    close: 'Close — nothing is sent',
    /** The choice cards' titles, keyed by the wire's pay mode. */
    payMode: {
      SPLIT_THE_COST: 'Split the cost',
      WHOLE_COURT: 'Pay the whole court',
    } satisfies Readonly<Record<PayMode, string>>,
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
    /** How a face is spoken, by where it stands: *tomek.k, in*, *ania.k, still to answer*. */
    in: 'in',
    stillToAnswer: 'still to answer',
    refused: {
      invitation_not_waiting: 'That invitation has ended.',
    },
  },
  seats: {
    heading: 'Seats',
    /** The pay mode's own word under the price, with Split (§29.8). */
    split: 'Split',
    state: {
      IN: 'In',
      CANT_MAKE_IT: 'can’t make it',
      DIDNT_ANSWER: 'didn’t answer',
      EMPTY: 'empty',
      SEAT_OPEN: 'Seat open',
    },
    /** A friend invited into an empty seat the read cannot name. */
    aFriend: 'A friend',
    invite: 'Invite a friend',
  },
  /** *Open to {group}* and its confirmation (§29.9); the sentences with the group are built. */
  open: {
    theGroup: 'the group',
    notYet: 'Not yet',
    close: 'Close — the seat stays as it is',
    opening: 'Opening…',
    refused: {
      cut_off_has_passed: 'The cut-off has passed, so the seat opened to the group on its own.',
      seat_just_taken: SEAT_TAKEN,
    },
  },
  /** The one-seat picker's order — *Invite piotr.s*, built — and the refusals it says. */
  invite: {
    inviting: 'Inviting…',
    nobody: 'Nobody else to invite. Add friends from your groups, or send your link.',
    refused: {
      seat_just_taken: SEAT_TAKEN,
      booking_is_called_off: 'This game is called off.',
      game_has_started: 'This game has started.',
    },
  },
  /**
   * The sender's leave sheet before the cut-off (§29.10), on the ordinary sheet's title and close —
   * the one door to calling it off as well as to leaving.
   */
  sendersLeave: {
    /** The door's label, naming both ways behind it (the product owner, 2026-11-07). */
    door: 'Leave or call it off',
    callOff: 'Call it off for everyone',
    playOn: 'Leave · the others play on',
    calling: 'Calling it off…',
    leaving: 'Leaving…',
    /** The toast once it is called off. */
    calledOff: 'Called off — nobody paid.',
    /** The toast once the sender has left and the others play on, by the pay mode (a call). */
    left: {
      SPLIT_THE_COST: 'You left — the others play on, and you pay nothing.',
      WHOLE_COURT: 'You left — the others play on. You still pay the court.',
    } satisfies Readonly<Record<PayMode, string>>,
    /** Why calling it off was refused — its own two; any other code is the deck's sentence. */
    refused: {
      cut_off_has_passed: 'The club’s cut-off has passed, so it can’t be called off for free.',
      booking_is_called_off: 'It’s already called off.',
    },
  },
} as const;
