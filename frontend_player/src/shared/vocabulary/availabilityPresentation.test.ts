/**
 * What a day, an hour and one cell of the week are called.
 *
 * Two things here are load-bearing rather than decorative. **Each cell names its day and its
 * hour**, because a screen reader gets nothing from the row a cell is in or the column it is
 * under. And **all hundred and twelve names are distinct**, which is what stops two cells
 * announcing alike.
 *
 * The third is the promotion itself: the sentence form — *Tue 19:00* — is built from the same
 * two tables the grid draws, so a reason line and a column head can never disagree about which
 * day is Thursday or what 19:00 is written as.
 */

import { cellLabel, dayLabel, hourLabel } from './availabilityPresentation';
import { HOURS, WEEKDAYS, type WeeklyHour } from './week';

const EVERY_CELL: readonly WeeklyHour[] = HOURS.flatMap((hour) =>
  WEEKDAYS.map((day) => ({ day, hour })),
);

describe('naming a cell', () => {
  it('names the whole day and the hour the cell starts at, in that order', () => {
    expect(cellLabel({ day: 1, hour: 7 })).toBe('Monday 07:00');
    expect(cellLabel({ day: 7, hour: 22 })).toBe('Sunday 22:00');
  });

  it('gives all hundred and twelve a name of their own', () => {
    const names = EVERY_CELL.map(cellLabel);

    expect(new Set(names).size).toBe(112);
  });
});

describe('the labels around the grid', () => {
  it('shortens each day for a column seven share', () => {
    expect(WEEKDAYS.map(dayLabel)).toEqual(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
  });

  it('labels the sixteen rows with the hour each starts at, on the 24-hour clock', () => {
    expect(HOURS.map(hourLabel)).toEqual([
      '07:00',
      '08:00',
      '09:00',
      '10:00',
      '11:00',
      '12:00',
      '13:00',
      '14:00',
      '15:00',
      '16:00',
      '17:00',
      '18:00',
      '19:00',
      '20:00',
      '21:00',
      '22:00',
    ]);
  });
});
