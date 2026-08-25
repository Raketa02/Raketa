/**
 * The words on the availability step.
 *
 * Two of them are load-bearing rather than decorative and are asserted as such: **each cell
 * names its day and its part of the day**, because a screen reader gets nothing from the row
 * a cell is in or the column it is under; and **the empty week's footnote says no
 * preference, never unavailable**, which is the one sentence standing between a blank grid
 * and a player believing they have opted out of something.
 */

import { DAY_PARTS, WEEKDAYS, WEEK_CELLS, everyCell } from '../domain/availabilityWeek';

import {
  AVAILABILITY_PROMISE_BODY,
  availabilityFootnote,
  cellLabel,
  dayLabel,
  dayPartHead,
} from './availabilityPresentation';

describe('naming a cell', () => {
  it('names the day and the part of the day, in that order', () => {
    expect(cellLabel({ day: 1, part: 'morning' })).toBe('Monday morning');
    expect(cellLabel({ day: 7, part: 'evening' })).toBe('Sunday evening');
  });

  it('gives all twenty-one a name of their own', () => {
    const names = everyCell().map(cellLabel);

    expect(new Set(names).size).toBe(WEEK_CELLS);
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

describe('the footnote', () => {
  it('says an empty week is no preference and never unavailable', () => {
    // The whole product principle, in the one place a player meets it: *blank means no
    // preference, never leave me out*. It also names what the blank costs, because a
    // consequence nobody states is one a player finds out about later.
    const empty = availabilityFootnote({ kind: 'empty' });

    expect(empty).toMatch(/no preference/i);
    expect(empty).toMatch(/never unavailable/i);
  });

  it('names the count once anything is ticked', () => {
    expect(availabilityFootnote({ kind: 'ticked', count: 1 })).toMatch(/^1 slot ticked/);
    expect(availabilityFootnote({ kind: 'ticked', count: 4 })).toMatch(/^4 slots ticked/);
  });

  it('stays inside the two lines the slot reserves', () => {
    // 6.8 reserves two lines of `tiny` under the grid and says a third line is an
    // amendment, not a copy tweak — so the length is a rule, not a preference. Roughly 58
    // characters fit on a line of `tiny` across the narrowest phone's content width.
    const every = [
      availabilityFootnote({ kind: 'empty' }),
      availabilityFootnote({ kind: 'ticked', count: 1 }),
      availabilityFootnote({ kind: 'ticked', count: WEEK_CELLS }),
    ];

    for (const line of every) expect(line.length).toBeLessThanOrEqual(116);
  });
});

describe('what the step promises', () => {
  it('says the week is never shown to anybody as a calendar', () => {
    // The step's own claim about what it is doing with the answer. A grid that looked like
    // a diary and was never said not to be one is the copy defect nobody re-reads.
    expect(AVAILABILITY_PROMISE_BODY).toMatch(/calendar/i);
  });
});
