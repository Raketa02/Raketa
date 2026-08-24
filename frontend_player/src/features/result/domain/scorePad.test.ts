/**
 * The instrument, on its own.
 *
 * Everything here is about the **pad** and nothing about a match: which cell a key
 * lands in, where the cursor goes, and which rows are finished enough to send. The
 * pad holds no rule about what a real score is — that is the server's permissive
 * validator, and this app holds no second opinion about it.
 */

import type { ScoreLine } from '@/features/now/types';

import {
  PAD_MAX,
  PAD_ROWS,
  clearRowInPad,
  emptyPad,
  padFrom,
  padHasUnfinishedRow,
  padIsSendable,
  padSets,
  selectInPad,
  typeInPad,
  type ScorePad,
} from './scorePad';

/** Type a run of numbers from wherever the cursor is. */
function typeAll(pad: ScorePad, values: readonly number[]): ScorePad {
  return values.reduce(typeInPad, pad);
}

describe('the pad’s own shape', () => {
  it('offers five rows and tops out at badminton’s highest number', () => {
    // Both are pinned to their literals rather than compared against themselves. A
    // constant compared against itself is a test that cannot fail — widen the pad
    // and both sides move together, and nobody finds out until a padel player is
    // shown a key for 30.
    expect(PAD_ROWS).toBe(5);
    expect(PAD_MAX).toBe(21);
    expect(emptyPad().rows).toHaveLength(5);
  });

  it('starts empty, on the first cell, with nothing to send', () => {
    const pad = emptyPad();

    expect(pad.active).toEqual({ row: 0, side: 0 });
    expect(padSets(pad)).toEqual([]);
    expect(padIsSendable(pad)).toBe(false);
  });
});

describe('typing', () => {
  it('fills her side then theirs, then moves to the next set', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3]);

    expect(pad.rows[0]).toEqual([6, 4]);
    expect(pad.rows[1]).toEqual([3, undefined]);
    expect(pad.active).toEqual({ row: 1, side: 1 });
  });

  it('stops on the last cell rather than wrapping to the first', () => {
    // Wrapping would silently overwrite the opening set on the next key press,
    // which is the one edit a player would never notice she had made.
    const full = typeAll(emptyPad(), [6, 4, 6, 4, 6, 4, 6, 4, 6, 4]);

    expect(full.active).toEqual({ row: PAD_ROWS - 1, side: 1 });

    const once = typeInPad(full, 9);

    expect(once.rows[0]).toEqual([6, 4]);
    expect(once.rows[PAD_ROWS - 1]).toEqual([6, 9]);
  });

  it('retypes the cell she selected, and nothing else', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3, 6]);
    const corrected = typeInPad(selectInPad(pad, { row: 0, side: 1 }), 2);

    expect(corrected.rows[0]).toEqual([6, 2]);
    expect(corrected.rows[1]).toEqual([3, 6]);
  });
});

describe('what may be sent', () => {
  it('sends the finished rows in the order they were typed', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3, 6, 6, 2]);

    expect(padSets(pad)).toEqual([
      [6, 4],
      [3, 6],
      [6, 2],
    ]);
  });

  it('refuses to send while one row is holding a single number', () => {
    // Sending it would mean choosing a number she did not type. The screen says so
    // rather than leaving a missing button to be interpreted.
    const pad = typeAll(emptyPad(), [6, 4, 3]);

    expect(padHasUnfinishedRow(pad)).toBe(true);
    expect(padIsSendable(pad)).toBe(false);
    expect(padSets(pad)).toEqual([[6, 4]]);
  });

  it('sends once a row is finished and nothing is half-typed', () => {
    const pad = typeAll(emptyPad(), [6, 4]);

    expect(padHasUnfinishedRow(pad)).toBe(false);
    expect(padIsSendable(pad)).toBe(true);
  });

  it('sends a zero, because a side that won no games scored none', () => {
    // `0` against `6` is a real set and the pad must be able to express it. What no
    // format produces is `0-0`, and that is the **server's** refusal rather than
    // this one: the pad has no opinion about which numbers make a match.
    const pad = typeAll(emptyPad(), [6, 0]);

    expect(padIsSendable(pad)).toBe(true);
    expect(padSets(pad)).toEqual([[6, 0]]);
  });
});

describe('clearing', () => {
  it('empties the whole row, so the pad never holds the shape it refuses to send', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3, 6]);
    const cleared = clearRowInPad(selectInPad(pad, { row: 1, side: 1 }));

    expect(cleared.rows[1]).toEqual([undefined, undefined]);
    expect(padHasUnfinishedRow(cleared)).toBe(false);
    expect(padSets(cleared)).toEqual([[6, 4]]);
  });

  it('is the only way a score gets shorter', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3, 6, 6, 2]);
    const cleared = clearRowInPad(selectInPad(pad, { row: 2, side: 0 }));

    expect(padSets(cleared)).toHaveLength(2);
  });

  it('puts the cursor back on the row it emptied', () => {
    const pad = typeAll(emptyPad(), [6, 4, 3, 6]);
    const cleared = clearRowInPad(selectInPad(pad, { row: 0, side: 1 }));

    expect(cleared.active).toEqual({ row: 0, side: 0 });
  });
});

describe('a pad opened on what is already there', () => {
  const onTheTable: ScoreLine = {
    sides: [{ players: ['Ada'] }, { players: ['Marta'] }],
    sets: [
      { first: 6, second: 4 },
      { first: 3, second: 6 },
    ],
  };

  it('holds the score as it arrived, viewer-first, with no flip', () => {
    // The server put her side first and `first` is hers. Flipping here would be a
    // second answer to *whose 6 was that*.
    const pad = padFrom(onTheTable);

    expect(pad.rows[0]).toEqual([6, 4]);
    expect(pad.rows[1]).toEqual([3, 6]);
    expect(padSets(pad)).toEqual([
      [6, 4],
      [3, 6],
    ]);
  });

  it('keeps the spare rows empty, so a correction can add a set', () => {
    const pad = padFrom(onTheTable);

    expect(pad.rows).toHaveLength(PAD_ROWS);
    expect(pad.rows[2]).toEqual([undefined, undefined]);
  });

  it('drops sets beyond what the pad can hold rather than growing', () => {
    // A score longer than the pad cannot arrive from this app, and a pad that grew
    // to fit one would be an instrument whose shape depended on the answer.
    const long: ScoreLine = {
      sides: onTheTable.sides,
      sets: Array.from({ length: PAD_ROWS + 2 }, () => ({ first: 6, second: 4 })),
    };

    expect(padFrom(long).rows).toHaveLength(PAD_ROWS);
  });
});
