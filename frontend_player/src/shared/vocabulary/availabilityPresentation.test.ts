/**
 * What a day, a part of a day and one cell of the week are called.
 *
 * Two things here are load-bearing rather than decorative. **Each cell names its day and its
 * part of the day**, because a screen reader gets nothing from the row a cell is in or the
 * column it is under. And **all twenty-one names are distinct**, which is what stops two
 * cells announcing alike.
 *
 * The third is the promotion itself: the sentence form — *Tue evening* — is built from the
 * same two tables the grid draws, so a reason line and a column head can never disagree
 * about which day is Thursday.
 */

import { cellLabel, dayLabel, dayPartHead, slotName } from './availabilityPresentation';
import { DAY_PARTS, WEEKDAYS, type WeekCell } from './week';

const EVERY_CELL: readonly WeekCell[] = WEEKDAYS.flatMap((day) =>
  DAY_PARTS.map((part) => ({ day, part })),
);

describe('naming a cell', () => {
  it('names the day and the part of the day, in that order', () => {
    expect(cellLabel({ day: 1, part: 'morning' })).toBe('Monday morning');
    expect(cellLabel({ day: 7, part: 'evening' })).toBe('Sunday evening');
  });

  it('gives all twenty-one a name of their own', () => {
    const names = EVERY_CELL.map(cellLabel);

    expect(new Set(names).size).toBe(21);
  });
});

describe('the labels around the grid', () => {
  it('shortens each day for a column capped at a quarter of the content', () => {
    expect(WEEKDAYS.map(dayLabel)).toEqual(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
  });

  it('heads the three columns with the parts of the day', () => {
    expect(DAY_PARTS.map(dayPartHead)).toEqual(['Morning', 'Afternoon', 'Evening']);
  });
});

describe('a cell inside a sentence', () => {
  it('is the short day and the part in lower case', () => {
    // `the-words.md` §6.2's `next {slot}`: a phrase in a line of prose, not a heading over
    // a column.
    expect(slotName({ day: 2, part: 'evening' })).toBe('Tue evening');
  });

  it('is built from the same tables the grid draws, never a third list', () => {
    // The whole reason the tables were promoted rather than copied: one Thursday.
    for (const cell of EVERY_CELL) {
      expect(slotName(cell).startsWith(dayLabel(cell.day))).toBe(true);
      expect(slotName(cell).endsWith(cell.part)).toBe(true);
    }
  });
});
