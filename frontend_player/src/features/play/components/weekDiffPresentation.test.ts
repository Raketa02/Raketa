/**
 * The diff grid: four states over a hundred and twelve hours, and the one week where every mark
 * is a dash.
 */

import { HOURS, WEEKDAYS, type WeeklyHour } from '@/shared/vocabulary/week';

import { weekDiffRows, weekDiffState } from './weekDiffPresentation';

const TUESDAY_EVENING = { day: 2, hour: 19 } as const;
const SATURDAY_MORNING = { day: 6, hour: 9 } as const;
const MONDAY_MORNING = { day: 1, hour: 9 } as const;

const stateAt = (rows: ReturnType<typeof weekDiffRows>, cell: WeeklyHour) =>
  rows
    .find((row) => row.key === `${cell.hour}`)
    ?.cells.find((one) => one.key === `${cell.day}-${cell.hour}`);

describe('what one cell says about itself', () => {
  const profile = [TUESDAY_EVENING, SATURDAY_MORNING];

  it('is on where the search kept a cell the profile already had', () => {
    expect(weekDiffState(TUESDAY_EVENING, profile, profile)).toBe('on');
  });

  it('is added where the search ticked one the profile does not hold', () => {
    expect(weekDiffState(MONDAY_MORNING, [...profile, MONDAY_MORNING], profile)).toBe('added');
  });

  it('is dropped where the search left one behind', () => {
    expect(weekDiffState(SATURDAY_MORNING, [TUESDAY_EVENING], profile)).toBe('dropped');
  });

  it('is off where neither week ticked it', () => {
    expect(weekDiffState(MONDAY_MORNING, profile, profile)).toBe('off');
  });

  /**
   * A week is a **set**, and a cell arriving twice is the same cell. The comparison the
   * origin of every line-up rests on does not depend on the wire sending each one once.
   */
  it('reads a repeated cell as the one cell it names', () => {
    expect(weekDiffState(TUESDAY_EVENING, [TUESDAY_EVENING, TUESDAY_EVENING], [])).toBe('added');
  });
});

describe('the grid the sheet draws', () => {
  it('is the whole week, sixteen hours of seven days, whatever changed', () => {
    const rows = weekDiffRows([TUESDAY_EVENING], [TUESDAY_EVENING]);

    expect(rows).toHaveLength(HOURS.length);
    expect(rows[0]?.label).toBe('07:00');
    expect(rows.at(-1)?.label).toBe('22:00');
    for (const row of rows) expect(row.cells).toHaveLength(WEEKDAYS.length);
  });

  it('names the cells that changed and hides the ones that did not', () => {
    const rows = weekDiffRows(
      [TUESDAY_EVENING, MONDAY_MORNING],
      [TUESDAY_EVENING, SATURDAY_MORNING],
    );

    expect(stateAt(rows, MONDAY_MORNING)).toMatchObject({
      state: 'added',
      accessibilityLabel: 'Monday 09:00, newly added',
    });
    expect(stateAt(rows, SATURDAY_MORNING)).toMatchObject({
      state: 'dropped',
      accessibilityLabel: 'Saturday 09:00, dropped',
    });
    expect(stateAt(rows, TUESDAY_EVENING)).toMatchObject({
      state: 'on',
      accessibilityLabel: 'Tuesday 19:00',
    });
    // An unchanged, unticked hour tells a listener nothing, and a hundred of them between the
    // ones that changed is the announcement §20.7 hides.
    expect(stateAt(rows, { day: 4, hour: 14 })?.accessibilityLabel).toBeUndefined();
  });

  /** #277's second body, as a drawing: the whole grid is the dropped half. */
  it('draws a cleared week as all dash and nothing else', () => {
    const rows = weekDiffRows([], [TUESDAY_EVENING, SATURDAY_MORNING]);
    const marks = rows.flatMap((row) => row.cells.map((cell) => cell.state));

    expect(marks.filter((state) => state === 'dropped')).toHaveLength(2);
    expect(marks).not.toContain('on');
    expect(marks).not.toContain('added');
  });
});
