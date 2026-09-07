/**
 * What the app knows about the shape of a score — **and what it refuses to know.**
 *
 * The delta this flow was specified in is explicit: *"the app knows the shape and declines the
 * obviously impossible; it does not enforce the rulebook"*, because local variation is wide
 * enough that a strict validator eventually calls a real match illegal. So the assertions below
 * are mostly about what **passes**: a 10-8 super tie-break, a 30-29 badminton game, a 45-minute
 * timed 3-2. What is refused is the four things the aggregate itself refuses, checked here so a
 * player is told before a round trip rather than by a `400`.
 */

import {
  MAX_POINTS,
  SHAPE,
  bumpCell,
  draftFrom,
  emptyDraft,
  nextCell,
  readScore,
  sameScore,
  setCell,
  setsWon,
} from './score';

/** A draft from pairs, in set order. `null` is an empty cell — never `0`, which is a score. */
function draft(...sets: readonly (readonly [number | null, number | null])[]) {
  const cell = (value: number | null) => (value === null ? '' : String(value));
  return [
    ...sets.map(([a, b]) => ({ a: cell(a), b: cell(b) })),
    ...emptyDraft('padel').slice(sets.length),
  ];
}

describe('reading a score off the grid', () => {
  it('is the sets that were filled in, absolute and in order', () => {
    const reading = readScore(draft([6, 4], [3, 6], [6, 2]));

    expect(reading).toEqual({
      ok: true,
      score: {
        sets: [
          { a: 6, b: 4 },
          { a: 3, b: 6 },
          { a: 6, b: 2 },
        ],
      },
    });
  });

  it('drops the rows nobody typed in, so a two-set match is a two-set score', () => {
    expect(readScore(draft([11, 9], [11, 7]))).toEqual({
      ok: true,
      score: {
        sets: [
          { a: 11, b: 9 },
          { a: 11, b: 7 },
        ],
      },
    });
  });

  it('keeps a nought, because losing a set to love is a score and an empty cell is not', () => {
    expect(readScore(draft([6, 0], [6, 0]))).toEqual({
      ok: true,
      score: {
        sets: [
          { a: 6, b: 0 },
          { a: 6, b: 0 },
        ],
      },
    });
  });
});

describe('what it declines, which is only the obviously impossible', () => {
  it('declines an empty grid, which is the bare rejection this flow does not have', () => {
    expect(readScore(emptyDraft('padel'))).toEqual({ ok: false, problem: { code: 'no-sets' } });
  });

  it('declines a set with one side missing, and names the set', () => {
    expect(readScore(draft([6, 4], [3, null]))).toEqual({
      ok: false,
      problem: { code: 'half-a-set', set: 2 },
    });
  });

  it('declines a gap, because the sets are in the order they were played', () => {
    expect(readScore(draft([6, 4], [null, null], [6, 2]))).toEqual({
      ok: false,
      problem: { code: 'a-gap', set: 2 },
    });
  });

  it('declines a level set — a set that is level has not finished', () => {
    expect(readScore(draft([6, 6]))).toEqual({
      ok: false,
      problem: { code: 'level-set', set: 1 },
    });
  });

  it('declines a score that names nobody, which is the invariant and not a sanity check', () => {
    expect(readScore(draft([6, 4], [3, 6]))).toEqual({ ok: false, problem: { code: 'no-winner' } });
  });

  it('reports the first problem in set order, so the sentence points at one cell', () => {
    expect(readScore(draft([6, 6], [3, null]))).toEqual({
      ok: false,
      problem: { code: 'level-set', set: 1 },
    });
  });
});

describe('the rulebook it does not enforce', () => {
  it('takes a padel super tie-break, which is not a set score and happens every week', () => {
    expect(readScore(draft([6, 4], [3, 6], [10, 8])).ok).toBe(true);
  });

  it('takes a badminton game past twenty-one, which is where badminton games go', () => {
    expect(readScore(draft([21, 19], [30, 29])).ok).toBe(true);
  });

  it('takes a timed format nobody would recognise as a sport', () => {
    expect(readScore(draft([3, 2])).ok).toBe(true);
  });
});

describe('the grid a sport opens with', () => {
  /** The prototype's own table: sets and games for two of them, games and points for the others. */
  it('is the prototype’s shape, unchanged', () => {
    expect(emptyDraft('padel')).toHaveLength(3);
    expect(emptyDraft('squash')).toHaveLength(5);
    expect(SHAPE.badminton.padTo).toBe(21);
    expect(SHAPE.tennis.padTo).toBe(7);
  });
});

describe('the pad’s keys', () => {
  it('writes a value into the cell the caret is on', () => {
    expect(setCell(emptyDraft('padel'), { set: 1, side: 'b' }, '11')[1]).toEqual({
      a: '',
      b: '11',
    });
  });

  it('clears a cell, which is what the rub-out sends', () => {
    const typed = setCell(emptyDraft('padel'), { set: 0, side: 'a' }, '6');

    expect(setCell(typed, { set: 0, side: 'a' }, '')[0]).toEqual({ a: '', b: '' });
  });

  /**
   * The `+` key is what makes the pad's range a statement about the common case rather than a
   * ruling: a padel third set goes past 7 and a badminton game past 21, and neither is something
   * this platform gets to call illegal.
   */
  it('counts past the pad’s own ceiling, starting one above it on an empty cell', () => {
    const once = bumpCell(emptyDraft('padel'), { set: 2, side: 'a' }, SHAPE.padel.padTo);

    expect(once[2]).toEqual({ a: '8', b: '' });
    expect(bumpCell(once, { set: 2, side: 'a' }, SHAPE.padel.padTo)[2]).toEqual({ a: '9', b: '' });
  });

  it('stops at the bound the contract states, rather than sending a shape it refuses', () => {
    const at99 = setCell(emptyDraft('padel'), { set: 0, side: 'a' }, String(MAX_POINTS));

    expect(bumpCell(at99, { set: 0, side: 'a' }, 7)[0]?.a).toBe(String(MAX_POINTS));
  });
});

describe('where the caret goes', () => {
  /** Across the row, then down — the prototype's advance, in the order the grid is drawn. */
  it('crosses to the other side, then drops to the next set', () => {
    expect(nextCell({ set: 0, side: 'a' }, ['a', 'b'], 3)).toEqual({ set: 0, side: 'b' });
    expect(nextCell({ set: 0, side: 'b' }, ['a', 'b'], 3)).toEqual({ set: 1, side: 'a' });
  });

  it('follows the reader’s own column order, so the left cell is always theirs first', () => {
    expect(nextCell({ set: 0, side: 'b' }, ['b', 'a'], 3)).toEqual({ set: 0, side: 'a' });
    expect(nextCell({ set: 0, side: 'a' }, ['b', 'a'], 3)).toEqual({ set: 1, side: 'b' });
  });

  it('stops on the last cell rather than wrapping over something already typed', () => {
    expect(nextCell({ set: 2, side: 'b' }, ['a', 'b'], 3)).toEqual({ set: 2, side: 'a' });
  });
});

describe('a grid pre-loaded with a score somebody already put up', () => {
  /**
   * A counter starts from the score it answers, because a real disagreement is usually one
   * digit — *"the third set was 6-4, not 6-2"* — and starting from an empty grid makes the
   * common case the expensive one.
   */
  it('reads back as the score it was loaded from', () => {
    const score = {
      sets: [
        { a: 6, b: 4 },
        { a: 3, b: 6 },
        { a: 6, b: 2 },
      ],
    };

    expect(readScore(draftFrom(score, 'padel'))).toEqual({ ok: true, score });
  });

  it('grows past the sport’s own rows rather than truncating a set somebody played', () => {
    const five = {
      sets: [
        { a: 6, b: 4 },
        { a: 3, b: 6 },
        { a: 6, b: 2 },
        { a: 3, b: 6 },
        { a: 7, b: 5 },
      ],
    };

    expect(draftFrom(five, 'padel')).toHaveLength(5);
    expect(readScore(draftFrom(five, 'padel'))).toEqual({ ok: true, score: five });
  });

  /**
   * The trap the pre-load creates and the reason the comparison exists: an unchanged counter is
   * a second proposal agreeing with the first, which leaves the game **unscored** between two
   * people who agreed.
   */
  it('is comparable to what it came from, so an unchanged counter can be refused', () => {
    const theirs = {
      sets: [
        { a: 6, b: 4 },
        { a: 6, b: 2 },
      ],
    };

    expect(sameScore(theirs, { sets: [...theirs.sets] })).toBe(true);
    expect(
      sameScore(theirs, {
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 3 },
        ],
      }),
    ).toBe(false);
    expect(sameScore(theirs, { sets: [{ a: 6, b: 4 }] })).toBe(false);
  });
});

describe('which side took a score', () => {
  it('counts sets rather than points, which is what marks the winner’s row', () => {
    const score = {
      sets: [
        { a: 6, b: 4 },
        { a: 3, b: 6 },
        { a: 6, b: 2 },
      ],
    };

    expect(setsWon(score, 'a')).toBe(2);
    expect(setsWon(score, 'b')).toBe(1);
  });
});
