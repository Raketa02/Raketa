/**
 * **What each control on these screens announces** — written here, through the same mechanism
 * the visible words are, and never inlined in a component.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §20's rule is that an
 * accessible name is **copy**: it is localisable, it quotes numbers that need a format, and it
 * composes codes whose sentences already have a home. So it lives beside the rest of the copy,
 * and §20.1's one rule decides every element:
 *
 * > **One accessibility element per action. Everything with no action of its own merges into
 * > the nearest action above it.**
 *
 * Three consequences on these screens are worth knowing before reading the file.
 *
 * **A printed score is one element and not a table.** Read cell by cell it is *six, four, three,
 * six* — a row of numbers with no statement in it, and no listener builds a score out of that.
 * It has no action of its own and nothing above it to merge into, so it is one element carrying
 * the whole score in words, with both sides named in every set. The drawing names them once at
 * the top of two columns; the label cannot, so it names them every time.
 *
 * **A grid cell is an answer, so there are as many elements as there are cells.** This is
 * [6.8](../../../../docs/design-system.md#68-the-availability-grid)'s own argument — the state
 * is the point and the role is what carries it — and `accessibilityState.selected` is what
 * React Native ships where §E6 asked for *pressed*.
 *
 * **The two answers on a standing score name the score they are about.** *That's right* and
 * *That's not right* announce identically on every game ever played, and the subject is the one
 * thing a listener cannot see above them — the same argument §20.3 makes for *Add {name} to the
 * court*.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { Game, Score } from '../domain/game';
import type { ScoreDraft, ScoreKey } from '../domain/score';
import type { GameSide } from '../domain/vocabulary';

import {
  ACCEPT_LABEL,
  COUNTER_LABEL,
  RUB_OUT_LABEL,
  gameEyebrow,
  setLabel,
  setsCounted,
  spokenScore,
} from './gamePresentation';

export interface SpokenSides {
  readonly ours: string;
  readonly theirs: string;
}

/**
 * A score, said from one side of the net — **the four facts that always travel together.**
 *
 * They were four parameters on three functions and three props on two components, which is one
 * type asking to be born: nothing says a score without also saying whose sport it is, whose side
 * is reading it, and what the two sides are called.
 */
export interface ScoreView {
  readonly score: Score;
  readonly sport: Sport;
  /** The reader's side of the net. The flip into `a`/`b` happens inside, once. */
  readonly mine: GameSide;
  readonly sides: SpokenSides;
}

/**
 * A row in *Your games*: **the identifying facts, then what it is asking of you.**
 *
 * Identifying facts lead, which is §20.3's order and the reason it exists — a listener who has
 * heard enough interrupts and acts, and *what* they would be acting on has to come first.
 */
export function gameRowLabel(sportName: string, game: Game, standing: string): string {
  return `${gameEyebrow(sportName, game)}. ${standing}`;
}

/**
 * The score, whole, in the reader's own order, under a lead saying **whose it is**.
 *
 * The lead is the caller's because it is the one thing that differs by placement — *the agreed
 * score*, *the score on the table*, *your score* — and the score itself never does.
 */
export function scoreLabel(lead: string, view: ScoreView): string {
  return `${lead}. ${spokenScore(view)}`;
}

/** One cell of the grid: which set, whose side, and what is in it. */
export function cellLabel(sport: Sport, set: number, side: string, value: string): string {
  return `${setLabel(sport, set + 1)}, ${side}, ${value === '' ? 'empty' : value}`;
}

/**
 * One key of the pad. A value says itself; the two that are not values say what they do.
 *
 * *Higher* rather than the visible `21+`, which is a face rather than a sentence: a listener
 * hearing *twenty-one plus* has been told a range where the key is an act.
 */
export function keyLabel(key: ScoreKey): string {
  switch (key.kind) {
    case 'value':
      return String(key.value);
    case 'higher':
      return HIGHER_A11Y_LABEL;
    case 'rub':
      return RUB_OUT_LABEL;
  }
}

/** What the `+` key does, said as an act. */
export const HIGHER_A11Y_LABEL = 'Higher';

/** Agreeing, with the score it agrees with — because *That's right* is true of every game. */
export function acceptLabel(view: ScoreView): string {
  return `${ACCEPT_LABEL}. ${spokenScore(view)}`;
}

/** Disagreeing, named by what it opens: there is no bare rejection, so this is a door. */
export const COUNTER_A11Y_LABEL = `${COUNTER_LABEL} — put a different score up`;

/**
 * How much of the grid is filled, for the send.
 *
 * A send whose name never changed would announce *Put the score in* over an empty grid and over
 * a finished one, which is the one thing about the instrument a listener cannot otherwise reach.
 */
export function submitLabelFor(visible: string, draft: ScoreDraft, sport: Sport): string {
  const filled = draft.filter((set) => set.a !== '' && set.b !== '').length;
  return `${visible}. ${setsCounted(sport, filled)} filled in`;
}
