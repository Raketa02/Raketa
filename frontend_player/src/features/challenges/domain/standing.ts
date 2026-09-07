/**
 * What a challenge **is**, at the instant it was read — five codes, and no more.
 *
 * *"**Challenge sent** and **Challenge for you** are one standing read from two sides, not two
 * states"* ([#221](https://github.com/Raketa02/Raketa/issues/221)): the code is one and the
 * sentence is two, and which one a reader gets is decided by whether they hold the organiser
 * seat.
 *
 * **Five, not twenty.** The prototype's twenty card states are *"a presentation vocabulary
 * spanning money, booking and results this context does not own"*, and an unknown standing
 * takes the out-of-date gap rather than a shorter list
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §13).
 *
 * The standing is **derived from the seats and the clock and never stored**, so it is right
 * for the whole gap between a deadline and anything noticing — which is also why nothing on
 * this side computes one.
 */

export const STANDINGS = [
  'AWAITING_ANSWERS',
  'ON',
  'LINE_UP_INCOMPLETE',
  'DECLINED',
  'LAPSED',
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
