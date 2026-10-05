/**
 * A finger dragged across the week grid, as a test can move it.
 *
 * A **tap** on an hour is `fireEvent.press` on its checkbox, like any other press. A **drag** is
 * `react-native-gesture-handler`'s pan (design-system 6.8), and Jest does no hit testing and
 * lays nothing out — so the paint field is given a size first, through its own `onLayout`, and
 * the pan is fired through the library's `fireGestureHandler` in the order the recogniser calls
 * it: began where the finger lands, active once it has travelled the paint intent, one event at
 * each hour it is then sampled over, ended at the last.
 *
 * **Samples are hours apart on purpose.** A finger is sampled, not traced, and `paint(a, b)`
 * jumps straight from `a` to `b` — so every hour a walk expects between them is one the grid had
 * to find on the line itself, which is what a fast drag on a phone asks of it.
 *
 * The field is laid out at an arbitrary width — the grid divides whatever it is given — and at
 * the theme's own cell height and gap, so the sixteen rows are where the drawing puts them.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { act, fireEvent, screen } from '@testing-library/react-native';
import { State } from 'react-native-gesture-handler';
import type { PanGesture, PanGestureHandlerEventPayload } from 'react-native-gesture-handler';
import { fireGestureHandler, getByGestureTestId } from 'react-native-gesture-handler/jest-utils';

import { AVAILABILITY_PAINT_FIELD, AVAILABILITY_PAINT_GESTURE } from '@/shared/ui/AvailabilityGrid';
import type { FieldPoint } from '@/shared/ui/availabilityGridGeometry';
import { theme } from '@/shared/ui/theme';
import { HOURS, WEEKDAYS, type WeeklyHour } from '@/shared/vocabulary/week';

const { cellHeight, gap, paintIntent } = theme.size.availability;

/** Any width will do; this one keeps every coordinate a whole number. */
const CELL_WIDTH = 30;

const FIELD = {
  x: 0,
  y: 0,
  width: WEEKDAYS.length * CELL_WIDTH + (WEEKDAYS.length - 1) * gap,
  height: HOURS.length * cellHeight + (HOURS.length - 1) * gap,
};

/** The middle of an hour's cell, in the paint field's own coordinates. */
function centreOf(cell: WeeklyHour): FieldPoint {
  return {
    x: WEEKDAYS.indexOf(cell.day) * (CELL_WIDTH + gap) + CELL_WIDTH / 2,
    y: HOURS.indexOf(cell.hour) * (cellHeight + gap) + cellHeight / 2,
  };
}

/**
 * One finger: down on `from`, then sampled over each hour of `through` in turn, and lifted on
 * the last. With no `through` it is a drag that never leaves the hour it began on.
 */
export function paint(from: WeeklyHour, ...through: readonly WeeklyHour[]): void {
  act(() => {
    fireEvent(screen.getByTestId(AVAILABILITY_PAINT_FIELD), 'layout', {
      nativeEvent: { layout: FIELD },
    });
  });

  const start = centreOf(from);
  const at = (point: FieldPoint) => ({
    x: point.x,
    y: point.y,
    absoluteX: point.x,
    absoluteY: point.y,
    translationX: point.x - start.x,
    translationY: point.y - start.y,
    velocityX: 0,
    velocityY: 0,
  });
  // Claimed a paint intent down from where it landed — still inside the first cell, which is
  // half a cell tall above and below its middle.
  const claimed = { x: start.x, y: start.y + paintIntent };
  const samples = through.map(centreOf);
  const lifted = samples.at(-1) ?? claimed;

  act(() => {
    fireGestureHandler<PanGesture>(getByGestureTestId(AVAILABILITY_PAINT_GESTURE), [
      { state: State.BEGAN, ...at(start) },
      { state: State.ACTIVE, ...at(claimed) },
      ...samples.map(at),
      { state: State.END, ...at(lifted) },
    ] satisfies Partial<PanGestureHandlerEventPayload & { state: State }>[]);
  });
}
