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

/**
 * **Who a posted game is for** (the mechanics §9.1 step 3; #546) — *Anyone*, a game of men, a game
 * of women, or *Mixed pairs*: in doubles, each side one man and one woman. The wire's own spelling,
 * because the control's words are keyed by it. Whether the poster stands on their own game is the
 * server's to say (`who_leaves_you_out`), never which of the two a refusal was.
 */
export type Who = 'ANYONE' | 'MEN' | 'WOMEN' | 'MIXED_PAIRS';

/** The four, in the control's order (mock 18). */
export const WHO_ORDER: readonly Who[] = ['ANYONE', 'MEN', 'WOMEN', 'MIXED_PAIRS'];

/** A game's kind — the switch's two segments, Competitive first. */
export type GameKind = 'competitive' | 'forFun';

/** The two, in the switch's order. */
export const GAME_KINDS = ['competitive', 'forFun'] as const satisfies readonly GameKind[];

/**
 * **Why a share could not be held when the game filled** (the mechanics §12.2, §19) — the wire's
 * own spelling, because `fillOutcome` decides by it: the bank wanting the player present, a decline,
 * terms to accept again for a card whose brand changed, and no method at all.
 */
export type PaymentRefusal = 'AUTHENTICATION_REQUIRED' | 'DECLINED' | 'TERMS_NEEDED' | 'NO_METHOD';

/**
 * **What a game on Home is, right now** (the mechanics §14.1; #542, #556) — one status per card,
 * folded by the server at its `read_at` from the booking, its Game's result and the clock. The
 * wire's own spelling, because the copy is keyed by it: *Waiting for one payment* (#625, #626),
 * *Booked*, *Seat open*, the five result states — *Played · no score* in *Never played*'s place
 * since #655 — and *Called off*. A full game books at once at every club (ADR-0196, #676): none
 * waits for its club.
 */
export type HomeStatus =
  | 'WAITING_FOR_A_PAYMENT'
  | 'BOOKED'
  | 'SEAT_OPEN'
  | 'NEEDS_RESULT'
  | 'CONFIRM_THE_RESULT'
  | 'COUNTED'
  | 'UNCOUNTED'
  /** Full at its hour, and nobody recorded it before the entry window closed: played (#655). */
  | 'PLAYED_NO_SCORE'
  | 'CALLED_OFF';

/**
 * **Why a game on Home is called off** (#544, #547, #624, #625) — a seat that opened before the
 * club's cut-off was still empty at it, or the club cancelled it (everybody still in is refunded in
 * full in both); of a full game gone back to filling, its last moment to book passed with a seat
 * open, or its court went to another game first (nobody paid in either); and a payment the game
 * waited for did not come in before its last moment to book (nobody paid). The wire's own spelling:
 * the line under the card is keyed by it.
 */
export type CalledOffReason =
  | 'SHORT_AT_THE_CUT_OFF'
  | 'CANCELLED_BY_THE_CLUB'
  | 'BOOK_BY_PASSED'
  | 'COURT_HOUR_LOST'
  | 'PAYMENT_NOT_IN_TIME';

/**
 * **Why the club cancelled a booked game** (#547; the mechanics §16.9) — the players are told it with
 * their refund. `OTHER` is no reason given, and the line says none.
 */
export type ClubCancelReason = 'WEATHER' | 'REPAIR' | 'DOUBLE_BOOKING' | 'OTHER';

/**
 * **Why a game on Home is uncounted with nobody disagreeing about a score** — its hour came with a
 * seat still open (#544): *Uncounted · a seat was empty*; or somebody tapped *isn't here yet* at the
 * court never arrived (#657, #658): the game takes no score and never counts — for a day
 * provisionally, until a late *I was there* is confirmed or the day ends.
 */
export type UncountedReason = 'SEAT_EMPTY' | 'DIDNT_COME';

/**
 * **What *Leave the game* costs right now** (the mechanics §13; #544) — before the club's cut-off
 * (nothing is taken: the hold on the card is let go, Q113), after it (the share stays taken, and
 * comes back less the fee kept on it only when somebody takes the seat), or while a full game waits
 * for one payment (#625: nobody has paid; leaving withdraws the yes). The sheet's words are keyed
 * by it.
 */
export type LeavingKind =
  'BEFORE_THE_CUT_OFF' | 'AFTER_THE_CUT_OFF' | 'WHILE_WAITING_FOR_A_PAYMENT';

/**
 * **Where the shares of a booked game stand** (the mechanics §12.2; Q113) — held on the cards until
 * the club's cut-off, the reader's only checked because a hold would not last that long (held at
 * its holding time, four days before the cut-off), or taken.
 */
export type ShareState = 'HELD' | 'CHECKED' | 'TAKEN';

/**
 * **What a refused card's thirty minutes are for** (#638; the mechanics §12.2, Q113) — one
 * machinery, two names, decided by the club's cut-off: before it nothing is taken, only held, so it
 * is the time to fix the card (*Fix your card by 14:40*); from it on the money is taken at once, so
 * it is the time to pay (*Confirm your payment by 14:40*). Only the refused player's own words
 * change by it; the others read *Waiting for one payment* either way.
 */
export type TimeTo = 'FIX_THE_CARD' | 'PAY';

/**
 * **Where a game still filling stands, for its details** (the mechanics §14.2; #542) — filling,
 * full and waiting for one player's payment (#625, #626), booked, or one of the three ways it ended
 * unfilled.
 */
export type ProposalStatus =
  'FILLING' | 'WAITING_FOR_A_PAYMENT' | 'FILLED' | 'EXPIRED' | 'WITHDRAWN' | 'COURT_HOUR_LOST';

/**
 * **What the reader may do on a game's details now**, in the screen's order (#542, #625): *I'm in* /
 * *Not this time*, *Withdraw* while they are In, *Leave the game* in its place while the full game
 * waits for one payment, and *Confirm your payment* while their seat waits on a refused one.
 */
export type ReaderAction = 'YES' | 'NO' | 'WITHDRAW' | 'LEAVE' | 'CONFIRM_PAYMENT';

/**
 * **Where the reader stands with somebody else on a booked game** — PLAYED WITH's relation (#754),
 * spelled here as the wire spells it, and held equal to it in `mappers/wireVocabulary.ts`. The same
 * four `friends` spells for its own surfaces: this feature names it itself rather than reading
 * `friends`' type, since `friends` reads this feature's keys and Home, and an import back, even of
 * a type, is a cycle (architecture Part 1 §6). The route hands the card both sides agree on.
 */
export type PlayedWithRelation = 'NONE' | 'SENT' | 'ASKED_YOU' | 'FRIEND';
