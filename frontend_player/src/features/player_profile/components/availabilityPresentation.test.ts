/**
 * The words on the availability step.
 *
 * Three of them are load-bearing rather than decorative and are asserted as such: **each
 * cell names its day and its part of the day**, because a screen reader gets nothing from
 * the row a cell is in or the column it is under; **the floor is stated in words**, because
 * a required answer a player only meets as a dead control is a rule nobody explained; and
 * **the empty week's footnote never says the blank was counted**, which is the reading
 * ADR-0102 withdrew.
 */

import { DAY_PARTS, WEEKDAYS, WEEK_CELLS, everyCell } from '../domain/availabilityWeek';

import {
  AVAILABILITY_PROMISE_BODY,
  availabilityContinueLabel,
  availabilityEyebrow,
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

describe('the floor, in words', () => {
  it('states the rule in the eyebrow, beside how far through the part the player is', () => {
    // The tag step's settled shape: a player should learn what is wanted by reading the
    // screen, not by being stopped by it.
    const eyebrow = availabilityEyebrow();

    expect(eyebrow).toMatch(/Step 3 of 6/);
    expect(eyebrow).toMatch(/at least one/i);
  });

  it('names what is missing on the control, rather than leaving it merely grey', () => {
    expect(availabilityContinueLabel({ kind: 'empty' })).toMatch(/at least one/i);
  });

  it('says nothing but Continue once the floor is met, at one slot or at twenty-one', () => {
    // No countdown to run and no ceiling to warn about: the floor is one, so the control is
    // either asking for a tick or it is not.
    expect(availabilityContinueLabel({ kind: 'ticked', count: 1 })).toBe('Continue');
    expect(availabilityContinueLabel({ kind: 'ticked', count: WEEK_CELLS })).toBe('Continue');
  });
});

describe('the footnote', () => {
  it('says an empty week is never unavailable, and never that it was counted', () => {
    // The half that survives ADR-0102: *blank means never leave me out*. The half that does
    // not is the cost the line used to name — *it leaves no overlap for anyone to share* was
    // a measured zero invented out of silence, which is exactly what the record withdrew.
    const empty = availabilityFootnote({ kind: 'empty' });

    expect(empty).toMatch(/never that you are unavailable/i);
    expect(empty).not.toMatch(/no overlap/i);
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
