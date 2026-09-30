/**
 * The week grid, drawn from a week — **the control, without the onboarding around it.**
 *
 * The availability step and the You tab's *Your week* draw the same grid from the same rule:
 * seven days across, sixteen hours down, Monday first and 07:00 at the top, a cell ticked where
 * the week holds it (6.8, mock 36). What differs between the two is everything *around* the
 * grid — the step's eyebrow with its floor and its *Continue*, the tab's *Save your week* and
 * *Clear all* — so the mapping from a week to the grid's rows is here, once, and each screen
 * composes it under its own chrome
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, first consequence).
 *
 * Nothing here decides anything: what a tap and a drag do are `availabilityWeek`'s, the words
 * for a day, an hour and a cell are `shared/vocabulary`'s, and the geometry and the gesture are
 * `AvailabilityGrid`'s. The grid reports a drag by where its cells are drawn, and
 * `weeklyHourAt` turns those back into the hours they are.
 */

import { AvailabilityGrid } from '@/shared/ui';
import { cellLabel, dayLabel, hourLabel } from '@/shared/vocabulary/availabilityPresentation';
import { HOURS, WEEKDAYS, weeklyHourAt, type WeeklyHour } from '@/shared/vocabulary/week';

import { isTicked } from '../domain/availabilityWeek';

export interface WeekGridProps {
  readonly week: readonly WeeklyHour[];
  /** An hour was tapped. The caller decides what that does to the week it holds. */
  readonly onPressCell: (cell: WeeklyHour) => void;
  /**
   * A drag painted a run: every hour it has crossed so far, whole, and whether it ticks them or
   * clears them. Reported again, one hour longer, as the finger goes.
   */
  readonly onPaintCells: (run: readonly WeeklyHour[], on: boolean) => void;
  /** 6.8's reserved two lines under the grid, inside the card. */
  readonly footnote?: string;
}

export function WeekGrid({ week, onPressCell, onPaintCells, footnote }: WeekGridProps) {
  return (
    <AvailabilityGrid
      columnHeads={WEEKDAYS.map(dayLabel)}
      rows={HOURS.map((hour) => ({
        key: String(hour),
        label: hourLabel(hour),
        cells: WEEKDAYS.map((day) => ({
          key: `${day}-${hour}`,
          selected: isTicked(week, { day, hour }),
          onPress: () => onPressCell({ day, hour }),
          accessibilityLabel: cellLabel({ day, hour }),
        })),
      }))}
      onPaint={(run, on) =>
        onPaintCells(
          run.flatMap(({ row, column }) => weeklyHourAt(row, column) ?? []),
          on,
        )
      }
      {...(footnote === undefined ? {} : { footnote })}
    />
  );
}
