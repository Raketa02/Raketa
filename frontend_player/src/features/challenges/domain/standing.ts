/**
 * What a challenge **is**, at the instant it was read — seven codes, and no more.
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
 * **`WITHDRAWN` is the sixth and it is one of the two the seats cannot reach**
 * ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)):
 * every other code is a fold of the seats and the clock, and this one is an act — *Remove the
 * challenge*, the organiser's while nobody has joined, and that act alone since ADR-0172. It is
 * neither a decline nor a lapse, and its word is the record's own — not *cancel*, and not
 * *stand down*, which the root `CONTEXT.md` owns platform-wide for a term that cannot be
 * evaluated.
 *
 * **`CALLED_OFF` is the seventh, and it is the game's fourth end seen from the court**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §1–§2): a court that has been a game ends *with* its game, by the departure that leaves one
 * player on it or by *Call it off*, and the challenge records that ending in the act that tells
 * the game. It is an ending like the other three — dated by `ended_at`, kept on the inbox's
 * day-long shelf, never re-entered — and the second conclusion the seats cannot reach, because
 * which of two deserted courts is called off is a fact only the act that took it knows.
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
  'CALLED_OFF',
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
 * What the person in a seat did about being asked — **four values, and *awaiting* is not one
 * of them.**
 *
 * The absence of an answer *is* awaiting, and giving it a name would make *nothing yet* and
 * `AWAITING` two spellings of one state with nothing to choose between them.
 *
 * **`LAPSED` is never a decline.** They do the same thing to the line-up and they are
 * different facts — the `answers challenges` strand counts challenges that got an answer
 * inside their window, and it is unmeasurable if silence is filed as judgement.
 *
 * **`LEFT` is the one answer written over another**
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)):
 * an accepted seat, on a court whose line-up had completed into a game, whose occupant has since
 * left it. It opens the seat exactly as the other two do and is neither of them — leaving a game
 * you agreed to is not declining an invitation, and nothing prices it yet.
 */
export const SEAT_ANSWERS = ['ACCEPTED', 'DECLINED', 'LAPSED', 'LEFT'] as const;

export type SeatAnswer = (typeof SEAT_ANSWERS)[number];

/**
 * **Which answers mean the seat has been given up** — a no, silence, and (ADR-0162) leaving the
 * game the court became. `ACCEPTED` is the one that does not.
 *
 * A `Record` keyed by the union rather than a disjunction at each reader, and **one table for
 * the two readers** — the pair rule and the detail's arm: a fifth answer added to the contract
 * fails `pnpm typecheck` here, once, rather than quietly counting as *in* wherever an `||` chain
 * forgot it, which is exactly the class of miss `LEFT` would have been.
 */
export const GIVES_UP_THE_SEAT: Readonly<Record<SeatAnswer, boolean>> = {
  ACCEPTED: false,
  DECLINED: true,
  LAPSED: true,
  LEFT: true,
};

/**
 * **An ending, as its sentence quotes it** — who ended it, how, and what the reader's own seat
 * says ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §3, §7).
 *
 * The four endings share one payload because they are keyed one way: **by whose act ended the
 * court and by that person's own seat**, which the wire names as `ended_by` and this fold turns
 * into a name. A seat that `LEFT` reads *left* wherever it is named — on a `DECLINED` court it
 * tells the departure that deserted a half-built court from the no that did — and `byADeparture`
 * is that one reading, made once.
 *
 * **`endedBy` is `you` where the reader's own act ended it** — their own *no*, their own *left*,
 * their own removal — which is what lets one deck say *You left* and *{name} left* off one
 * field. The two folded endings read the reader's own seat as well: §13's invitee column — *You
 * said no*, *Your day ran out* — is true of a seat that gave up whoever's act closed the court
 * after it, and `ownAnswer` carries that seat.
 *
 * **And one ending is nobody's** ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §3): a `CALLED_OFF` court the hour ended, still short of a player when its moment passed. The
 * wire names nobody on it by design, and `byNobody` is that reading — told apart from `unknown`,
 * which is a name the wire owed and could not give.
 */
export interface EndingFacts {
  /**
   * The player whose act ended it — `ended_by`, as a sentence names them. `unknown` where the
   * wire named a seat `users` can no longer answer for, or named nobody on an ending that owes
   * a name: the row draws `?` and never a name this app picked by walking the seats.
   */
  readonly endedBy: NamedPlayer;
  /** Whether `ended_by`'s seat reads `LEFT`: the ending was a departure, not a no or a lapse. */
  readonly byADeparture: boolean;
  /**
   * The wire named nobody: the hour's call-off, the one ending that is nobody's act. Present
   * exactly there, absent on every ending somebody's act made.
   */
  readonly byNobody?: true;
  /**
   * What the **reader's own seat** says where they gave it up — a no, a day run out, a yes taken
   * back. Absent where they are in, or hold no seat.
   */
  readonly ownAnswer?: SeatAnswer;
}

/**
 * One standing, with the payload its sentence quotes.
 *
 * A discriminated fold rather than `(standing, side, counts)`: the live standings quote a
 * figure, the endings quote a person and their act, and a flat signature would let a caller
 * pass a count that belongs to a different standing.
 *
 * **A person is a `NamedPlayer`, never a string.** Every ending names somebody, and
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
  | {
      readonly standing: 'AWAITING_ANSWERS';
      readonly awaiting: number;
      /**
       * What the **reader's own seat** says, where the reader is an invitee who has answered.
       *
       * `standing_of` returns this standing while **any** seat is awaiting, so a padel four can
       * be here with the reader's own answer already given — and the sentence keyed on
       * `(standing, side)` alone told them they were the holdup ([#389](https://github.com/Raketa02/Raketa/issues/389)).
       * Ignored on the organiser's own row: their seat is accepted from birth and they are the
       * one waiting.
       *
       * > **Absence means the opposite of what it means on `LINE_UP_INCOMPLETE`.** There an
       * > absent answer is a reader who is **in**; here it is a reader who has **not spoken**.
       * > The field is the same fact from the same seat, and the polarity belongs to the
       * > standing rather than to the field — which is why one name serves both and why this
       * > note exists. What *is* the same in both: **absent draws the sentence that shipped.**
       */
      readonly ownAnswer?: SeatAnswer;
    }
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
  | ({ readonly standing: 'DECLINED' } & EndingFacts)
  | ({ readonly standing: 'LAPSED' } & EndingFacts)
  | ({ readonly standing: 'WITHDRAWN' } & EndingFacts)
  | ({ readonly standing: 'CALLED_OFF' } & EndingFacts)
);

/** The four standings that are endings — the arms of {@link StandingFacts} that carry {@link EndingFacts}. */
export type EndedStanding = Extract<Standing, 'DECLINED' | 'LAPSED' | 'WITHDRAWN' | 'CALLED_OFF'>;

/** The four arms of {@link StandingFacts} that are endings — one type, so a reader of them switches over four and no more. */
export type EndedFacts = Extract<StandingFacts, { readonly standing: EndedStanding }>;
