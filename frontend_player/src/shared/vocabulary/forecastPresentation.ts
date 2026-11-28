/**
 * **The Balance forecast block's words** — the eyebrow, the gap, the counted sentence, the two
 * tiles, and what each of the block's elements says to a listener
 * ([the-words.md](../../../../docs/specs/matchmaking/the-words.md) §24.8, §25).
 *
 * ## Below every feature that draws the block
 *
 * The block (`shared/ui`'s `ForecastBlock`, `StakeTiles`) was the booked game's alone until a
 * competitive game's details drew it too, as the top card a player reads before saying yes
 * ([#839](https://github.com/Rakieta02/Rakieta/issues/839); ADR-0207 §6, which moves it). It came
 * here whole, with its words, because two features that may not import each other — `games` and
 * `proposals` — say them. `balancePresentation.ts` stays the home of the word and the tone a figure
 * is read in; this file is the block's own.
 *
 * ## An accessible name is copy
 *
 * §20's rule: it is localisable, it quotes numbers that need a format, and it composes words whose
 * home is here. So the block's three spoken names live beside its visible words, never inlined in
 * the component.
 *
 * **Every figure is the server's.** The gap is signed by the engine and printed as served; nothing
 * here subtracts two rounded levels.
 */

import { formatLevel, formatSignedLevel } from '@/shared/formatting/ratingFormat';

import { balanceLabel } from './balancePresentation';

/** The two side strengths a forecast was read from, and the gap between them **as served**. */
export interface ForecastSplit {
  readonly yourSide: number;
  readonly theirSide: number;
  /** `yourSide − theirSide`, signed by the engine. Never subtracted here. */
  readonly gap: number;
}

/** What a **counted** result would do to your Level — the pair, sent together or not at all. */
export interface ForecastStake {
  readonly winDelta: number;
  readonly lossDelta: number;
}

/**
 * The block's eyebrow. **Stored as words and drawn uppercase** by the eyebrow style: a second copy
 * in capitals would reach a screen reader as letters.
 */
export const BALANCE_FORECAST = 'Balance forecast';

/**
 * The word between the two side strengths, and the whole of what the middle column says. Lower
 * case, because it is a unit rather than a heading: the two figures either side of it are the
 * sentence.
 */
export const GAP_WORD = 'gap';

/**
 * **What a confirmed score does on a counted game**, under the percentage. The booked game says it
 * of a `COUNTED` game, a competitive game's details of every game they draw the block for — the
 * same fact on the same block, so one sentence.
 */
export const COUNTED_GAME_SENTENCE = 'A counted game — a confirmed score moves everybody’s level.';

/** The two stake tiles' names. *If*, because the result has not happened. */
export const WIN_TILE = 'If you win';
export const LOSE_TILE = 'If you lose';

/**
 * The split row's spoken name — **the two sides and the gap, in the order the row prints them**:
 * `You and kasia.w 2,70, tomek.p and marek.b 2,71, gap −0,01`.
 *
 * The names are a sentence's, nicknames whole over *and*, where the bar under the row draws stems
 * over `+`: a listener hears the register a sentence is in. The bar itself announces nothing — it
 * would be the fourth reading of one fact.
 */
export function splitLabel(names: readonly [string, string], split: ForecastSplit): string {
  const yours = `${names[0]} ${formatLevel(split.yourSide)}`;
  const theirs = `${names[1]} ${formatLevel(split.theirSide)}`;
  return `${yours}, ${theirs}, ${GAP_WORD} ${formatLevel(split.gap)}`;
}

/**
 * The reading's spoken name: the balance word and its figure — §20.4's order, the word first
 * because the bar is a colour — then the sentence about what a score does, where there is one.
 */
export function readingLabel(pct: number, sentence: string | undefined): string {
  return sentence === undefined ? balanceLabel(pct) : `${balanceLabel(pct)}. ${sentence}`;
}

/** The two tiles as one element: **two clauses or none**, the pair being the fact. */
export function stakeLabel(stake: ForecastStake): string {
  return `${WIN_TILE} ${formatSignedLevel(stake.winDelta)}, ${LOSE_TILE} ${formatSignedLevel(stake.lossDelta)}`;
}
