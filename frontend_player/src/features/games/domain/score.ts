/**
 * The score, as the grid holds it and as the wire takes it — **and the four things this app is
 * entitled to refuse about one.**
 *
 * ## The shape is the prototype's, and so is the instrument
 *
 * `prototype/result-confirmation` is the ticket's own prior art and settled the entry
 * interaction: *"a pad, not a stepper and not a keyboard"*, over a grid of the sport's own legs,
 * *"validated permissively — the app knows the shape and declines the obviously impossible, and
 * never enforces the rulebook"*. `SHAPE` below is that prototype's table unchanged: padel and
 * tennis in **sets and games**, squash and badminton in **games and points**. What survived a
 * second look is the `+` key beside it, and it is what makes the table permissive rather than a
 * ruling — a padel super tie-break goes past 7 and a badminton game past 21, and the key keeps
 * counting rather than the pad calling a real evening illegal.
 *
 * ## Absolute, never relative to whoever is looking
 *
 * A draft is `{ a, b }` per set, exactly as `SetScoreSchema` is: *"a score stored from one point
 * of view has to be flipped by whoever reads it next, and the first reader to forget publishes a
 * loss as a win."* Which column is drawn first is a **view** decision the grid makes from the
 * reader's own side, and it is the only place the flip happens.
 *
 * ## Cells are digits, because nought is a score and empty is not
 *
 * Each cell holds what somebody put there as characters, so `''` and `'0'` stay different facts:
 * losing a set to love is a result, and a set nobody has filled in is not one. The prototype's
 * `number | null` says the same thing; strings say it without a parse at every render.
 *
 * ## What it refuses is the aggregate's list, plus two shapes the wire cannot spell
 *
 * A 10-8 super tie-break, a 30-29 badminton game and a timed 3-2 all pass. What is declined is
 * the three the server declines — `a_result_must_carry_a_score`, `a_score_must_name_a_winner`,
 * `a_score_is_not_this_shape` — plus the two the grid can produce and the wire has no code for:
 * a half-typed set, and a gap in a list whose whole meaning is *the order they were played*.
 *
 * **One refusal in this feature is not the aggregate's at all**, and it is `sameScore`'s, at the
 * screen: a counter that is byte-for-byte the score it answers. The server takes it, and what it
 * produces is two matching proposals nobody accepts, which is an **unscored game between two
 * people who agreed**. It is refused because the client is the only party that can see it coming
 * — the counter's grid was pre-loaded, so this is a harm the pre-load created.
 *
 * **Refusing here does not make the server's refusal dead copy.** The commit re-validates every
 * rule a picker enforced, and re-sending the identical body would fail identically — the same
 * posture the profile commit takes, and the reason `gameErrorMessage` still writes a sentence
 * for all three codes.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { Score } from './game';
import type { ScoreColumn } from './vocabulary';

/**
 * How many sets a score may hold. **Five**, which is the longest match any of the four sports
 * has and the contract's own `maxItems`.
 */
export const MAX_SETS = 5;

/** The most either side may have taken in one set — the contract's bound, and the `+` key's. */
export const MAX_POINTS = 99;

/** What a sport's grid is made of: how many rows, and how far the pad counts before the `+`. */
export interface ScoreShape {
  /** Rows on the grid. The prototype's common formats; `3.1` fixes no format. */
  readonly legs: number;
  /** The pad's normal range, `0…padTo`. Beyond it the `+` key keeps counting. */
  readonly padTo: number;
}

/**
 * The prototype's table, and **the decision its README left open, taken.**
 *
 * It is a statement about the **common** format and never about the rulebook: the `+` key is
 * what carries a fifth set nobody expected and a badminton game that went to thirty, so the
 * numbers here cost nobody an evening they actually played.
 *
 * **Badminton keeps `21`, and the cost is a four-row pad.** The prototype recorded the problem
 * and refused to settle it: *"badminton's 0–21 is twenty-four keys and four rows, which is a
 * different instrument, not a wider one… decide whether badminton gets a `padTo` of 11 plus the
 * `+` key or something else entirely."* The alternative loses on the case that matters — **21 is
 * the number a won badminton game ends on**, so a pad stopping at 11 puts ten taps of the `+`
 * key behind the single most common figure in the sport, on the screen where a score is typed
 * one-handed. Four rows of keys is worse-looking and cheaper to use, and the grid is inside a
 * scroller. What is *not* acceptable is a pad that makes the ordinary evening the expensive one.
 */
export const SHAPE: Readonly<Record<Sport, ScoreShape>> = {
  padel: { legs: 3, padTo: 7 },
  tennis: { legs: 3, padTo: 7 },
  squash: { legs: 5, padTo: 11 },
  badminton: { legs: 3, padTo: 21 },
};

/** One row of the grid: what side A took, and what side B took, as typed. */
export interface SetDraft {
  readonly a: string;
  readonly b: string;
}

/** The grid, one entry per row it draws. */
export type ScoreDraft = readonly SetDraft[];

/** Which cell a key lands in. The column is the wire's, so nothing here is reader-relative. */
export interface Cell {
  readonly set: number;
  readonly side: ScoreColumn;
}

/**
 * One key of the pad — **a value, one more than the last, or nothing there at all.**
 *
 * A union rather than three call sites branching on a string, because three things read a key:
 * the drawing, the accessible name, and the write. Spelled once here so those three cannot
 * disagree about what the keys are.
 */
export type ScoreKey =
  | { readonly kind: 'value'; readonly value: number }
  | { readonly kind: 'higher' }
  | { readonly kind: 'rub' };

/** The pad, in the order it is drawn: the sport's own values, then the two that are not one. */
export function padKeys(padTo: number): readonly ScoreKey[] {
  return [
    ...Array.from({ length: padTo + 1 }, (_ignored, value) => ({ kind: 'value', value }) as const),
    { kind: 'higher' },
    { kind: 'rub' },
  ];
}

/**
 * What is wrong with a draft, and **which set it is wrong in** where there is one.
 *
 * A union rather than a code and an optional number, because *set 2 is half typed* and *this
 * score names nobody* are sentences of different shapes, and the copy deck writes one function
 * per variant for exactly that reason.
 */
export type ScoreProblem =
  | { readonly code: 'no-sets' }
  | { readonly code: 'a-gap'; readonly set: number }
  | { readonly code: 'half-a-set'; readonly set: number }
  | { readonly code: 'level-set'; readonly set: number }
  | { readonly code: 'no-winner' };

/**
 * A read draft: the score, or the one thing standing in the way of it.
 *
 * One function rather than a validator beside a converter, so a screen cannot send a draft
 * nobody read — the invalid case is not representable at the call site.
 */
export type ScoreReading =
  | { readonly ok: true; readonly score: Score }
  | { readonly ok: false; readonly problem: ScoreProblem };

/** A grid with nothing in it, at the sport's own number of rows. */
export function emptyDraft(sport: Sport): ScoreDraft {
  return Array.from({ length: SHAPE[sport].legs }, () => ({ a: '', b: '' }));
}

/**
 * A grid pre-loaded with a score somebody already put up — the counter's and the correction's.
 *
 * It grows past the sport's own row count where the score it came from did, because a score the
 * server took is a score this grid must be able to show back: truncating one to fit a table
 * about the common format would drop a set somebody played.
 */
export function draftFrom(score: Score, sport: Sport): ScoreDraft {
  const rows = Math.min(MAX_SETS, Math.max(SHAPE[sport].legs, score.sets.length));
  return Array.from({ length: rows }, (_ignored, index) => {
    const set = score.sets[index];
    return set === undefined ? { a: '', b: '' } : { a: String(set.a), b: String(set.b) };
  });
}

/**
 * One key, into one cell — **the whole of what a key does to a draft.**
 *
 * The caret is the component's, because it is a caret; what a key *writes* is a rule, and
 * `advancesCaret` beside it is the other half of the same rule rather than a second one.
 */
export function applyKey(draft: ScoreDraft, cell: Cell, key: ScoreKey, padTo: number): ScoreDraft {
  switch (key.kind) {
    case 'value':
      return setCell(draft, cell, String(key.value));
    case 'higher':
      return bumpCell(draft, cell, padTo);
    case 'rub':
      // A rub-out clears the cell and leaves the caret on it, because what a player does next is
      // type the figure they meant — the prototype's own `write(null)`, which does not advance.
      return setCell(draft, cell, '');
  }
}

/** Only a value moves the caret on. See {@link nextCell} for where it goes. */
export function advancesCaret(key: ScoreKey): boolean {
  return key.kind === 'value';
}

/** Write one cell. `''` clears it, which is what the pad's rub-out sends. */
export function setCell(draft: ScoreDraft, cell: Cell, value: string): ScoreDraft {
  return draft.map((set, index) =>
    index !== cell.set ? set : cell.side === 'a' ? { a: value, b: set.b } : { a: set.a, b: value },
  );
}

/**
 * The `+` key: one more than what is there, and one more than the pad's own ceiling when the
 * cell is empty.
 *
 * This is the whole of *permissive*: the pad states the common range and this key is what says
 * the platform holds no opinion about a tie-break, a golden point or a timed format. Capped at
 * the contract's own bound, because past it the server refuses the shape rather than the score.
 */
export function bumpCell(draft: ScoreDraft, cell: Cell, padTo: number): ScoreDraft {
  const current = draft[cell.set]?.[cell.side] ?? '';
  const next = current === '' ? padTo + 1 : Math.min(MAX_POINTS, Number(current) + 1);
  return setCell(draft, cell, String(next));
}

/**
 * Where the caret goes after a value is typed — **across the row, then down**, in the order the
 * grid is drawn.
 *
 * The prototype's own advance, and the reason it is worth having: a score is typed on a court,
 * one-handed, and re-aiming at the next cell after every figure is four taps a player should
 * not have to make. It stops on the last cell rather than wrapping, because wrapping would put
 * the caret back over a number somebody has already typed.
 */
export function nextCell(cell: Cell, columns: readonly ['a' | 'b', 'a' | 'b'], rows: number): Cell {
  if (cell.side === columns[0]) return { set: cell.set, side: columns[1] };
  return { set: Math.min(cell.set + 1, rows - 1), side: columns[0] };
}

/** The score this grid says, or the first thing wrong with it — **in set order**. */
export function readScore(draft: ScoreDraft): ScoreReading {
  const last = draft.reduce(
    (found, set, index) => (set.a === '' && set.b === '' ? found : index),
    -1,
  );
  if (last < 0) return { ok: false, problem: { code: 'no-sets' } };

  const sets: { a: number; b: number }[] = [];
  for (let index = 0; index <= last; index += 1) {
    const set = draft[index] ?? { a: '', b: '' };
    const at = index + 1;
    if (set.a === '' && set.b === '') return { ok: false, problem: { code: 'a-gap', set: at } };
    if (set.a === '' || set.b === '')
      return { ok: false, problem: { code: 'half-a-set', set: at } };
    const a = Number(set.a);
    const b = Number(set.b);
    if (a === b) return { ok: false, problem: { code: 'level-set', set: at } };
    sets.push({ a, b });
  }

  const won = sets.filter((set) => set.a > set.b).length;
  if (won * 2 === sets.length) return { ok: false, problem: { code: 'no-winner' } };

  return { ok: true, score: { sets } };
}

/**
 * Whether two scores say the same thing.
 *
 * One caller and one reason: a counter is pre-loaded with the score it answers, because a real
 * disagreement is usually one digit — and an **unchanged** one sent back is a second proposal
 * that agrees with the first, which leaves the game unscored between two people who agreed.
 * Comparing set by set rather than by a joined string, because a score is a list of pairs and a
 * string is a rendering of one.
 */
export function sameScore(one: Score, other: Score): boolean {
  return (
    one.sets.length === other.sets.length &&
    one.sets.every((set, index) => set.a === other.sets[index]?.a && set.b === other.sets[index]?.b)
  );
}

/** How many sets one column took, for the table that marks the winner's row. */
export function setsWon(score: Score, column: ScoreColumn): number {
  return score.sets.filter((set) => (column === 'a' ? set.a > set.b : set.b > set.a)).length;
}
