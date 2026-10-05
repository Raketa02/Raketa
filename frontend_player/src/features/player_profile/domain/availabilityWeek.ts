/**
 * The player's ordinary week — their **weekly hours**: which of a hundred and twelve hours are
 * ticked, and what a tap and a drag do to them.
 *
 * **Seven days by sixteen hours, 07:00 to 23:00, and that is the finest precision this product
 * produces** ([ADR-0189](../../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
 * §5). No date, no minute, no calendar — a cell is a standing preference about an ordinary week,
 * not an entry in a diary; it is held by the hour because a court is booked by the hour.
 *
 * ## No ceiling, and no cell that refuses — but there is a floor
 *
 * Every cell toggles, always, in both directions. That is why this returns a week rather than
 * the three-armed change `toggleSocialTag` returns: there is no state a *press* could be turned
 * away from, so a `refused` arm would be a type describing a rule the domain does not have. A
 * full week is legal, and the last tick comes off like any other — the floor blocks continuing,
 * never correcting, exactly as the tag ceiling blocks adding and never removing.
 *
 * **The floor is one hour of the week** (ADR-0102), and it binds where a week is *given*: the
 * step will not continue on an empty one, and the commit refuses one. It is not served — it is
 * fixed — so unlike the tag bounds it is a rule this side may hold, and `weekStanding` below is
 * the whole of where it is held. The step draws its control from that answer and
 * `readyToCommit` reports a missing answer from it, so there is no second place a floor of one
 * is written and no second place to forget to move it.
 *
 * **A drag paints a run and is not bulk selection.** There is still no row tap, no column tap
 * and no *weekends* shortcut — a claim about what players want that this product has no
 * evidence for. Painting is a finger drawing the week it means, one hour at a time and as fast
 * as it likes, which is what a hundred and twelve independent answers need to be answerable at
 * all.
 *
 * ## No renderer, no store
 *
 * The onboarding step and the You tab's *Your week* obey these rules from two screens — the
 * same week, the same toggle, different chrome. So they are functions of a week, which is also
 * what makes them testable without mounting anything.
 */

import {
  HOURS,
  WEEKDAYS,
  isTicked,
  paintCells,
  toggleCell,
  type WeeklyHour,
} from '@/shared/vocabulary/week';

/**
 * A cell's identity, the tap over it and the drag across a run moved to
 * `shared/vocabulary/week` when Play became the second feature to toggle these cells — the
 * identical function, which is that folder's own test for what belongs in it. They are
 * re-exported here so this module stays the one place the availability step reads its rules
 * from; what stayed behind is the part that is a *claim about a profile*, which is the floor.
 */
export { isTicked, paintCells, toggleCell };

/** A hundred and twelve — the whole week, and the largest it can be. */
export const WEEK_CELLS = WEEKDAYS.length * HOURS.length;

/** Every cell of the grid, in the order it is drawn: 07:00 first, Monday to Sunday along it. */
export function everyCell(): readonly WeeklyHour[] {
  return HOURS.flatMap((hour) => WEEKDAYS.map((day) => ({ day, hour })));
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

export function weekStanding(week: readonly WeeklyHour[]): WeekStanding {
  return week.length === 0 ? { kind: 'empty' } : { kind: 'ticked', count: week.length };
}

/**
 * **Two weeks are the same week when they hold the same cells** — in any order, however many
 * times a cell appears.
 *
 * The You tab's *Your week* holds a draft until *Save*, and the button is shut while the draft
 * is the week the profile already holds: a save that changes nothing is a round trip for an
 * answer already in hand. By cell and never by order, because the profile answers in the
 * platform's own reading order whatever order the player pressed in
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 */
export function sameWeek(one: readonly WeeklyHour[], other: readonly WeeklyHour[]): boolean {
  const ticked = new Set(one.map(cellKey));
  const against = new Set(other.map(cellKey));
  if (ticked.size !== against.size) return false;
  return [...ticked].every((cell) => against.has(cell));
}

function cellKey(cell: WeeklyHour): string {
  return `${cell.day}-${cell.hour}`;
}
