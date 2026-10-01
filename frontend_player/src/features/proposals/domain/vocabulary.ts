/**
 * **The group deck's codes, spelled here** — the unions the card draws its words by, held equal to
 * the generated ones in `mappers/wireVocabulary.ts`, so a code the contract adds or renames fails
 * `pnpm typecheck` in the one file whose job is saying so.
 *
 * The wire's own spellings, kept, for every code a copy table is keyed by: a card's type, what a
 * yes does to its court, the overlap's grade and shade and a range of the day. **The kind is the
 * one exception**: the wire's `SearchMode` is `COMPETITIVE | FOR_FUN`, and the group page's switch
 * already holds the same two as `competitive | forFun` (`groups`' game intent), which is the value
 * a player chooses and hands this feature — so the deck speaks the switch's spelling, and the
 * mapper converts at the wire.
 */

/**
 * The three cards a deck deals (the mechanics §8.1) — `SEAT_OPEN` a rescue: a booked game that lost
 * a player, dealt to its best fits (#545). Its id is the booking's.
 */
export type CardType = 'SEAT_OPEN' | 'CHALLENGE' | 'PICKED_FOR_YOU';

/**
 * What a yes on the card does to its court — a free vote while the game is short of more than your
 * yes, the booking itself when your yes is the last one, and a rescue's court, **booked** already:
 * a yes takes the seat and pays at once (the screens A2.3).
 */
export type CourtState = 'COURT_AVAILABLE' | 'BOOK_IT_NOW' | 'BOOKED';

/** *High / Good / Slim overlap* — the grade the server gives the card's week. */
export type OverlapGrade = 'HIGH' | 'GOOD' | 'SLIM';

/** How many of the card's people are free together in one cell of the grid. */
export type OverlapShade = 'BRIGHT' | 'DIM' | 'DARK';

/** A third of a day — Morning 07–12, Afternoon 12–17, Evening 17–23. */
export type DayRange = 'MORNING' | 'AFTERNOON' | 'EVENING';

/** The grid's three rows, top to bottom. */
export const DAY_RANGES: readonly DayRange[] = ['MORNING', 'AFTERNOON', 'EVENING'];

/** A game's kind — the switch's two segments, Competitive first. */
export type GameKind = 'competitive' | 'forFun';

/**
 * **Why a share could not be held when the game filled** (the mechanics §12.2, §19) — the wire's
 * own spelling, because `fillOutcome` decides by it: the bank wanting the player present, a decline,
 * terms to accept again for a card whose brand changed, and no method at all.
 */
export type PaymentRefusal = 'AUTHENTICATION_REQUIRED' | 'DECLINED' | 'TERMS_NEEDED' | 'NO_METHOD';

/**
 * **What a game on Home is, right now** (the mechanics §14.1; #542, #556) — one status per card,
 * folded by the server at its `read_at` from the booking, its Game's result and the clock. The
 * wire's own spelling, because the copy is keyed by it: *Waiting for the club*, *Booked*, *Seat
 * open*, the five result states as today's cards name them, and *Called off*.
 */
export type HomeStatus =
  | 'WAITING_FOR_THE_CLUB'
  | 'BOOKED'
  | 'SEAT_OPEN'
  | 'NEEDS_RESULT'
  | 'CONFIRM_THE_RESULT'
  | 'COUNTED'
  | 'UNCOUNTED'
  | 'NEVER_PLAYED'
  | 'CALLED_OFF';

/**
 * **Why a game on Home is called off** (#543, #544) — the club refused the request, or did not
 * answer it in time (nobody paid in either), or a seat that opened before the club's cut-off was
 * still empty at it (everybody still in is refunded in full). The wire's own spelling: the line
 * under the card is keyed by it.
 */
export type CalledOffReason = 'REFUSED' | 'NO_ANSWER' | 'SHORT_AT_THE_CUT_OFF';

/**
 * **Why a game on Home is uncounted with nobody disagreeing about a score** (#544) — its hour came
 * with a seat still open: *Uncounted · a seat was empty*.
 */
export type UncountedReason = 'SEAT_EMPTY';

/**
 * **What *Leave the game* costs right now** (the mechanics §13; #544) — before the club's cut-off
 * (refunded at once, less the card fee), after it (refunded only when somebody takes the seat), or
 * while an On request club decides (nobody has paid; leaving withdraws the yes). The sheet's words
 * are keyed by it.
 */
export type LeavingKind = 'BEFORE_THE_CUT_OFF' | 'AFTER_THE_CUT_OFF' | 'WHILE_WAITING_FOR_THE_CLUB';

/**
 * **Where a game still filling stands, for its details** (the mechanics §14.2; #542) — filling,
 * full and waiting for an On request club, booked, or one of the four ways it ended unfilled.
 */
export type ProposalStatus =
  | 'FILLING'
  | 'WAITING_FOR_THE_CLUB'
  | 'FILLED'
  | 'EXPIRED'
  | 'WITHDRAWN'
  | 'COURT_HOUR_LOST'
  | 'TURNED_DOWN';

/**
 * **What the reader may do on a game's details now**, in the screen's order (#542, #543): *I'm in* /
 * *Not this time*, *Withdraw* while they are In, *Leave the game* in its place while the club
 * decides, and *Confirm your payment* while their seat waits on a refused one.
 */
export type ReaderAction = 'YES' | 'NO' | 'WITHDRAW' | 'LEAVE' | 'CONFIRM_PAYMENT';
