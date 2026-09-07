/**
 * The week the search ran on, drawn against the week the profile holds — **6.8's diff variant,
 * as rows.**
 *
 * The sheet's own sentence names two marks (*"A plus is new, a dash is one you dropped"*), and
 * this is what puts them on the grid: a cell that was ticked before and still is draws the
 * tick, one the search added draws a **plus**, one it dropped draws a **dash**, and one that
 * was off and stayed off draws nothing at all. Three shapes, because the prototype's volt ring
 * and 45 % opacity were colour as the only signal — Part 13's prohibition twice over — and the
 * component retired them.
 *
 * **The rule is a set membership and not a comparison of two lists.** `domain/workingWeek`
 * says why a week is compared as a set: order is not a fact about a week, and a cell can
 * arrive twice off the wire. The same reasoning governs one cell at a time here.
 *
 * **All twenty-one cells are built, including the ones with nothing to say.** The grid is a
 * shape a reader recognises, so the empty cells are what makes the marked ones legible; what
 * `off` costs a *listener* is nothing, because `availabilityDiffCellLabel` hides it rather
 * than announcing it empty (§20.7).
 *
 * A **cleared week** therefore draws as every profile cell dashed and nothing else — the whole
 * grid is the dropped half, which is exactly what §12's second body says in words.
 */

import type { AvailabilityDiffRow, AvailabilityDiffState } from '@/shared/ui';
import { dayLabel } from '@/shared/vocabulary/availabilityPresentation';
import { isTicked, DAY_PARTS, WEEKDAYS, type WeekCell } from '@/shared/vocabulary/week';

import { availabilityDiffCellLabel } from './accessibilityPresentation';

/**
 * What one cell says about itself, from the two weeks it is in or out of.
 *
 * The four states are the component's own union, so a fifth would fail to compile here and in
 * the label table beside it rather than drawing an unmarked cell.
 */
export function weekDiffState(
  cell: WeekCell,
  ran: readonly WeekCell[],
  profile: readonly WeekCell[],
): AvailabilityDiffState {
  const now = isTicked(ran, cell);
  const before = isTicked(profile, cell);

  if (now && before) return 'on';
  if (now) return 'added';
  return before ? 'dropped' : 'off';
}

/**
 * The seven rows the sheet draws, each with its three cells — the same geometry the editor
 * has, because it is the same component in its other mode.
 */
export function weekDiffRows(
  ran: readonly WeekCell[],
  profile: readonly WeekCell[],
): readonly AvailabilityDiffRow[] {
  return WEEKDAYS.map((day) => ({
    key: `${day}`,
    label: dayLabel(day),
    cells: DAY_PARTS.map((part) => {
      const cell: WeekCell = { day, part };
      const state = weekDiffState(cell, ran, profile);
      const spoken = availabilityDiffCellLabel(cell, state);

      return {
        key: `${day}-${part}`,
        state,
        // Omitted is **hidden**, never announced empty: a slot that was off and stayed off
        // has nothing to tell a listener, and twenty-one of those between the ones that do
        // is the double announcement the column heads are hidden to avoid.
        ...(spoken === undefined ? {} : { accessibilityLabel: spoken }),
      };
    }),
  }));
}
