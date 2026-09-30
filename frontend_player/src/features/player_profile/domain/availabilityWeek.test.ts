/**
 * The week's toggle and count rules, with no renderer.
 *
 * The grid is the only place a time preference is expressed anywhere in this product, and
 * the profile editor will express it from a screen that looks nothing like the onboarding
 * step — so what a press and a drag do, and what a count means, are proved here rather than
 * through a hundred and twelve rectangles.
 *
 * **The absences are the point.** There is no floor, no ceiling and no cell that stops
 * toggling, so the cases that would fail a rule borrowed from `socialTagSelection` — a press
 * on the last hour left, a press at zero — are the ones written down.
 */

import type { WeeklyHour } from './ProfileDraft';
import {
  WEEK_CELLS,
  everyCell,
  isTicked,
  paintCells,
  sameWeek,
  toggleCell,
  weekStanding,
} from './availabilityWeek';

/** Every cell of the grid, ticked — the far end, and a legal answer like any other. */
const WHOLE_WEEK: readonly WeeklyHour[] = everyCell();

describe('the shape of the week', () => {
  // The seven days and the sixteen hours are `@/shared/vocabulary/week`'s, and their order is
  // asserted there — Play reads the same week back as overlap.
  it('is a hundred and twelve independent answers — seven days of sixteen hours', () => {
    expect(WEEK_CELLS).toBe(112);
    // The count and the cells are stated separately, so the two can disagree and be caught.
    expect(everyCell()).toHaveLength(WEEK_CELLS);
  });

  it('is drawn Monday to Sunday along each hour, 07:00 first', () => {
    // The grid's reading order: an hour's row, left to right, then the next row down.
    expect(everyCell().slice(0, 8)).toEqual([
      { day: 1, hour: 7 },
      { day: 2, hour: 7 },
      { day: 3, hour: 7 },
      { day: 4, hour: 7 },
      { day: 5, hour: 7 },
      { day: 6, hour: 7 },
      { day: 7, hour: 7 },
      { day: 1, hour: 8 },
    ]);
    expect(everyCell().at(-1)).toEqual({ day: 7, hour: 22 });
  });
});

describe('ticking a cell', () => {
  it('adds it in the order the player pressed', () => {
    // Press order, exactly as the tag selection keeps it: what a player ticked first is a
    // fact about them, and sorting to the grid's order would throw it away before the
    // commit ever saw it.
    expect(toggleCell([], { day: 3, hour: 19 })).toEqual([{ day: 3, hour: 19 }]);

    expect(toggleCell([{ day: 3, hour: 19 }], { day: 1, hour: 9 })).toEqual([
      { day: 3, hour: 19 },
      { day: 1, hour: 9 },
    ]);
  });

  it('tells one cell from every other cell that shares a day or an hour', () => {
    const week = toggleCell([], { day: 1, hour: 9 });

    expect(isTicked(week, { day: 1, hour: 9 })).toBe(true);
    // The same hour on another day, and another hour of the same day. Independent answers
    // are the whole reason there is no row and no column behaviour.
    expect(isTicked(week, { day: 2, hour: 9 })).toBe(false);
    expect(isTicked(week, { day: 1, hour: 10 })).toBe(false);
  });

  it('leaves the week it was given untouched', () => {
    const before: readonly WeeklyHour[] = [{ day: 1, hour: 9 }];

    toggleCell(before, { day: 5, hour: 14 });

    expect(before).toEqual([{ day: 1, hour: 9 }]);
  });

  it('has no ceiling: the last hour of the week is taken like the first', () => {
    const allButOne = WHOLE_WEEK.slice(0, -1);

    expect(toggleCell(allButOne, { day: 7, hour: 22 })).toHaveLength(WEEK_CELLS);
  });
});

describe('unticking a cell', () => {
  it('drops it and leaves the rest in order', () => {
    const week: readonly WeeklyHour[] = [
      { day: 1, hour: 9 },
      { day: 3, hour: 19 },
      { day: 6, hour: 14 },
    ];

    expect(toggleCell(week, { day: 3, hour: 19 })).toEqual([
      { day: 1, hour: 9 },
      { day: 6, hour: 14 },
    ]);
  });

  it('has no floor: the last cell comes off like any other', () => {
    // Nothing here refuses. An empty week is a complete answer, so there is no state a
    // press could be turned away from — which is why this returns a week rather than the
    // three-armed change `toggleSocialTag` has to return.
    expect(toggleCell([{ day: 1, hour: 9 }], { day: 1, hour: 9 })).toEqual([]);
  });

  it('empties a full week one cell at a time', () => {
    const emptied = WHOLE_WEEK.reduce<readonly WeeklyHour[]>(
      (week, cell) => toggleCell(week, cell),
      WHOLE_WEEK,
    );

    expect(emptied).toEqual([]);
  });
});

describe('a drag across the grid', () => {
  // The rule is `@/shared/vocabulary/week`'s and proved there; this is the step's reading of
  // it — a run painted from nothing is a week the floor is met by, and a run cleared off the
  // only hours there were is the empty week the floor refuses.
  it('ticks a run of hours in one gesture, and the week then stands on them', () => {
    const run: readonly WeeklyHour[] = [
      { day: 2, hour: 18 },
      { day: 2, hour: 19 },
      { day: 2, hour: 20 },
    ];

    expect(weekStanding(paintCells([], run, true))).toEqual({ kind: 'ticked', count: 3 });
    expect(weekStanding(paintCells(run, run, false))).toEqual({ kind: 'empty' });
  });
});

describe('what a week counts as', () => {
  it('is empty at nothing ticked', () => {
    // Not *short*, and not a refusal: blank means no preference, never leave me out, and
    // the standing exists to give the footnote its words rather than to block anything.
    expect(weekStanding([])).toEqual({ kind: 'empty' });
  });

  it('carries the count once anything is ticked', () => {
    expect(weekStanding([{ day: 1, hour: 9 }])).toEqual({ kind: 'ticked', count: 1 });
    expect(weekStanding(WHOLE_WEEK)).toEqual({ kind: 'ticked', count: WEEK_CELLS });
  });
});

/**
 * **Whether a draft is worth saving** — the You tab's *Your week* holds a draft until its
 * button, and the button is shut while the draft is the week the profile already holds. The
 * comparison is by cell and never by order: the profile answers in its own reading order
 * whatever order the player pressed in, and a week re-sorted is not a week changed.
 */
describe('two weeks being the same week', () => {
  const TUESDAY_EVENING: WeeklyHour = { day: 2, hour: 19 };
  const SATURDAY_MORNING: WeeklyHour = { day: 6, hour: 9 };

  it('is true of the same cells in any order', () => {
    expect(sameWeek([TUESDAY_EVENING, SATURDAY_MORNING], [SATURDAY_MORNING, TUESDAY_EVENING])).toBe(
      true,
    );
    expect(sameWeek([], [])).toBe(true);
  });

  it('is false when a cell is ticked on one side only', () => {
    expect(sameWeek([TUESDAY_EVENING], [TUESDAY_EVENING, SATURDAY_MORNING])).toBe(false);
    expect(sameWeek([TUESDAY_EVENING], [])).toBe(false);
  });

  it('reads a cell pressed twice on the draft as one cell', () => {
    // A draft is built by `toggleCell`, which never holds a cell twice — but the rule must not
    // depend on that, because the profile's answer is what it is compared against.
    expect(sameWeek([TUESDAY_EVENING, TUESDAY_EVENING], [TUESDAY_EVENING])).toBe(true);
  });
});
