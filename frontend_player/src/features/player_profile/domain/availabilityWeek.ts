/**
 * The player's ordinary week: which of twenty-one cells are ticked, and what a tick does.
 *
 * **Seven days by three parts of the day, and that is the finest precision this product
 * produces.** No clock time, no date, no calendar — a cell is a standing preference about
 * an ordinary week, not an entry in a diary, and there is nothing here for an hour to be
 * stored in.
 *
 * ## No ceiling, and no cell that refuses — but there is a floor
 *
 * Every cell toggles, always, in both directions. That is why this returns a week rather
 * than the three-armed change `toggleSocialTag` returns: there is no state a *press* could
 * be turned away from, so a `refused` arm would be a type describing a rule the domain does
 * not have. A full week is legal, and the last tick comes off like any other — the floor
 * blocks continuing, never correcting, exactly as the tag ceiling blocks adding and never
 * removing.
 *
 * **The floor is one cell of the twenty-one** (ADR-0102), and it binds where a week is
 * *given*: the step will not continue on an empty one, and the commit refuses one. It is
 * not served — it is fixed — so unlike the tag bounds it is a rule this side may hold, and
 * `weekStanding` below is the whole of where it is held. The step draws its control from
 * that answer and `readyToCommit` reports a missing answer from it, so there is no second
 * place a floor of one is written and no second place to forget to move it.
 *
 * **There is no bulk selection either**, and it is absent from this file rather than merely
 * unbuilt in the screen: a row, a column or a *weekends* shortcut is a claim about what
 * players want that this product has no evidence for, and describing an irregular week is
 * the whole reason the grid is twenty-one independent answers instead of three.
 *
 * ## No renderer, no store
 *
 * The onboarding step is the first screen to obey these rules and the profile editor will be
 * the second — the same week, the same toggle, a different screen. So they are functions of
 * a week, which is also what makes them testable without mounting anything.
 */

import type { AvailabilitySlot, DayPart, Weekday } from './ProfileDraft';

/**
 * Monday first, as ISO weekdays.
 *
 * The order is the contract's as well as the design system's: `AvailabilitySlotResource`
 * numbers days 1-7 as ISO weekdays and says the grid is Monday-first, so nothing on either
 * side of the wire sorts.
 */
export const WEEKDAYS: readonly Weekday[] = [1, 2, 3, 4, 5, 6, 7];

/** The three parts of the day, in the order `DayPart` declares them. */
export const DAY_PARTS: readonly DayPart[] = ['morning', 'afternoon', 'evening'];

/** Twenty-one — the whole grid, and the largest a week can be. */
export const WEEK_CELLS = WEEKDAYS.length * DAY_PARTS.length;

/** Every cell of the grid, in the order it is drawn: Monday first, morning first. */
export function everyCell(): readonly AvailabilitySlot[] {
  return WEEKDAYS.flatMap((day) => DAY_PARTS.map((part) => ({ day, part })));
}

/** Whether two cells are the same cell — the identity everything below turns on. */
function sameCell(one: AvailabilitySlot, other: AvailabilitySlot): boolean {
  return one.day === other.day && one.part === other.part;
}

export function isTicked(week: readonly AvailabilitySlot[], cell: AvailabilitySlot): boolean {
  return week.some((ticked) => sameCell(ticked, cell));
}

/**
 * Press a cell: tick it, or untick it.
 *
 * Ticks are appended in **press order**, exactly as the tag selection keeps them. What a
 * player ticked first is a fact about them, and re-sorting to the grid's own order would
 * throw it away before the commit ever saw it.
 */
export function toggleCell(
  week: readonly AvailabilitySlot[],
  cell: AvailabilitySlot,
): readonly AvailabilitySlot[] {
  if (isTicked(week, cell)) {
    return week.filter((ticked) => !sameCell(ticked, cell));
  }
  return [...week, cell];
}

/**
 * What this week amounts to — the two things a screen has anything to say about.
 *
 * A **count**, never a sentence: the words belong to whichever screen is asking, and there
 * are going to be two of them. `empty` is its own arm rather than a count of nought because
 * the empty week is the one the product has something to say about — and, since ADR-0102,
 * the one a step will not continue from. A screen that had to compare a number to zero
 * would be re-deciding the floor every time it drew a control.
 */
export type WeekStanding =
  { readonly kind: 'empty' } | { readonly kind: 'ticked'; readonly count: number };

export function weekStanding(week: readonly AvailabilitySlot[]): WeekStanding {
  return week.length === 0 ? { kind: 'empty' } : { kind: 'ticked', count: week.length };
}
