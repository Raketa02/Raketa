/**
 * What a challenge **is**, at the instant it was read — five codes, and no more.
 *
 * *"**Challenge sent** and **Challenge for you** are one standing read from two sides, not two
 * states"* ([#221](https://github.com/Raketa02/Raketa/issues/221)): the code is one and the
 * sentence is two, and which one a reader gets is decided by whether they hold the organiser
 * seat.
 *
 * **Six, not twenty.** The prototype's twenty card states are *"a presentation vocabulary
 * spanning money, booking and results this context does not own"*, and an unknown standing
 * takes the out-of-date gap rather than a shorter list
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §13).
 *
 * **`WITHDRAWN` is the sixth and it is the one the seats cannot reach**
 * ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)):
 * every other code is a fold of the seats and the clock, and this one is an act. It is
 * neither a decline nor a lapse, and its word is the record's own — not *cancel* or *call
 * off*, which belong to the plan, and not *stand down*, which the root `CONTEXT.md` owns
 * platform-wide for a term that cannot be evaluated.
 *
 * The standing is **derived from the seats and the clock and never stored**, so it is right
 * for the whole gap between a deadline and anything noticing — which is also why nothing on
 * this side computes one.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

export const STANDINGS = [
  'AWAITING_ANSWERS',
  'ON',
  'LINE_UP_INCOMPLETE',
  'DECLINED',
  'LAPSED',
  'WITHDRAWN',
] as const;

export type Standing = (typeof STANDINGS)[number];

/**
 * Which side of the challenge the reader is on.
 *
 * Derived from whether `organiser_id` is theirs — one list, never two, so nothing on the wire
 * carries a side and nothing here asks for one.
 */
export type ChallengeSide = 'organiser' | 'invitee';

/**
 * What the person in a seat did about being asked — **three values, and *awaiting* is not one
 * of them.**
 *
 * The absence of an answer *is* awaiting, and giving it a name would make *nothing yet* and
 * `AWAITING` two spellings of one state with nothing to choose between them.
 *
 * **`LAPSED` is never a decline.** They do the same thing to the line-up and they are
 * different facts — the `answers challenges` strand counts challenges that got an answer
 * inside their window, and it is unmeasurable if silence is filed as judgement.
 */
export const SEAT_ANSWERS = ['ACCEPTED', 'DECLINED', 'LAPSED'] as const;

export type SeatAnswer = (typeof SEAT_ANSWERS)[number];

/**
 * One standing, with the payload its sentence quotes.
 *
 * A discriminated fold rather than `(standing, side, counts)`: four of the six quote a
 * figure or a name, two quote nothing, and a flat signature would let a caller pass a count
 * that belongs to a different standing.
 *
 * **A person is a `NamedPlayer`, never a string.** Four of these sentences name somebody, and
 * ADR-0107's *the whole handle or nobody* is a rule about what may be written — a `name:
 * string` parameter would let a caller shorten a handle on the way in and leave the rule
 * documented rather than held.
 *
 * **It is `domain/` because it is a fold and not a table.** The words are
 * `components/challengePresentation.ts`'s; what is here is the reading a caller could get
 * *wrong* — which seat is the reader's, how many are open, and which of the people on the
 * court a sentence names. That distinction was paid for once already: the shipped line counted
 * *"still to answer"* in the one standing where nothing ever is.
 */
export type StandingFacts = { readonly side: ChallengeSide } & (
  | { readonly standing: 'AWAITING_ANSWERS'; readonly awaiting: number }
  | { readonly standing: 'ON' }
  | {
      readonly standing: 'LINE_UP_INCOMPLETE';
      readonly accepted: number;
      /**
       * Seats with nobody in them — **never a count of who has yet to answer**, which in this
       * standing is nobody by construction.
       */
      readonly open: number;
      /**
       * What the **reader's own seat** says, where the reader is an invitee who has left.
       *
       * Absent means they are in, which is the sentence that shipped. `ACCEPTED` is the same
       * thing said explicitly. The other two are §13.1's third reading, and the field exists
       * because a side alone cannot tell them apart. Ignored on the organiser's own row: their
       * seat is accepted from birth and they are the one asking.
       */
      readonly ownAnswer?: SeatAnswer;
    }
  | { readonly standing: 'DECLINED'; readonly player: NamedPlayer }
  | { readonly standing: 'LAPSED'; readonly player: NamedPlayer }
  | { readonly standing: 'WITHDRAWN'; readonly player: NamedPlayer }
);
