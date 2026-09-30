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

/** The three cards a deck deals (the mechanics §8.1). `SEAT_OPEN` is dealt once rescues are (#545). */
export type CardType = 'SEAT_OPEN' | 'CHALLENGE' | 'PICKED_FOR_YOU';

/**
 * What a yes on the card does to its court — a free vote while the game is short of more than your
 * yes, the booking itself when your yes is the last one (the screens A2.3). *Booked* is a rescue's
 * and is read off the card's type, not served here.
 */
export type CourtState = 'COURT_AVAILABLE' | 'BOOK_IT_NOW';

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
