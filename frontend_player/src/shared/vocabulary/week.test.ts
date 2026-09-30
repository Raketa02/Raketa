/**
 * The week's own shape — seven days in one order, sixteen hours in one order — and the two
 * presses over it: a tap, and a drag that paints a run.
 *
 * Both orders are the **contract's** as well as the design system's, which is why they are
 * asserted at all — `WeeklyHourResource` numbers days 1-7 as ISO weekdays, Monday first, and
 * an hour by the wall-clock hour its cell starts at, 7 to 22, so nothing on either side of the
 * wire sorts.
 */

import { HOURS, WEEKDAYS, paintCells, toggleCell, weeklyHourAt, type WeeklyHour } from './week';

const TUE_19: WeeklyHour = { day: 2, hour: 19 };
const TUE_20: WeeklyHour = { day: 2, hour: 20 };
const TUE_21: WeeklyHour = { day: 2, hour: 21 };
const SAT_9: WeeklyHour = { day: 6, hour: 9 };

describe('the shape of the week', () => {
  it('runs Monday to Sunday as ISO weekdays', () => {
    expect(WEEKDAYS).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });

  it('runs sixteen hours, the first starting at 07:00 and the last at 22:00', () => {
    expect(HOURS).toEqual([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]);
  });
});

describe('the hour at a place on the grid', () => {
  // 6.8 draws the hours down and the days across, 07:00 and Monday in the top corner.
  it('reads the row as the hour and the column as the day', () => {
    expect(weeklyHourAt(0, 0)).toEqual({ day: 1, hour: 7 });
    expect(weeklyHourAt(12, 1)).toEqual({ day: 2, hour: 19 });
    expect(weeklyHourAt(15, 6)).toEqual({ day: 7, hour: 22 });
  });

  it('is no hour at all off the grid', () => {
    expect(weeklyHourAt(16, 0)).toBeUndefined();
    expect(weeklyHourAt(0, 7)).toBeUndefined();
    expect(weeklyHourAt(-1, 0)).toBeUndefined();
  });
});

describe('a tap', () => {
  it('ticks an hour that was off, after the ones already ticked', () => {
    expect(toggleCell([SAT_9], TUE_19)).toEqual([SAT_9, TUE_19]);
  });

  it('unticks an hour that was on, and only that hour', () => {
    expect(toggleCell([TUE_19, TUE_20], TUE_19)).toEqual([TUE_20]);
  });

  it('tells two hours of one day apart', () => {
    expect(toggleCell([TUE_19], TUE_20)).toEqual([TUE_19, TUE_20]);
  });
});

describe('a drag that paints', () => {
  it('ticks every hour of the run that was off, in the order the finger crossed them', () => {
    expect(paintCells([SAT_9], [TUE_19, TUE_20, TUE_21], true)).toEqual([
      SAT_9,
      TUE_19,
      TUE_20,
      TUE_21,
    ]);
  });

  it('leaves an hour already on where it is, rather than ticking it twice', () => {
    expect(paintCells([TUE_20], [TUE_19, TUE_20, TUE_21], true)).toEqual([TUE_20, TUE_19, TUE_21]);
  });

  it('clears every hour of the run, and nothing outside it', () => {
    expect(paintCells([SAT_9, TUE_19, TUE_20, TUE_21], [TUE_19, TUE_20], false)).toEqual([
      SAT_9,
      TUE_21,
    ]);
  });

  /**
   * A drag reports the run it has painted so far, whole, on every move — so the same run
   * arrives again and again, one hour longer each time. Painting it twice has to be painting
   * it once, or a screen one render behind the finger would drop the hours it had not drawn.
   */
  it('lands the same week however many times the same run is painted', () => {
    const once = paintCells([SAT_9], [TUE_19, TUE_20], true);

    expect(paintCells(once, [TUE_19, TUE_20], true)).toEqual(once);
    expect(paintCells(paintCells(once, [TUE_19], false), [TUE_19], false)).toEqual(
      paintCells(once, [TUE_19], false),
    );
  });

  it('paints an hour the run crosses twice only once', () => {
    expect(paintCells([], [TUE_19, TUE_20, TUE_19], true)).toEqual([TUE_19, TUE_20]);
  });
});
