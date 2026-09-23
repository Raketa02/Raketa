/**
 * The availability grid, drawn from a week — **the control, without the onboarding around it.**
 *
 * The availability step and the You tab's *Your week* draw the same grid from the same rule:
 * seven days down, three parts of the day across, Monday first, a cell ticked where the week
 * holds it (6.8). What differs between the two is everything *around* the grid — the step's
 * eyebrow with its floor and its *Continue*, the tab's *Save your week* and *Clear all* — so
 * the mapping from a week to the grid's rows is here, once, and each screen composes it under
 * its own chrome ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, first consequence).
 *
 * Nothing here decides anything: what a press does is `availabilityWeek`'s, the words for a
 * day and a cell are `shared/vocabulary`'s, and the geometry is `AvailabilityGrid`'s. The
 * footnote is the step's slot handed through — the step draws none, and the tab draws the
 * count.
 */

import { AvailabilityGrid } from '@/shared/ui';
import { cellLabel, dayLabel, dayPartHead } from '@/shared/vocabulary/availabilityPresentation';
import { DAY_PARTS, WEEKDAYS } from '@/shared/vocabulary/week';

import type { AvailabilitySlot } from '../domain/ProfileDraft';
import { isTicked } from '../domain/availabilityWeek';

export interface WeekGridProps {
  readonly week: readonly AvailabilitySlot[];
  /** A cell was pressed. The caller decides what that does to the week it holds. */
  readonly onPressCell: (cell: AvailabilitySlot) => void;
  /** 6.8's reserved two lines under the grid, inside the card. */
  readonly footnote?: string;
}

export function WeekGrid({ week, onPressCell, footnote }: WeekGridProps) {
  return (
    <AvailabilityGrid
      columnHeads={DAY_PARTS.map(dayPartHead)}
      rows={WEEKDAYS.map((day) => ({
        key: String(day),
        label: dayLabel(day),
        cells: DAY_PARTS.map((part) => ({
          key: `${day}-${part}`,
          selected: isTicked(week, { day, part }),
          onPress: () => onPressCell({ day, part }),
          accessibilityLabel: cellLabel({ day, part }),
        })),
      }))}
      {...(footnote === undefined ? {} : { footnote })}
    />
  );
}
