/**
 * **The ranking's codes, spelled by this feature** ([#775](https://github.com/Raketa02/Raketa/issues/775);
 * [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)). Copy is keyed
 * by them, so each is spelled here and held equal to the contract's in `mappers/wireVocabulary.ts`:
 * a code added on the wire fails `pnpm typecheck` there, and again wherever no words exist for it.
 */

/**
 * **What the reader's place card says** (the rankings screens §4):
 *
 * - `LISTED` — *YOUR PLACE · 7th · of 13*, the level, the chip and the gap line;
 * - `NEEDS_RESULTS` — fewer results than the view takes: *2 of 5 games — …*;
 * - `NO_LEVEL` — no level in the sport: *No squash level yet — …*, with **Get your squash level**;
 * - `OFF_THE_LIST` — no result in 90 days: *Off the list — …*;
 * - `HIDDEN` — General only: listed, and *Show me in General* turned off — the place without the gap
 *   line, *Hidden from General* in its place;
 * - `JUST_YOU` and `NO_FRIEND_LISTED` — Friends only (#777).
 */
export type CardState =
  | 'LISTED'
  | 'NEEDS_RESULTS'
  | 'NO_LEVEL'
  | 'OFF_THE_LIST'
  | 'JUST_YOU'
  | 'NO_FRIEND_LISTED'
  | 'HIDDEN';

/** **The chip**: places moved in the last 7 days — up, down, the same, or new to the list. */
export type ChipKind = 'UP' | 'DOWN' | 'SAME' | 'NEW';

/** **Which list**: everybody listed in the sport, or the reader and their friends (#777). */
export type RankingView = 'GENERAL' | 'FRIENDS';
