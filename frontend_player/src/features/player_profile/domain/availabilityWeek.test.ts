/**
 * The week's toggle and count rules, with no renderer.
 *
 * The grid is the only place a time preference is expressed anywhere in this product, and
 * the profile editor will express it from a screen that looks nothing like the onboarding
 * step — so what a press does, and what a count means, are proved here rather than through
 * twenty-one rectangles.
 *
 * **The absences are the point.** There is no floor, no ceiling and no cell that stops
 * toggling, so the cases that would fail a rule borrowed from `socialTagSelection` — a press
 * on the twenty-second, a press at zero — are the ones written down.
 */

import type { AvailabilitySlot } from './ProfileDraft';
import {
  WEEK_CELLS,
  everyCell,
  isTicked,
  sameWeek,
  toggleCell,
  weekStanding,
} from './availabilityWeek';

/** Every cell of the grid, ticked — the far end, and a legal answer like any other. */
const WHOLE_WEEK: readonly AvailabilitySlot[] = everyCell();

describe('the shape of the week', () => {
  // The seven days and the three parts are `@/shared/vocabulary/week`'s, and their order is
  // asserted there — Play reads the same week back as overlap.
  it('is twenty-one independent answers', () => {
    expect(WEEK_CELLS).toBe(21);
    // The count and the cells are stated separately, so the two can disagree and be caught.
    expect(everyCell()).toHaveLength(WEEK_CELLS);
  });
});

describe('ticking a cell', () => {
  it('adds it in the order the player pressed', () => {
    // Press order, exactly as the tag selection keeps it: what a player ticked first is a
    // fact about them, and sorting to the grid's order would throw it away before the
    // commit ever saw it.
    expect(toggleCell([], { day: 3, part: 'evening' })).toEqual([{ day: 3, part: 'evening' }]);

    expect(toggleCell([{ day: 3, part: 'evening' }], { day: 1, part: 'morning' })).toEqual([
      { day: 3, part: 'evening' },
      { day: 1, part: 'morning' },
    ]);
  });

  it('tells one cell from every other cell that shares a day or a part', () => {
    const week = toggleCell([], { day: 1, part: 'morning' });

    expect(isTicked(week, { day: 1, part: 'morning' })).toBe(true);
    // The same part on another day, and another part of the same day. Twenty-one
    // independent answers is the whole reason there is no row and no column behaviour.
    expect(isTicked(week, { day: 2, part: 'morning' })).toBe(false);
    expect(isTicked(week, { day: 1, part: 'evening' })).toBe(false);
  });

  it('leaves the week it was given untouched', () => {
    const before: readonly AvailabilitySlot[] = [{ day: 1, part: 'morning' }];

    toggleCell(before, { day: 5, part: 'afternoon' });

    expect(before).toEqual([{ day: 1, part: 'morning' }]);
  });

  it('has no ceiling: the twenty-first tick is taken like the first', () => {
    const twenty = WHOLE_WEEK.slice(0, 20);

    expect(toggleCell(twenty, { day: 7, part: 'evening' })).toHaveLength(21);
  });
});

describe('unticking a cell', () => {
  it('drops it and leaves the rest in order', () => {
    const week: readonly AvailabilitySlot[] = [
      { day: 1, part: 'morning' },
      { day: 3, part: 'evening' },
      { day: 6, part: 'afternoon' },
    ];

    expect(toggleCell(week, { day: 3, part: 'evening' })).toEqual([
      { day: 1, part: 'morning' },
      { day: 6, part: 'afternoon' },
    ]);
  });

  it('has no floor: the last cell comes off like any other', () => {
    // Nothing here refuses. An empty week is a complete answer, so there is no state a
    // press could be turned away from — which is why this returns a week rather than the
    // three-armed change `toggleSocialTag` has to return.
    expect(toggleCell([{ day: 1, part: 'morning' }], { day: 1, part: 'morning' })).toEqual([]);
  });

  it('empties a full week one cell at a time', () => {
    const emptied = WHOLE_WEEK.reduce<readonly AvailabilitySlot[]>(
      (week, cell) => toggleCell(week, cell),
      WHOLE_WEEK,
    );

    expect(emptied).toEqual([]);
  });
});

describe('what a week counts as', () => {
  it('is empty at nothing ticked', () => {
    // Not *short*, and not a refusal: blank means no preference, never leave me out, and
    // the standing exists to give the footnote its words rather than to block anything.
    expect(weekStanding([])).toEqual({ kind: 'empty' });
  });

  it('carries the count once anything is ticked', () => {
    expect(weekStanding([{ day: 1, part: 'morning' }])).toEqual({ kind: 'ticked', count: 1 });
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
  const TUESDAY_EVENING: AvailabilitySlot = { day: 2, part: 'evening' };
  const SATURDAY_MORNING: AvailabilitySlot = { day: 6, part: 'morning' };

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
